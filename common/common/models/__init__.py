"""
Shared Pydantic models

These models can be imported by any service:
    from common.models import User, Chat, ChatParticipant
"""

from common.models.user import (
    User,
    UserCreate,
    UserUpdate,
    UserLoginRequest,
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

from common.models.messages import (
    MessageCreate,
    Message,
    UploadStatus,
    UploadRequest,
    UploadRequestResponse,
)

from common.models.inbox import (
    InboxList,
)

from common.models.invite import (
    Invite,
    InviteCreate,
    InviteUpdate,
    InviteStatus,
    InviteWithUsers,
)
__all__ = [
    # User models
    "User",
    "UserCreate",
    "UserUpdate",
    "UserLoginRequest",
    # Chat models
    "Chat",
    "ChatCreate",
    "ChatParticipant",
    "AddParticipantsRequest",
    "ChatWithParticipants",
    # Message models
    "Message",
    "MessageCreate",
    "UploadStatus",
    "UploadRequest",
    "UploadRequestResponse",
    # Inbox models
    "InboxList",
    # Invite models
    "Invite",
    "InviteCreate",
    "InviteUpdate",
    "InviteStatus",
    "InviteWithUsers",
    # Response models
    "MessageResponse",
    "HealthResponse",
]

