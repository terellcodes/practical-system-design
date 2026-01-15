"""
Inbox-related Pydantic models

Used by:
- chat-service (primary owner)
- Any service that needs inbox data

The Inbox table uses the inbox pattern for user-centric message views.
Each inbox item represents an undelivered message for a specific recipient.
"""

from datetime import datetime
from typing import Optional, List, Dict, Any

from pydantic import BaseModel, Field

from common.models.messages import Message


class InboxList(BaseModel):
    """Response model for a list of inbox items"""
    items: List[Message] = Field(default_factory=list, description="List of inbox items")
    count: int = Field(..., description="Number of inbox items returned")
    recipient_id: int = Field(..., description="Recipient user ID for these inbox items")
    last_evaluated_key: Optional[Dict[str, Any]] = Field(
        default=None, 
        description="Pagination token for fetching next page"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "recipient_id": 123,
                "count": 2,
                "items": [
                    {
                        "recipient_id": 123,
                        "message_id": "msg-abc123",
                        "chat_id": "chat-xyz789",
                        "created_at": "2024-01-15T10:30:00"
                    },
                    {
                        "recipient_id": 123,
                        "message_id": "msg-def456",
                        "chat_id": "chat-xyz789",
                        "created_at": "2024-01-15T10:31:00"
                    }
                ],
                "last_evaluated_key": None
            }
        }

