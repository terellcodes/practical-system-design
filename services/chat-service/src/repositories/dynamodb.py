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
from common.models import Chat, ChatParticipant, InboxList, Message
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

    def add_participant(self, chat_id: str, participant_id: int) -> ChatParticipant:
        """Add a participant to a chat."""
        try:
            now = datetime.utcnow()
            item = {
                'chatId': chat_id,
                'participantId': str(participant_id),  # Convert int to str for DynamoDB
                'joinedAt': now.isoformat(),
            }

            self.participants_table.put_item(Item=item)
            logger.info(f"Participant {participant_id} added to chat {chat_id}")

            return ChatParticipant(
                chat_id=chat_id,
                participant_id=participant_id,  # Return as int
                joined_at=now,
            )
        except ClientError as e:
            logger.error(f"Failed to add participant: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to add participant: {str(e)}"
            )

    def remove_participant(self, chat_id: str, participant_id: int) -> bool:
        """Remove a participant from a chat."""
        try:
            self.participants_table.delete_item(
                Key={'chatId': chat_id, 'participantId': str(participant_id)}  # Convert int to str for DynamoDB key
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
                    participant_id=int(item['participantId']),  # Convert str to int from DynamoDB
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

    def get_chats_for_participant(self, participant_id: int) -> List[str]:
        """Get all chat IDs for a participant (Query on GSI)."""
        try:
            response = self.participants_table.query(
                IndexName=PARTICIPANT_INDEX,
                KeyConditionExpression=Key('participantId').eq(str(participant_id))  # Convert int to str for DynamoDB query
            )

            return [item['chatId'] for item in response.get('Items', [])]
        except ClientError as e:
            logger.error(f"Failed to get chats for participant: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to get chats: {str(e)}"
            )

    def is_participant(self, chat_id: str, participant_id: int) -> bool:
        """Check if user is a participant in chat."""
        try:
            response = self.participants_table.get_item(
                Key={'chatId': chat_id, 'participantId': str(participant_id)}  # Convert int to str for DynamoDB key
            )
            return 'Item' in response
        except ClientError:
            return False
        
    # =========================================================================
    # Messages Operations
    # =========================================================================
    def save_message(
        self,
        chat_id: str,
        sender_id: int,
        content: str,
        recipient_ids: Optional[List[int]] = None,
        # Sender display info (optional)
        sender_username: Optional[str] = None,
        sender_name: Optional[str] = None,
        # Attachment fields (optional)
        upload_status: Optional[str] = None,
        s3_bucket: Optional[str] = None,
        s3_object_key: Optional[str] = None,
        message_id: Optional[str] = None,
    ) -> dict:
        """
        Save a message to DynamoDB and populate inbox for all recipients.
        
        For messages with attachments (upload_status=PENDING), inbox fanout is skipped.
        The fanout happens later when upload completes via Kafka consumer.
        
        Args:
            chat_id: The chat ID
            sender_id: The sender's user ID
            content: Message content
            recipient_ids: List of recipient user IDs (for inbox fanout)
            sender_username: Optional sender's username (for display)
            sender_name: Optional sender's display name
            upload_status: Optional upload status (PENDING, COMPLETED, FAILED)
            s3_bucket: Optional S3 bucket name for attachment
            s3_object_key: Optional S3 object key for attachment
        
        Returns:
            dict: Message data including message_id and timestamps
        """
        try:
            import uuid
            
            now = datetime.utcnow()
            message_id = message_id or f"msg-{uuid.uuid4().hex[:12]}"
            timestamp_ms = int(now.timestamp() * 1000)
            
            # Save to Messages table
            message_item = {
                'chatId': chat_id,
                'createdAt': timestamp_ms,
                'messageId': message_id,
                'senderId': str(sender_id),  # Convert int to str for DynamoDB
                'content': content,
            }
            
            # Add sender display info if present
            if sender_username:
                message_item['senderUsername'] = sender_username
            if sender_name:
                message_item['senderName'] = sender_name
            
            # Add attachment fields if present
            if upload_status:
                message_item['uploadStatus'] = upload_status
            if s3_bucket:
                message_item['s3Bucket'] = s3_bucket
            if s3_object_key:
                message_item['s3ObjectKey'] = s3_object_key
            
            self.messages_table.put_item(Item=message_item)
            
            # Fanout to Inbox table for each recipient
            # Skip fanout for PENDING messages - they'll be fanned out when upload completes
            is_pending_upload = upload_status == "PENDING"
            
            if recipient_ids and not is_pending_upload:
                with self.inbox_table.batch_writer() as batch:
                    for recipient_id in recipient_ids:
                        inbox_item = {
                            'recipientId': str(recipient_id),  # Convert int to str for DynamoDB
                            'createdAt': timestamp_ms,
                            'chatId': chat_id,
                            'messageId': message_id,
                        }
                        batch.put_item(Item=inbox_item)
                
                logger.info(f"Message {message_id} saved to chat {chat_id} and fanned out to {len(recipient_ids)} inboxes")
            elif is_pending_upload:
                logger.info(f"Message {message_id} saved to chat {chat_id} with PENDING upload (inbox fanout deferred)")
            else:
                logger.info(f"Message {message_id} saved to chat {chat_id} (no inbox fanout)")

            # Build response
            response = {
                'message_id': message_id,
                'chat_id': chat_id,
                'sender_id': sender_id,
                'content': content,
                'created_at': now.isoformat(),
                'timestamp': timestamp_ms
            }
            
            # Include attachment fields in response if present
            if upload_status:
                response['upload_status'] = upload_status
            if s3_bucket:
                response['s3_bucket'] = s3_bucket
            if s3_object_key:
                response['s3_object_key'] = s3_object_key
            
            return response
        except ClientError as e:
            logger.error(f"Failed to create message in {chat_id}: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to create message: {str(e)}"
            )
    
    def update_message_upload_status(self, message_id: str, created_at: int, upload_status: str) -> bool:
        """
        Update the upload status of a message (used by Kafka consumer after upload completes).
        
        Args:
            message_id: The message ID
            created_at: The message creation timestamp (part of sort key)
            upload_status: New status (COMPLETED or FAILED)
        
        Returns:
            bool: True if update succeeded
        """
        try:
            self.messages_table.update_item(
                Key={
                    'messageId': message_id,
                    'createdAt': created_at
                },
                UpdateExpression='SET uploadStatus = :status',
                ExpressionAttributeValues={
                    ':status': upload_status
                }
            )
            logger.info(f"Updated message {message_id} upload status to {upload_status}")
            return True
        except ClientError as e:
            logger.error(f"Failed to update message {message_id} upload status: {e}")
            return False
    
    def fanout_message_to_inbox(self, message_id: str, chat_id: str, created_at: int, recipient_ids: List[int]) -> bool:
        """
        Fanout a message to recipients' inboxes (used after upload completes).

        Args:
            message_id: The message ID
            chat_id: The chat ID
            created_at: The message creation timestamp
            recipient_ids: List of recipient user IDs

        Returns:
            bool: True if fanout succeeded
        """
        try:
            with self.inbox_table.batch_writer() as batch:
                for recipient_id in recipient_ids:
                    inbox_item = {
                        'recipientId': str(recipient_id),  # Convert int to str for DynamoDB
                        'createdAt': created_at,
                        'chatId': chat_id,
                        'messageId': message_id,
                    }
                    batch.put_item(Item=inbox_item)

            logger.info(f"Message {message_id} fanned out to {len(recipient_ids)} inboxes")
            return True
        except ClientError as e:
            logger.error(f"Failed to fanout message {message_id}: {e}")
            return False
        
    # =========================================================================
    # Inbox Operations
    # =========================================================================

    def delete_inbox_message(self, recipient_id: int, message_id: str) -> bool:
        logger.info(f'Attempting to delete inbox message for recipient: {recipient_id} for message_id {message_id}')
        response = self.inbox_table.get_item(Key={
            'recipientId': str(recipient_id),  # Convert int to str for DynamoDB key
            'messageId': message_id
        })

        if not response.get('Item'):
            logger.info(f'Failed to delete message. Message does not exist in inbox for {recipient_id}')
            return False

        self.inbox_table.delete_item(Key={
            'recipientId': str(recipient_id),  # Convert int to str for DynamoDB key
            'messageId': message_id
        })
        logger.info('Succesfully deleted message from inbox')
        return True
    
    def get_inbox_messages(
        self,
        recipient_id: int,
        limit: int = 50,
        last_evaluated_key: Optional[dict] = None
    ) -> InboxList:
        """
        Get messages from a user's inbox (across all chats), sorted by time.

        Args:
            recipient_id: The user's ID
            limit: Maximum number of messages to return
            last_evaluated_key: For pagination

        Returns:
            InboxList with converted InboxItem models
        """
        try:
            query_params = {
                'KeyConditionExpression': Key('recipientId').eq(str(recipient_id)),  # Convert int to str for DynamoDB query
                'ScanIndexForward': False,  # Newest first
                'Limit': limit
            }
            
            if last_evaluated_key:
                query_params['ExclusiveStartKey'] = last_evaluated_key
            
            response = self.inbox_table.query(**query_params)
            items = response.get('Items', [])
            
            # Sort by createdAt timestamp (newest first)
            # createdAt is stored as milliseconds (number), so sort numerically
            items.sort(key=lambda item: float(item.get('createdAt', 0)))
            
            message_ids = list(map(lambda item: item.get('messageId'), items))
            logger.info(f"Inbox messages fetched: {message_ids}")


            inbox_messages = self.hydrate_inbox_messages(message_ids)

            items = zip(items, inbox_messages)
            
            # Convert DynamoDB items to Message models
            inbox_message_list = []
            for msg_item in inbox_messages:
                
                # Convert createdAt from Decimal to float before division
                message_created_at_ms = float(msg_item.get('createdAt', 0))
                message_created_at_dt = datetime.fromtimestamp(message_created_at_ms / 1000.0)
                
                # Build message with optional attachment fields
                message_data = {
                    'message_id': msg_item.get('messageId', ''),
                    'chat_id': msg_item.get('chatId', ''),
                    'sender_id': int(msg_item.get('senderId', '0')),  # Convert str to int from DynamoDB
                    'content': msg_item.get('content', ''),
                    'created_at': message_created_at_dt
                }
                
                # Include attachment fields if present
                if msg_item.get('uploadStatus'):
                    message_data['upload_status'] = msg_item.get('uploadStatus')
                if msg_item.get('s3Bucket'):
                    message_data['s3_bucket'] = msg_item.get('s3Bucket')
                if msg_item.get('s3ObjectKey'):
                    message_data['s3_object_key'] = msg_item.get('s3ObjectKey')
                
                message = Message(**message_data)
                inbox_message_list.append(message)
            
            
            return InboxList(
                items=inbox_message_list,
                count=len(inbox_message_list),
                recipient_id=recipient_id,
                last_evaluated_key=response.get('LastEvaluatedKey')
            )
        except ClientError as e:
            logger.error(f"Failed to get inbox for {recipient_id}: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to get inbox: {str(e)}"
            )
        
    def hydrate_inbox_messages(
            self,
            message_ids: List[str]
    ) -> List[dict]:
        """
        Batch fetch full message content for a list of message IDs.
        
        Args:
            message_ids: List of message IDs to fetch
        
        Returns:
            List of full message items (dicts) from Messages table
        
        Note: Uses query() with just messageId (partition key) since we don't have createdAt.
        This is less efficient than batch_get_item but works with just messageId.
        Each messageId should only have one message, so we take the first result.
        """
        
        if not message_ids:
            return []
        
        logger.info(f"Attempting to hydate inbox messages")
        all_messages = []
        
        # Query each messageId individually (can't batch query by different partition keys)
        for message_id in message_ids:
            try:
                # Query by messageId (partition key) only
                # This returns all items with that messageId (should be just one)
                response = self.messages_table.query(
                    KeyConditionExpression=Key('messageId').eq(message_id),
                    Limit=1  # We only expect one message per messageId
                )
                
                items = response.get('Items', [])
                if items:
                    all_messages.append(items[0])  # Take the first (and should be only) result
                    
            except ClientError as e:
                logger.error(f"Failed to query message {message_id}: {e}")
                # Continue with other messages instead of failing completely
                continue
        logger.info(f"Successfully hydrated inbox messages")
        return all_messages

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