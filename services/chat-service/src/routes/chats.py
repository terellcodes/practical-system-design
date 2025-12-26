"""
Chat CRUD API endpoints
"""

from typing import List

from fastapi import APIRouter, Depends, status

from common.models import (
    Chat,
    ChatCreate,
    ChatParticipant,
    AddParticipantsRequest,
    ChatWithParticipants,
    MessageResponse,
    UploadRequest,
    UploadRequestResponse,
)
from src.services.chat_service import ChatService

router = APIRouter(prefix="/chats", tags=["Chats"])


def get_chat_service() -> ChatService:
    return ChatService()


@router.post("", response_model=Chat, status_code=status.HTTP_201_CREATED)
async def create_chat(
    chat_data: ChatCreate,
    service: ChatService = Depends(get_chat_service)
):
    """Create a new chat."""
    return service.create_chat(chat_data)


@router.get("/{chat_id}", response_model=ChatWithParticipants)
async def get_chat(
    chat_id: str,
    service: ChatService = Depends(get_chat_service)
):
    """Get a chat with participants."""
    return service.get_chat_with_participants(chat_id)


@router.delete("/{chat_id}", response_model=MessageResponse)
async def delete_chat(
    chat_id: str,
    service: ChatService = Depends(get_chat_service)
):
    """Delete a chat and all participants."""
    service.delete_chat(chat_id)
    return MessageResponse(message=f"Chat {chat_id} deleted", id=chat_id)


@router.get("/participant/{participant_id}", response_model=List[Chat])
async def get_chats_for_participant(
    participant_id: str,
    service: ChatService = Depends(get_chat_service)
):
    """Get all chats for a participant (uses GSI)."""
    return service.get_chats_for_participant(participant_id)


@router.post("/{chat_id}/participants", response_model=List[ChatParticipant], status_code=status.HTTP_201_CREATED)
async def add_participants(
    chat_id: str,
    request: AddParticipantsRequest,
    service: ChatService = Depends(get_chat_service)
):
    """Add participants to a chat."""
    return service.add_participants(chat_id, request.participant_ids)


@router.delete("/{chat_id}/participants/{participant_id}", response_model=MessageResponse)
async def remove_participant(
    chat_id: str,
    participant_id: str,
    service: ChatService = Depends(get_chat_service)
):
    """Remove a participant from a chat."""
    service.remove_participant(chat_id, participant_id)
    return MessageResponse(
        message=f"Participant {participant_id} removed from chat {chat_id}",
        id=chat_id
    )

@router.get("/{chat_id}/sync")
async def sync_chat(
    chat_id: str,
    user_id: str,
    service: ChatService = Depends(get_chat_service)
):
    """Fetch undelivered messsage from inbox"""
    return service.get_messages_from_inbox(chat_id, user_id)


@router.post("/{chat_id}/messages/upload-request", response_model=UploadRequestResponse, status_code=status.HTTP_201_CREATED)
async def request_upload(
    chat_id: str,
    request: UploadRequest,
    service: ChatService = Depends(get_chat_service)
):
    """
    Request a pre-signed URL for uploading a file attachment.
    
    This endpoint:
    1. Creates a message in PENDING status
    2. Returns a pre-signed URL for direct upload to S3
    
    The client should then:
    1. PUT the file to the upload_url with the correct Content-Type
    2. S3 will trigger an event when upload completes
    3. The message status will be updated to COMPLETED
    4. Recipients will then see the message with the attachment
    """
    return service.request_upload(chat_id, request)

