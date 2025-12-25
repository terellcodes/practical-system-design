"""
Message-related Pydantic models

Used by:
- chat-service (primary owner)
- Any service that needs message data
"""

from datetime import datetime
from typing import Optional, List

from pydantic import BaseModel, Field


class MessageCreate(BaseModel):
    """Request model for creating a message"""
    chat_id: str = Field(..., description="Chat ID this message belongs to")
    sender_id: str = Field(..., description="ID of the user sending the message")
    content: str = Field(..., min_length=1, max_length=5000, description="Message content")

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
