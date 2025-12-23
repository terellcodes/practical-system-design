"""
Shared Pydantic models

These models can be imported by any service:
    from common.models import User, Chat, ChatParticipant
"""

from common.models.user import (
    User,
    UserCreate,
    UserUpdate,
)

from common.models.chat import (
    Chat,
    ChatCreate,
    ChatParticipant,
    AddParticipantsRequest,
    ChatWithParticipants,
)

from common.models.responses import (
    MessageResponse,
    HealthResponse,
)

__all__ = [
    # User models
    "User",
    "UserCreate",
    "UserUpdate",
    # Chat models
    "Chat",
    "ChatCreate",
    "ChatParticipant",
    "AddParticipantsRequest",
    "ChatWithParticipants",
    # Response models
    "MessageResponse",
    "HealthResponse",
]

