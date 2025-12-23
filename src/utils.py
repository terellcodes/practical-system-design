"""
Utility functions for data conversion
"""

from datetime import datetime
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from src.models.user import User


def get_user_key(user_id: int) -> str:
    """Generate a consistent key for user storage"""
    return f"user-{user_id}"


def get_next_id_key() -> str:
    """Key for storing the next available user ID"""
    return "next-user-id"


def user_to_dict(user: "User") -> dict:
    """Convert User model to dictionary for storage"""
    return {
        "id": user.id,
        "name": user.name,
        "email": user.email,
        "created_at": user.created_at.isoformat()
    }


def dict_to_user(data: dict) -> "User":
    """Convert dictionary to User model"""
    from src.models.user import User
    
    return User(
        id=data["id"],
        name=data["name"],
        email=data["email"],
        created_at=datetime.fromisoformat(data["created_at"])
    )

