"""
DynamoDB repository using boto3 for Chat domain
"""

import logging
from datetime import datetime
from typing import Optional, List
from decimal import Decimal

import boto3
from boto3.dynamodb.conditions import Key
from botocore.exceptions import ClientError
from fastapi import HTTPException, status

from src.config import (
    DYNAMODB_ENDPOINT,
    AWS_REGION,
    AWS_ACCESS_KEY_ID,
    AWS_SECRET_ACCESS_KEY,
    CHATS_TABLE,
    CHAT_PARTICIPANTS_TABLE,
    PARTICIPANT_INDEX,
    IS_LOCAL,
)
from src.models.chat import Chat, ChatParticipant

logger = logging.getLogger(__name__)


def get_dynamodb_resource():
    """Get boto3 DynamoDB resource configured for local or AWS"""
    if IS_LOCAL:
        return boto3.resource(
            'dynamodb',
            endpoint_url=DYNAMODB_ENDPOINT,
            region_name=AWS_REGION,
            aws_access_key_id=AWS_ACCESS_KEY_ID,
            aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
        )
    else:
        # Production: uses IAM role/credentials automatically
        return boto3.resource('dynamodb', region_name=AWS_REGION)


class DynamoDBRepository:
    """Repository for DynamoDB operations (Chat domain)"""
    
    def __init__(self):
        self.dynamodb = get_dynamodb_resource()
        self.chats_table = self.dynamodb.Table(CHATS_TABLE)
        self.participants_table = self.dynamodb.Table(CHAT_PARTICIPANTS_TABLE)
    
    # =========================================================================
    # Chat Operations
    # =========================================================================
    
    def create_chat(self, chat_id: str, name: str, metadata: dict) -> Chat:
        """Create a new chat in DynamoDB"""
        try:
            now = datetime.utcnow()
            item = {
                'id': chat_id,
                'name': name,
                'metadata': metadata or {},
                'createdAt': now.isoformat(),
            }
            
            self.chats_table.put_item(Item=item)
            logger.info(f"Chat {chat_id} created in DynamoDB")
            
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
        """Get a chat by ID"""
        try:
            response = self.chats_table.get_item(Key={'id': chat_id})
            
            if 'Item' not in response:
                logger.info(f"Chat {chat_id} not found")
                return None
            
            item = response['Item']
            logger.info(f"Chat {chat_id} found in DynamoDB")
            
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
        """Delete a chat by ID"""
        try:
            self.chats_table.delete_item(Key={'id': chat_id})
            logger.info(f"Chat {chat_id} deleted from DynamoDB")
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
        """Add a participant to a chat"""
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
            logger.error(f"Failed to add participant {participant_id} to chat {chat_id}: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to add participant: {str(e)}"
            )
    
    def remove_participant(self, chat_id: str, participant_id: str) -> bool:
        """Remove a participant from a chat"""
        try:
            self.participants_table.delete_item(
                Key={
                    'chatId': chat_id,
                    'participantId': participant_id,
                }
            )
            logger.info(f"Participant {participant_id} removed from chat {chat_id}")
            return True
        except ClientError as e:
            logger.error(f"Failed to remove participant {participant_id} from chat {chat_id}: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to remove participant: {str(e)}"
            )
    
    def get_participants_for_chat(self, chat_id: str) -> List[ChatParticipant]:
        """Get all participants in a chat (uses main table query)"""
        try:
            response = self.participants_table.query(
                KeyConditionExpression=Key('chatId').eq(chat_id)
            )
            
            participants = []
            for item in response.get('Items', []):
                participants.append(ChatParticipant(
                    chat_id=item['chatId'],
                    participant_id=item['participantId'],
                    joined_at=datetime.fromisoformat(item['joinedAt']),
                ))
            
            logger.info(f"Found {len(participants)} participants for chat {chat_id}")
            return participants
        except ClientError as e:
            logger.error(f"Failed to get participants for chat {chat_id}: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to get participants: {str(e)}"
            )
    
    def get_chats_for_participant(self, participant_id: str) -> List[str]:
        """
        Get all chat IDs for a participant (uses GSI).
        Returns list of chat IDs.
        """
        try:
            response = self.participants_table.query(
                IndexName=PARTICIPANT_INDEX,
                KeyConditionExpression=Key('participantId').eq(participant_id)
            )
            
            chat_ids = [item['chatId'] for item in response.get('Items', [])]
            logger.info(f"Found {len(chat_ids)} chats for participant {participant_id}")
            return chat_ids
        except ClientError as e:
            logger.error(f"Failed to get chats for participant {participant_id}: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to get chats for participant: {str(e)}"
            )
    
    def is_participant(self, chat_id: str, participant_id: str) -> bool:
        """Check if a user is a participant in a chat"""
        try:
            response = self.participants_table.get_item(
                Key={
                    'chatId': chat_id,
                    'participantId': participant_id,
                }
            )
            return 'Item' in response
        except ClientError as e:
            logger.error(f"Failed to check participant status: {e}")
            return False

