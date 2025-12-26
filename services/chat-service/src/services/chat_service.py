"""
Chat business logic service
"""

import logging
import uuid
from typing import List, Optional

from fastapi import HTTPException, status

from common.models import Chat, ChatCreate, ChatParticipant, ChatWithParticipants, UploadRequest, UploadRequestResponse
from common.storage import create_s3_client, generate_presigned_upload_url, generate_s3_object_key
from src.repositories.dynamodb import DynamoDBRepository
from src.config import S3_CONFIG

logger = logging.getLogger(__name__)


class ChatService:
    """Service layer for chat operations"""

    def __init__(self, repository: Optional[DynamoDBRepository] = None, s3_client=None):
        self.repository = repository or DynamoDBRepository()
        self._s3_client = s3_client
    
    @property
    def s3_client(self):
        """Lazy initialization of S3 client"""
        if self._s3_client is None:
            self._s3_client = create_s3_client(S3_CONFIG)
        return self._s3_client

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
    
    def get_messages_from_inbox(self, chat_id: str, recipient_id: str) -> dict:
        return self.repository.get_inbox_messages(recipient_id)
    
    def request_upload(self, chat_id: str, request: UploadRequest) -> UploadRequestResponse:
        """
        Request a pre-signed URL for uploading a file attachment.
        
        This creates a message in PENDING status and returns a pre-signed URL
        for the client to upload directly to S3. Once the upload completes,
        S3 triggers an event that updates the message status to COMPLETED.
        
        Args:
            chat_id: The chat to attach the file to
            request: Upload request with filename, content_type, sender_id
        
        Returns:
            UploadRequestResponse with message_id, upload_url, s3_key
        """
        # Verify chat exists
        self.get_chat(chat_id)
        
        # Verify sender is a participant
        if not self.repository.is_participant(chat_id, request.sender_id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"User {request.sender_id} is not a participant in chat {chat_id}"
            )
        
        # Generate message ID first (we need it for the S3 key)
        message_id = f"msg-{uuid.uuid4().hex[:12]}"
        
        # Generate S3 object key
        s3_key = generate_s3_object_key(
            chat_id=chat_id,
            message_id=message_id,
            filename=request.filename,
            content_type=request.content_type
        )
        
        # Generate pre-signed upload URL
        upload_url = generate_presigned_upload_url(
            s3_client=self.s3_client,
            bucket=S3_CONFIG.bucket_name,
            object_key=s3_key,
            content_type=request.content_type,
            expiration=3600  # 1 hour
        )
        
        if not upload_url:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to generate upload URL"
            )
        
        # Create message in PENDING status (no inbox fanout yet)
        saved_message = self.repository.save_message(
            chat_id=chat_id,
            sender_id=request.sender_id,
            content=request.content or f"[Attachment: {request.filename}]",
            recipient_ids=None,  # Don't fanout yet - wait for upload to complete
            upload_status="PENDING",
            s3_bucket=S3_CONFIG.bucket_name,
            s3_object_key=s3_key,
        )
        
        logger.info(f"Created PENDING message {message_id} for upload in chat {chat_id}")
        
        return UploadRequestResponse(
            message_id=saved_message['message_id'],
            upload_url=upload_url,
            s3_key=s3_key,
            expires_in=3600
        )

