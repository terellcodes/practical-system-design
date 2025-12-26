"""
Common package - Shared models and utilities for microservices

This package provides:
- Pydantic models that can be used by any service
- Database connection utilities (PostgreSQL, Redis, DynamoDB)
- Storage utilities (S3)
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
    UploadStatus,
    # Response models
    MessageResponse,
    HealthResponse,
)

from common.storage import (
    S3Config,
    create_s3_client,
    generate_presigned_upload_url,
    generate_presigned_download_url,
    generate_s3_object_key,
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
    "UploadStatus",
    # Response models
    "MessageResponse",
    "HealthResponse",
    # Storage utilities
    "S3Config",
    "create_s3_client",
    "generate_presigned_upload_url",
    "generate_presigned_download_url",
    "generate_s3_object_key",
]

