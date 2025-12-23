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
    PARTICIPANT_INDEX,
)

logger = logging.getLogger(__name__)


class DynamoDBRepository:
    """Repository for DynamoDB operations"""

    def __init__(self):
        self.dynamodb = create_dynamodb_resource(DYNAMODB_CONFIG)
        self.chats_table = self.dynamodb.Table(CHATS_TABLE)
        self.participants_table = self.dynamodb.Table(CHAT_PARTICIPANTS_TABLE)

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

    async def health_check(self) -> bool:
        """Check DynamoDB connectivity."""
        try:
            self.chats_table.table_status
            return True
        except Exception:
            return False
