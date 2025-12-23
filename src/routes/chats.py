"""
Chat API endpoints
"""

from typing import List

from fastapi import APIRouter, Depends, status

from src.models.chat import (
    Chat,
    ChatCreate,
    ChatParticipant,
    AddParticipantsRequest,
    ChatWithParticipants,
    ChatMessageResponse,
)
from src.services.chat_service import ChatService

router = APIRouter(prefix="/chats", tags=["Chats"])


def get_chat_service() -> ChatService:
    """Dependency injection for ChatService"""
    return ChatService()


@router.post("", response_model=Chat, status_code=status.HTTP_201_CREATED)
async def create_chat(
    chat_data: ChatCreate,
    service: ChatService = Depends(get_chat_service)
):
    """
    Create a new chat.
    
    Generates a unique ID and stores the chat in DynamoDB.
    """
    return service.create_chat(chat_data)


@router.get("/{chat_id}", response_model=ChatWithParticipants)
async def get_chat(
    chat_id: str,
    service: ChatService = Depends(get_chat_service)
):
    """
    Get a chat by ID with all its participants.
    """
    return service.get_chat_with_participants(chat_id)


@router.delete("/{chat_id}", response_model=ChatMessageResponse)
async def delete_chat(
    chat_id: str,
    service: ChatService = Depends(get_chat_service)
):
    """
    Delete a chat and all its participants.
    """
    service.delete_chat(chat_id)
    return ChatMessageResponse(
        message=f"Chat {chat_id} deleted successfully",
        chat_id=chat_id
    )


@router.get("/participant/{participant_id}", response_model=List[Chat])
async def get_chats_for_participant(
    participant_id: str,
    service: ChatService = Depends(get_chat_service)
):
    """
    Get all chats for a participant.
    
    Uses DynamoDB GSI (participantId-index) for efficient query.
    """
    return service.get_chats_for_participant(participant_id)


@router.post("/{chat_id}/participants", response_model=List[ChatParticipant], status_code=status.HTTP_201_CREATED)
async def add_participants(
    chat_id: str,
    request: AddParticipantsRequest,
    service: ChatService = Depends(get_chat_service)
):
    """
    Add participants to a chat.
    
    Skips participants who are already in the chat.
    """
    return service.add_participants(chat_id, request.participant_ids)


@router.delete("/{chat_id}/participants/{participant_id}", response_model=ChatMessageResponse)
async def remove_participant(
    chat_id: str,
    participant_id: str,
    service: ChatService = Depends(get_chat_service)
):
    """
    Remove a participant from a chat.
    """
    service.remove_participant(chat_id, participant_id)
    return ChatMessageResponse(
        message=f"Participant {participant_id} removed from chat {chat_id}",
        chat_id=chat_id
    )

