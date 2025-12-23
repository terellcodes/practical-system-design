"""
Chat business logic service

Handles chat operations using DynamoDB with GSI for efficient queries.
"""

import logging
import uuid
from typing import List, Optional

from fastapi import HTTPException, status

from src.models.chat import (
    Chat,
    ChatCreate,
    ChatParticipant,
    ChatWithParticipants,
)
from src.repositories.dynamodb import DynamoDBRepository

logger = logging.getLogger(__name__)


class ChatService:
    """Service layer for chat operations"""
    
    def __init__(self, repository: Optional[DynamoDBRepository] = None):
        self.repository = repository or DynamoDBRepository()
    
    def create_chat(self, chat_data: ChatCreate) -> Chat:
        """
        Create a new chat.
        
        Generates a unique ID and stores in DynamoDB.
        """
        logger.info(f"Creating new chat: {chat_data.name}")
        
        # Generate unique chat ID
        chat_id = f"chat-{uuid.uuid4().hex[:12]}"
        
        # Create chat in DynamoDB
        chat = self.repository.create_chat(
            chat_id=chat_id,
            name=chat_data.name,
            metadata=chat_data.metadata or {},
        )
        
        logger.info(f"Chat {chat_id} created successfully")
        return chat
    
    def get_chat(self, chat_id: str) -> Chat:
        """
        Get a chat by ID.
        
        Raises 404 if chat not found.
        """
        logger.info(f"Fetching chat {chat_id}")
        
        chat = self.repository.get_chat(chat_id)
        
        if not chat:
            logger.warning(f"Chat {chat_id} not found")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Chat with ID {chat_id} not found"
            )
        
        return chat
    
    def get_chat_with_participants(self, chat_id: str) -> ChatWithParticipants:
        """
        Get a chat with all its participants.
        """
        logger.info(f"Fetching chat {chat_id} with participants")
        
        chat = self.get_chat(chat_id)
        participants = self.repository.get_participants_for_chat(chat_id)
        
        return ChatWithParticipants(
            chat=chat,
            participants=participants,
        )
    
    def delete_chat(self, chat_id: str) -> bool:
        """
        Delete a chat and all its participants.
        """
        logger.info(f"Deleting chat {chat_id}")
        
        # Verify chat exists
        self.get_chat(chat_id)
        
        # Remove all participants first
        participants = self.repository.get_participants_for_chat(chat_id)
        for participant in participants:
            self.repository.remove_participant(chat_id, participant.participant_id)
        
        # Delete the chat
        self.repository.delete_chat(chat_id)
        
        logger.info(f"Chat {chat_id} deleted successfully")
        return True
    
    def add_participants(self, chat_id: str, participant_ids: List[str]) -> List[ChatParticipant]:
        """
        Add participants to a chat.
        
        Skips participants who are already in the chat.
        """
        logger.info(f"Adding {len(participant_ids)} participants to chat {chat_id}")
        
        # Verify chat exists
        self.get_chat(chat_id)
        
        added_participants = []
        for participant_id in participant_ids:
            # Check if already a participant
            if self.repository.is_participant(chat_id, participant_id):
                logger.info(f"Participant {participant_id} already in chat {chat_id}, skipping")
                continue
            
            # Add participant
            participant = self.repository.add_participant(chat_id, participant_id)
            added_participants.append(participant)
        
        logger.info(f"Added {len(added_participants)} new participants to chat {chat_id}")
        return added_participants
    
    def remove_participant(self, chat_id: str, participant_id: str) -> bool:
        """
        Remove a participant from a chat.
        
        Raises 404 if participant not in chat.
        """
        logger.info(f"Removing participant {participant_id} from chat {chat_id}")
        
        # Verify chat exists
        self.get_chat(chat_id)
        
        # Verify participant is in the chat
        if not self.repository.is_participant(chat_id, participant_id):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Participant {participant_id} not found in chat {chat_id}"
            )
        
        self.repository.remove_participant(chat_id, participant_id)
        
        logger.info(f"Participant {participant_id} removed from chat {chat_id}")
        return True
    
    def get_chats_for_participant(self, participant_id: str) -> List[Chat]:
        """
        Get all chats for a participant.
        
        Uses GSI for efficient query.
        """
        logger.info(f"Fetching chats for participant {participant_id}")
        
        # Get chat IDs using GSI
        chat_ids = self.repository.get_chats_for_participant(participant_id)
        
        # Fetch each chat
        chats = []
        for chat_id in chat_ids:
            chat = self.repository.get_chat(chat_id)
            if chat:
                chats.append(chat)
        
        logger.info(f"Found {len(chats)} chats for participant {participant_id}")
        return chats

