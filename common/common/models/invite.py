"""
Invite-related SQLModel models

Used by user-service for managing contact invites.
"""

from datetime import datetime, timezone
from enum import Enum
from typing import Optional

from sqlalchemy import Column, String
from sqlmodel import SQLModel, Field


class InviteStatus(str, Enum):
    """Status of an invite"""
    PENDING = "pending"
    ACCEPTED = "accepted"
    REJECTED = "rejected"


class InviteCreate(SQLModel):
    """Request model for creating an invite"""
    connect_pin: str = Field(..., min_length=1, max_length=8, description="Connect PIN of the user to invite")


class InviteUpdate(SQLModel):
    """Request model for accepting/rejecting an invite"""
    status: InviteStatus = Field(..., description="New status (accepted or rejected)")


class InviteBase(SQLModel):
    """Base invite model with shared fields"""
    invitor_id: int = Field(..., foreign_key="users.id", index=True, description="ID of user who sent the invite")
    invitee_id: int = Field(..., foreign_key="users.id", index=True, description="ID of user who received the invite")
    status: str = Field(
        default=InviteStatus.PENDING.value, 
        sa_column=Column(String(20), nullable=False, default="pending"),
        description="Current status of the invite"
    )


class Invite(InviteBase, table=True):
    """Invite model - serves as both API model and database table"""
    __tablename__ = "invites"
    
    id: Optional[int] = Field(default=None, primary_key=True, description="Invite's unique identifier")
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc).replace(tzinfo=None),
        description="Timestamp when invite was created"
    )
    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc).replace(tzinfo=None),
        description="Timestamp when invite was last updated"
    )


class InviteWithUsers(SQLModel):
    """Invite response model with user details"""
    id: int
    invitor_id: int
    invitor_username: str
    invitor_name: str
    invitee_id: int
    invitee_username: str
    invitee_name: str
    status: InviteStatus
    created_at: datetime
    updated_at: datetime

