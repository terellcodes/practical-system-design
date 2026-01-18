"""
Kafka Consumer for processing upload completion events.

Consumes from 'upload-completed' topic and:
1. Updates message status from PENDING → COMPLETED
2. Fans out message to recipient inboxes
3. Publishes to Redis for WebSocket broadcast
"""

import asyncio
import json
import logging
from datetime import datetime
from typing import Optional

from kafka import KafkaConsumer
from kafka.errors import KafkaError

from src.config import (
    KAFKA_BOOTSTRAP_SERVERS,
    KAFKA_UPLOAD_COMPLETED_TOPIC,
)
from src.repositories.dynamodb import DynamoDBRepository
from src import websocket as ws_module
from common.observability import get_tracer

logger = logging.getLogger(__name__)


class UploadCompletionConsumer:
    """
    Kafka consumer that processes upload completion events.
    
    When a file upload completes:
    1. Update message status in DynamoDB (PENDING → COMPLETED)
    2. Fanout to recipient inboxes
    3. Publish to Redis so WebSocket clients receive the message
    """
    
    def __init__(self, repository: Optional[DynamoDBRepository] = None):
        self.repository = repository or DynamoDBRepository()
        self.consumer: Optional[KafkaConsumer] = None
        self._running = False
        self._task: Optional[asyncio.Task] = None
    
    def _create_consumer(self) -> KafkaConsumer:
        """Create and configure Kafka consumer."""
        return KafkaConsumer(
            KAFKA_UPLOAD_COMPLETED_TOPIC,
            bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS.split(','),
            group_id='chat-service-upload-processor',
            auto_offset_reset='earliest',
            enable_auto_commit=True,
            value_deserializer=lambda m: json.loads(m.decode('utf-8')),
            # Shorter timeouts for faster startup
            session_timeout_ms=10000,
            heartbeat_interval_ms=3000,
        )
    
    async def start(self):
        """Start the consumer in a background task."""
        self._running = True
        self._task = asyncio.create_task(self._consume_loop())
        logger.info(f"Kafka consumer started for topic: {KAFKA_UPLOAD_COMPLETED_TOPIC}")
    
    async def stop(self):
        """Stop the consumer gracefully."""
        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        if self.consumer:
            self.consumer.close()
        logger.info("Kafka consumer stopped")
    
    async def _consume_loop(self):
        """Main consumption loop - runs in background."""
        # Run Kafka polling in a thread pool since kafka-python is synchronous
        loop = asyncio.get_event_loop()
        
        try:
            # Create consumer (blocking call, so run in executor)
            self.consumer = await loop.run_in_executor(
                None, self._create_consumer
            )
            logger.info("Kafka consumer connected")
            
            while self._running:
                # Poll for messages (run in executor since it's blocking)
                messages = await loop.run_in_executor(
                    None, lambda: self.consumer.poll(timeout_ms=1000)
                )
                
                for topic_partition, records in messages.items():
                    for record in records:
                        try:
                            await self._process_message(record.value)
                        except Exception as e:
                            logger.error(f"Error processing message: {e}")
                
                # Small delay to prevent tight loop
                await asyncio.sleep(0.1)
                
        except asyncio.CancelledError:
            logger.info("Consumer loop cancelled")
        except Exception as e:
            logger.error(f"Consumer loop error: {e}")
        finally:
            if self.consumer:
                self.consumer.close()
    
    async def _process_message(self, message: dict):
        """
        Process a single upload completion message.

        Expected message format:
        {
            "message_id": "msg-xxx",
            "chat_id": "chat-xxx",
            "s3_bucket": "chat-media",
            "s3_key": "chats/.../file.jpg",
            "filename": "file.jpg",
            "size": 12345,
            "event_type": "upload_completed",
            "correlation_id": "xxx-xxx-xxx"
        }
        """
        logger.info(f"Processing upload completion: {message}")

        message_id = message.get('message_id')
        chat_id = message.get('chat_id')
        s3_bucket = message.get('s3_bucket')
        s3_key = message.get('s3_key')
        correlation_id = message.get('correlation_id', 'unknown')

        if not message_id or not chat_id:
            logger.warning(f"Invalid message, missing message_id or chat_id: {message}")
            return

        # Create a span for processing this Kafka message
        tracer = get_tracer()
        with tracer.start_as_current_span(
            "kafka.process_upload_completion",
            attributes={
                "messaging.system": "kafka",
                "messaging.destination": KAFKA_UPLOAD_COMPLETED_TOPIC,
                "correlation.id": correlation_id,
                "message.id": message_id,
                "chat.id": chat_id,
            }
        ):
            await self._do_process_message(
                message_id, chat_id, s3_bucket, s3_key, correlation_id, message
            )

    async def _do_process_message(
        self,
        message_id: str,
        chat_id: str,
        s3_bucket: str,
        s3_key: str,
        correlation_id: str,
        message: dict
    ):
        """Internal message processing with tracing context."""
        try:
            # 1. Get message details from DynamoDB to get created_at timestamp
            # We need to query by message_id to get the full record
            messages_table = self.repository.messages_table
            response = messages_table.query(
                KeyConditionExpression='messageId = :mid',
                ExpressionAttributeValues={':mid': message_id},
                Limit=1
            )
            
            items = response.get('Items', [])
            if not items:
                logger.warning(f"Message {message_id} not found in DynamoDB")
                return
            
            msg_record = items[0]
            created_at_raw = msg_record.get('createdAt', 0)
            created_at = int(float(created_at_raw))
            sender_id = int(msg_record.get('senderId', '0'))  # Convert string to int for frontend compatibility
            content = msg_record.get('content', '')
            sender_username = msg_record.get('senderUsername')
            sender_name = msg_record.get('senderName')
            
            # 2. Update message status to COMPLETED
            success = self.repository.update_message_upload_status(
                message_id=message_id,
                created_at=created_at,
                upload_status='COMPLETED'
            )
            
            if not success:
                logger.error(f"Failed to update message {message_id} status")
                return
            
            logger.info(f"Updated message {message_id} status to COMPLETED")
            
            # 3. Get chat participants for inbox fanout
            participants = self.repository.get_participants_for_chat(chat_id)
            recipient_ids = [p.participant_id for p in participants if p.participant_id != sender_id]
            
            # 4. Fanout to inboxes
            if recipient_ids:
                self.repository.fanout_message_to_inbox(
                    message_id=message_id,
                    chat_id=chat_id,
                    created_at=created_at,
                    recipient_ids=recipient_ids
                )
                logger.info(f"Fanned out message {message_id} to {len(recipient_ids)} inboxes")
            
            # 5. Publish to Redis for WebSocket broadcast
            if ws_module.manager:
                created_at_iso = datetime.utcfromtimestamp(created_at / 1000).isoformat()

                # Build the WebSocket message
                ws_payload = {
                    "type": "message",
                    "message_id": message_id,
                    "chat_id": chat_id,
                    "sender_id": sender_id,
                    "content": content,
                    "created_at": created_at_iso,
                    "upload_status": "COMPLETED",
                    "s3_bucket": s3_bucket,
                    "s3_key": s3_key,
                }
                # Include sender display info if available
                if sender_username:
                    ws_payload["sender_username"] = sender_username
                if sender_name:
                    ws_payload["sender_name"] = sender_name
                ws_message = json.dumps(ws_payload)
                
                await ws_module.manager.publish_message(chat_id, ws_message)
                logger.info(f"Published message {message_id} to Redis for WebSocket broadcast")
            
            logger.info(f"Successfully processed upload completion for message {message_id}")
            
        except Exception as e:
            logger.error(f"Error processing upload completion for {message_id}: {e}")
            raise


# Global consumer instance
upload_consumer: Optional[UploadCompletionConsumer] = None


def create_upload_consumer(repository: Optional[DynamoDBRepository] = None) -> UploadCompletionConsumer:
    """Factory function to create the upload consumer."""
    return UploadCompletionConsumer(repository)