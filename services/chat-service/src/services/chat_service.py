"""
Chat business logic service
"""

import logging
import uuid
from typing import List, Optional

from fastapi import HTTPException, status

from common.models import Chat, ChatCreate, ChatParticipant, ChatWithParticipants
from src.repositories.dynamodb import DynamoDBRepository

logger = logging.getLogger(__name__)


class ChatService:
    """Service layer for chat operations"""

    def __init__(self, repository: Optional[DynamoDBRepository] = None):
        self.repository = repository or DynamoDBRepository()

    def create_chat(self, chat_data: ChatCreate) -> Chat:
        """Create a new chat."""
        chat_id = f"chat-{uuid.uuid4().hex[:12]}"
        
        return self.repository.create_chat(
            chat_id=chat_id,
            name=chat_data.name,
            metadata=chat_data.metadata or {},
        )

    def get_chat(self, chat_id: str) -> Chat:
        """Get a chat by ID."""
        chat = self.repository.get_chat(chat_id)
        
        if not chat:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Chat {chat_id} not found"
            )
        
        return chat

    def get_chat_with_participants(self, chat_id: str) -> ChatWithParticipants:
        """Get a chat with all participants."""
        chat = self.get_chat(chat_id)
        participants = self.repository.get_participants_for_chat(chat_id)
        
        return ChatWithParticipants(chat=chat, participants=participants)

    def delete_chat(self, chat_id: str) -> bool:
        """Delete a chat and all participants."""
        self.get_chat(chat_id)  # Verify exists
        
        # Remove all participants
        participants = self.repository.get_participants_for_chat(chat_id)
        for p in participants:
            self.repository.remove_participant(chat_id, p.participant_id)
        
        self.repository.delete_chat(chat_id)
        return True

    def add_participants(self, chat_id: str, participant_ids: List[str]) -> List[ChatParticipant]:
        """Add participants to a chat."""
        self.get_chat(chat_id)  # Verify exists
        
        added = []
        for pid in participant_ids:
            if not self.repository.is_participant(chat_id, pid):
                participant = self.repository.add_participant(chat_id, pid)
                added.append(participant)
        
        return added

    def remove_participant(self, chat_id: str, participant_id: str) -> bool:
        """Remove a participant from a chat."""
        self.get_chat(chat_id)  # Verify exists
        
        if not self.repository.is_participant(chat_id, participant_id):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Participant {participant_id} not in chat {chat_id}"
            )
        
        self.repository.remove_participant(chat_id, participant_id)
        return True

    def get_chats_for_participant(self, participant_id: str) -> List[Chat]:
        """Get all chats for a participant."""
        chat_ids = self.repository.get_chats_for_participant(participant_id)
        
        chats = []
        for cid in chat_ids:
            chat = self.repository.get_chat(cid)
            if chat:
                chats.append(chat)
        
        return chats
