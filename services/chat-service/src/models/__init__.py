"""
Chat Service - Models

Re-exports from common package for convenience.
Service-specific models can also be added here.
"""

# Import all models from common
from common.models import (
    # Chat models
    Chat,
    ChatCreate,
    ChatParticipant,
    AddParticipantsRequest,
    ChatWithParticipants,
    # Response models
    MessageResponse,
    HealthResponse,
    # User models also available if needed
    User,
)

__all__ = [
    "Chat",
    "ChatCreate",
    "ChatParticipant",
    "AddParticipantsRequest",
    "ChatWithParticipants",
    "MessageResponse",
    "HealthResponse",
    "User",
]
