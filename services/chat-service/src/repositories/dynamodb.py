"""
DynamoDB repository using boto3

Key Concepts for System Design Interviews:
- Partition Key (PK): Determines data distribution
- Sort Key (SK): Enables range queries within partition
- GSI: Allows querying by different attributes
"""

import logging
from datetime import datetime
from typing import Optional, List

from boto3.dynamodb.conditions import Key
from botocore.exceptions import ClientError
from fastapi import HTTPException, status

from common.database import create_dynamodb_resource
from common.models import Chat, ChatParticipant
from src.config import (
    DYNAMODB_CONFIG,
    CHATS_TABLE,
    CHAT_PARTICIPANTS_TABLE,
    MESSAGES_TABLE,
    INBOX_TABLE,
    PARTICIPANT_INDEX,
)

logger = logging.getLogger(__name__)


class DynamoDBRepository:
    """Repository for DynamoDB operations"""

    # Shared DynamoDB resource (initialized once in main.py)
    _dynamodb_resource = None

    def __init__(self, dynamodb_resource=None):
        # Use provided resource or fall back to creating one (for backwards compatibility)
        if dynamodb_resource is not None:
            self.dynamodb = dynamodb_resource
        elif self._dynamodb_resource is not None:
            self.dynamodb = self._dynamodb_resource
        else:
            # Fallback: create new connection (logs warning)
            logger.warning("Creating new DynamoDB connection. Consider using shared resource.")
            self.dynamodb = create_dynamodb_resource(DYNAMODB_CONFIG)
        
        self.chats_table = self.dynamodb.Table(CHATS_TABLE)
        self.participants_table = self.dynamodb.Table(CHAT_PARTICIPANTS_TABLE)
        self.messages_table = self.dynamodb.Table(MESSAGES_TABLE)
        self.inbox_table = self.dynamodb.Table(INBOX_TABLE)
    
    @classmethod
    def set_shared_resource(cls, dynamodb_resource):
        """Set the shared DynamoDB resource (call once on startup)"""
        cls._dynamodb_resource = dynamodb_resource
        logger.info("Shared DynamoDB resource configured")

    # =========================================================================
    # Chat Operations
    # =========================================================================

    def create_chat(self, chat_id: str, name: str, metadata: dict) -> Chat:
        """Create a new chat in DynamoDB."""
        try:
            now = datetime.utcnow()
            item = {
                'id': chat_id,
                'name': name,
                'metadata': metadata or {},
                'createdAt': now.isoformat(),
            }

            self.chats_table.put_item(Item=item)
            logger.info(f"Chat {chat_id} created")

            return Chat(
                id=chat_id,
                name=name,
                metadata=metadata or {},
                created_at=now,
            )
        except ClientError as e:
            logger.error(f"Failed to create chat {chat_id}: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to create chat: {str(e)}"
            )

    def get_chat(self, chat_id: str) -> Optional[Chat]:
        """Get a chat by ID."""
        try:
            response = self.chats_table.get_item(Key={'id': chat_id})

            if 'Item' not in response:
                return None

            item = response['Item']
            return Chat(
                id=item['id'],
                name=item['name'],
                metadata=item.get('metadata', {}),
                created_at=datetime.fromisoformat(item['createdAt']),
            )
        except ClientError as e:
            logger.error(f"Failed to get chat {chat_id}: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to get chat: {str(e)}"
            )

    def delete_chat(self, chat_id: str) -> bool:
        """Delete a chat by ID."""
        try:
            self.chats_table.delete_item(Key={'id': chat_id})
            logger.info(f"Chat {chat_id} deleted")
            return True
        except ClientError as e:
            logger.error(f"Failed to delete chat {chat_id}: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to delete chat: {str(e)}"
            )

    # =========================================================================
    # ChatParticipant Operations
    # =========================================================================

    def add_participant(self, chat_id: str, participant_id: str) -> ChatParticipant:
        """Add a participant to a chat."""
        try:
            now = datetime.utcnow()
            item = {
                'chatId': chat_id,
                'participantId': participant_id,
                'joinedAt': now.isoformat(),
            }

            self.participants_table.put_item(Item=item)
            logger.info(f"Participant {participant_id} added to chat {chat_id}")

            return ChatParticipant(
                chat_id=chat_id,
                participant_id=participant_id,
                joined_at=now,
            )
        except ClientError as e:
            logger.error(f"Failed to add participant: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to add participant: {str(e)}"
            )

    def remove_participant(self, chat_id: str, participant_id: str) -> bool:
        """Remove a participant from a chat."""
        try:
            self.participants_table.delete_item(
                Key={'chatId': chat_id, 'participantId': participant_id}
            )
            logger.info(f"Participant {participant_id} removed from chat {chat_id}")
            return True
        except ClientError as e:
            logger.error(f"Failed to remove participant: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to remove participant: {str(e)}"
            )

    def get_participants_for_chat(self, chat_id: str) -> List[ChatParticipant]:
        """Get all participants in a chat (Query on PK)."""
        try:
            response = self.participants_table.query(
                KeyConditionExpression=Key('chatId').eq(chat_id)
            )

            return [
                ChatParticipant(
                    chat_id=item['chatId'],
                    participant_id=item['participantId'],
                    joined_at=datetime.fromisoformat(item['joinedAt']),
                )
                for item in response.get('Items', [])
            ]
        except ClientError as e:
            logger.error(f"Failed to get participants: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to get participants: {str(e)}"
            )

    def get_chats_for_participant(self, participant_id: str) -> List[str]:
        """Get all chat IDs for a participant (Query on GSI)."""
        try:
            response = self.participants_table.query(
                IndexName=PARTICIPANT_INDEX,
                KeyConditionExpression=Key('participantId').eq(participant_id)
            )

            return [item['chatId'] for item in response.get('Items', [])]
        except ClientError as e:
            logger.error(f"Failed to get chats for participant: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to get chats: {str(e)}"
            )

    def is_participant(self, chat_id: str, participant_id: str) -> bool:
        """Check if user is a participant in chat."""
        try:
            response = self.participants_table.get_item(
                Key={'chatId': chat_id, 'participantId': participant_id}
            )
            return 'Item' in response
        except ClientError:
            return False
        
    # =========================================================================
    # Messages Operations
    # =========================================================================
    def save_message(self, chat_id: str, sender_id: str, content: str, recipient_ids: List[str] = None) -> dict:
        """
        Save a message to DynamoDB and populate inbox for all recipients.
        
        Args:
            chat_id: The chat ID
            sender_id: The sender's user ID
            content: Message content
            recipient_ids: List of recipient user IDs (for inbox fanout)
        
        Returns:
            dict: Message data including message_id and timestamps
        """
        try:
            import uuid
            
            now = datetime.utcnow()
            message_id = f"msg-{uuid.uuid4().hex[:12]}"
            timestamp_ms = int(now.timestamp() * 1000)
            
            # Save to Messages table
            message_item = {
                'chatId': chat_id,
                'createdAt': timestamp_ms,
                'messageId': message_id,
                'senderId': sender_id,
                'content': content,
            }
            self.messages_table.put_item(Item=message_item)
            
            # Fanout to Inbox table for each recipient
            if recipient_ids:
                with self.inbox_table.batch_writer() as batch:
                    for recipient_id in recipient_ids:
                        inbox_item = {
                            'recipientId': recipient_id,
                            'createdAt': timestamp_ms,
                            'chatId': chat_id,
                            'messageId': message_id,
                        }
                        batch.put_item(Item=inbox_item)
                
                logger.info(f"Message {message_id} saved to chat {chat_id} and fanned out to {len(recipient_ids)} inboxes")
            else:
                logger.info(f"Message {message_id} saved to chat {chat_id} (no inbox fanout)")

            return {
                'message_id': message_id,
                'chat_id': chat_id,
                'sender_id': sender_id,
                'content': content,
                'created_at': now.isoformat(),
                'timestamp': timestamp_ms
            }
        except ClientError as e:
            logger.error(f"Failed to create message in {chat_id}: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to create message: {str(e)}"
            )
        
    # =========================================================================
    # Inbox Operations
    # =========================================================================

    def delete_inbox_message(self, recipient_id: str, message_id: str) -> bool:
        logger.info(f'Attempting to delete inbox message for recipient: {recipient_id} for message_id {message_id}')
        response = self.inbox_table.get_item(Key={
            'recipientId': recipient_id,
            'messageId': message_id
        })

        if not response.get('Item'):
            logger.info(f'Failed to delete message. Message does not exist in inbox for {recipient_id}')
            return False

        self.inbox_table.delete_item(Key={
            'recipientId': recipient_id,
            'messageId': message_id
        })
        logger.info('Succesfully deleted message from inbox')
        return True
    
    def get_inbox_messages(
        self, 
        recipient_id: str, 
        limit: int = 50, 
        last_evaluated_key: dict = None
    ) -> dict:
        """
        Get messages from a user's inbox (across all chats), sorted by time.
        
        Args:
            recipient_id: The user's ID
            limit: Maximum number of messages to return
            last_evaluated_key: For pagination
        
        Returns:
            dict with 'items' and 'last_evaluated_key'
        """
        try:
            query_params = {
                'KeyConditionExpression': Key('recipientId').eq(recipient_id),
                'ScanIndexForward': False,  # Newest first
                'Limit': limit
            }
            
            if last_evaluated_key:
                query_params['ExclusiveStartKey'] = last_evaluated_key
            
            response = self.inbox_table.query(**query_params)
            
            return {
                'items': response.get('Items', []),
                'last_evaluated_key': response.get('LastEvaluatedKey'),
                'count': len(response.get('Items', []))
            }
        except ClientError as e:
            logger.error(f"Failed to get inbox for {recipient_id}: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to get inbox: {str(e)}"
            )

    # =========================================================================
    # Health Check Operations
    # =========================================================================

    async def health_check(self) -> bool:
        """Check DynamoDB connectivity."""
        try:
            self.chats_table.table_status
            return True
        except Exception:
            return False