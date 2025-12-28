"""
User-related SQLModel models

Used by:
- user-service (primary owner, with table=True)
- Any service that needs user data (as regular models)
"""

from datetime import datetime, timezone
from typing import Optional

from sqlmodel import SQLModel, Field


class UserCreate(SQLModel):
    """Request model for creating a user"""
    name: str = Field(..., min_length=1, max_length=100, description="User's full name")
    email: str = Field(..., description="User's email address")


class UserLoginRequest(SQLModel):
    """Request model for simple username-based login"""
    username: str = Field(..., min_length=1, max_length=50, description="Username")


class UserUpdate(SQLModel):
    """Request model for updating a user"""
    name: Optional[str] = Field(None, min_length=1, max_length=100, description="User's full name")
    email: Optional[str] = Field(None, description="User's email address")


class User(SQLModel, table=True):
    """User model - serves as both API model and database table"""
    __tablename__ = "users"  # Explicitly set table name to 'users'
    
    id: Optional[int] = Field(default=None, primary_key=True, description="User's unique identifier")
    name: str = Field(max_length=100, description="User's full name")
    email: str = Field(description="User's email address")
    username: str = Field(max_length=50, unique=True, description="User's username")
    connect_pin: str = Field(max_length=8, unique=True, description="User's unique connect PIN")
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc).replace(tzinfo=None),
        description="Timestamp when user was created"
    )
