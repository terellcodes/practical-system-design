"""
Pydantic models for request/response validation
"""

from src.models.user import (
    User,
    UserCreate,
    UserUpdate,
    HealthResponse,
    MessageResponse,
)

from src.models.chat import (
    Chat,
    ChatCreate,
    ChatParticipant,
    AddParticipantsRequest,
    ChatWithParticipants,
    ChatMessageResponse,
)

__all__ = [
    # User models
    "User",
    "UserCreate",
    "UserUpdate",
    "HealthResponse",
    "MessageResponse",
    # Chat models
    "Chat",
    "ChatCreate",
    "ChatParticipant",
    "AddParticipantsRequest",
    "ChatWithParticipants",
    "ChatMessageResponse",
]

