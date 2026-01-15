"""
Contact-related SQLModel models

Used by user-service for managing contacts.
Contacts use a unidirectional design where contact_one_id < contact_two_id
to ensure a single row represents the relationship between two users.
"""

from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import Column, Integer, UniqueConstraint
from sqlmodel import SQLModel, Field


class Contact(SQLModel, table=True):
    """
    Contact model - represents a bidirectional contact relationship.
    
    Uses unidirectional storage: contact_one_id is always the smaller user ID.
    This ensures one row per relationship and simpler uniqueness constraints.
    """
    __tablename__ = "contacts"
    __table_args__ = (
        UniqueConstraint('contact_one_id', 'contact_two_id', name='uq_contacts_pair'),
    )
    
    id: Optional[int] = Field(default=None, primary_key=True, description="Contact's unique identifier")
    contact_one_id: int = Field(
        sa_column=Column(Integer, nullable=False, index=True),
        description="First user ID (always the smaller ID)"
    )
    contact_two_id: int = Field(
        sa_column=Column(Integer, nullable=False, index=True),
        description="Second user ID (always the larger ID)"
    )
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc).replace(tzinfo=None),
        description="Timestamp when contact was created"
    )


class ContactWithUser(SQLModel):
    """Contact response model with user details"""
    id: int
    contact_id: int  # The other user's ID
    contact_username: str
    contact_name: str
    created_at: datetime


class ContactCheckResponse(SQLModel):
    """Response model for checking if two users are contacts"""
    are_contacts: bool
    user_id_1: int
    user_id_2: int



