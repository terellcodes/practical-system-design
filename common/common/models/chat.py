"""
Chat-related Pydantic models

Used by:
- chat-service (primary owner)
- Any service that needs chat data
"""

from datetime import datetime
from typing import Optional, Dict, Any, List

from pydantic import BaseModel, Field


class ChatCreate(BaseModel):
    """Request model for creating a chat"""
    name: str = Field(..., min_length=1, max_length=100, description="Chat name")
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Additional chat metadata")

    class Config:
        json_schema_extra = {
            "example": {
                "name": "Team Chat",
                "metadata": {"description": "General team discussion"}
            }
        }


class Chat(BaseModel):
    """Response model for a chat"""
    id: str = Field(..., description="Chat's unique identifier")
    name: str = Field(..., description="Chat name")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional chat metadata")
    created_at: datetime = Field(..., description="Timestamp when chat was created")

    class Config:
        json_schema_extra = {
            "example": {
                "id": "chat-abc123",
                "name": "Team Chat",
                "metadata": {"description": "General team discussion"},
                "created_at": "2024-01-15T10:30:00"
            }
        }


class ChatParticipant(BaseModel):
    """Model for a chat participant relationship"""
    chat_id: str = Field(..., description="Chat ID")
    participant_id: str = Field(..., description="Participant ID (user ID)")
    joined_at: datetime = Field(..., description="Timestamp when participant joined")

    class Config:
        json_schema_extra = {
            "example": {
                "chat_id": "chat-abc123",
                "participant_id": "user-1",
                "joined_at": "2024-01-15T10:30:00"
            }
        }


class AddParticipantsRequest(BaseModel):
    """Request model for adding participants to a chat"""
    participant_ids: List[str] = Field(..., min_length=1, description="List of participant IDs to add")

    class Config:
        json_schema_extra = {
            "example": {
                "participant_ids": ["user-1", "user-2", "user-3"]
            }
        }


class ChatWithParticipants(BaseModel):
    """Response model for a chat with its participants"""
    chat: Chat
    participants: List[ChatParticipant] = Field(default_factory=list)

    class Config:
        json_schema_extra = {
            "example": {
                "chat": {
                    "id": "chat-abc123",
                    "name": "Team Chat",
                    "metadata": {},
                    "created_at": "2024-01-15T10:30:00"
                },
                "participants": [
                    {"chat_id": "chat-abc123", "participant_id": "user-1", "joined_at": "2024-01-15T10:30:00"}
                ]
            }
        }

