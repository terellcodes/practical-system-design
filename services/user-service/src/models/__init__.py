"""
User Service - Models

Re-exports from common package for convenience.
Service-specific models can also be added here.
"""

# Import all models from common
from common.models import (
    User,
    UserCreate,
    UserUpdate,
    MessageResponse,
    HealthResponse,
    # Chat models also available if needed
    Chat,
    ChatParticipant,
)

__all__ = [
    "User",
    "UserCreate",
    "UserUpdate",
    "MessageResponse",
    "HealthResponse",
    "Chat",
    "ChatParticipant",
]
