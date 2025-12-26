"""
Common package - Shared models and utilities for microservices

This package provides:
- Pydantic models that can be used by any service
- Database connection utilities (PostgreSQL, Redis, DynamoDB)
- Shared configuration helpers
"""

from common.models import (
    # User models
    User,
    UserCreate,
    UserUpdate,
    # Chat models
    Chat,
    ChatCreate,
    ChatParticipant,
    AddParticipantsRequest,
    ChatWithParticipants,
    # Messages models
    Message,
    # Response models
    MessageResponse,
    HealthResponse,
)

__version__ = "0.1.0"

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
    # Message models
    "Message",
    # Response models
    "MessageResponse",
    "HealthResponse",
]

