"""
Message-related Pydantic models

Used by:
- chat-service (primary owner)
- Any service that needs message data
"""

from datetime import datetime
from enum import Enum
from typing import Optional, List

from pydantic import BaseModel, Field


class UploadStatus(str, Enum):
    """Status of media upload for a message"""
    PENDING = "PENDING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


class MessageCreate(BaseModel):
    """Request model for creating a message"""
    chat_id: str = Field(..., description="Chat ID this message belongs to")
    sender_id: str = Field(..., description="ID of the user sending the message")
    content: str = Field(..., min_length=1, max_length=5000, description="Message content")
    
    # Attachment fields (optional)
    has_attachment: bool = Field(default=False, description="Whether message has a file attachment")
    attachment_filename: Optional[str] = Field(default=None, description="Original filename of attachment")
    attachment_content_type: Optional[str] = Field(default=None, description="MIME type of attachment (e.g., image/jpeg)")

    class Config:
        json_schema_extra = {
            "example": {
                "chat_id": "chat-123",
                "sender_id": "user-123",
                "content": "Hello, everyone!"
            }
        }


class Message(BaseModel):
    """Response model for a message"""
    message_id: str = Field(..., description="Message's unique identifier")
    chat_id: str = Field(..., description="Chat ID this message belongs to")
    sender_id: str = Field(..., description="ID of the user who sent the message")
    content: str = Field(..., description="Message content")
    created_at: datetime = Field(..., description="Timestamp when message was created")
    
    # Attachment fields (optional - only present for media messages)
    upload_status: Optional[UploadStatus] = Field(default=None, description="Status of media upload: PENDING, COMPLETED, or FAILED")
    s3_bucket: Optional[str] = Field(default=None, description="S3 bucket where attachment is stored")
    s3_object_key: Optional[str] = Field(default=None, description="S3 object key for the attachment")

    class Config:
        json_schema_extra = {
            "example": {
                "message_id": "msg-abc123",
                "chat_id": "chat-xyz789",
                "sender_id": "user-123",
                "content": "Hello, everyone!",
                "created_at": "2024-01-15T10:30:00"
            }
        }


class MessageList(BaseModel):
    """Response model for a list of messages"""
    messages: List[Message] = Field(default_factory=list, description="List of messages")
    count: int = Field(..., description="Number of messages returned")
    chat_id: str = Field(..., description="Chat ID for these messages")

    class Config:
        json_schema_extra = {
            "example": {
                "chat_id": "chat-xyz789",
                "count": 2,
                "messages": [
                    {
                        "message_id": "msg-abc123",
                        "chat_id": "chat-xyz789",
                        "sender_id": "user-123",
                        "content": "Hello!",
                        "created_at": "2024-01-15T10:30:00"
                    },
                    {
                        "message_id": "msg-def456",
                        "chat_id": "chat-xyz789",
                        "sender_id": "user-456",
                        "content": "Hi there!",
                        "created_at": "2024-01-15T10:31:00"
                    }
                ]
            }
        }


class UploadRequest(BaseModel):
    """Request model for requesting an upload URL"""
    sender_id: str = Field(..., description="ID of the user uploading the file")
    filename: str = Field(..., min_length=1, max_length=255, description="Original filename")
    content_type: str = Field(..., description="MIME type of the file (e.g., image/jpeg, video/mp4)")
    content: str = Field(default="", max_length=5000, description="Optional message content/caption")

    class Config:
        json_schema_extra = {
            "example": {
                "sender_id": "user-123",
                "filename": "photo.jpg",
                "content_type": "image/jpeg",
                "content": "Check out this photo!"
            }
        }


class UploadRequestResponse(BaseModel):
    """Response model for upload request - contains pre-signed URL"""
    message_id: str = Field(..., description="ID of the created message (in PENDING status)")
    upload_url: str = Field(..., description="Pre-signed URL for direct upload to S3")
    s3_key: str = Field(..., description="S3 object key where file will be stored")
    expires_in: int = Field(default=3600, description="Seconds until upload URL expires")

    class Config:
        json_schema_extra = {
            "example": {
                "message_id": "msg-abc123",
                "upload_url": "https://s3.amazonaws.com/chat-media/...",
                "s3_key": "chats/chat-xyz/attachments/msg-abc123/abc123_photo.jpg",
                "expires_in": 3600
            }
        }
