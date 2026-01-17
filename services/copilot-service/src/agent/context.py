"""
Request context for storing user information during tool execution.
"""

from contextvars import ContextVar
from typing import Optional
from dataclasses import dataclass


@dataclass
class UserContext:
    """User context for the current request."""
    user_id: int
    username: Optional[str] = None
    user_name: Optional[str] = None


# Context variable to store user info for the current request
_user_context: ContextVar[Optional[UserContext]] = ContextVar(
    "user_context", default=None
)


def set_user_context(user_id: int, username: Optional[str], user_name: Optional[str]):
    """Set the user context for the current request."""
    _user_context.set(UserContext(
        user_id=user_id,
        username=username,
        user_name=user_name,
    ))


def get_user_context() -> Optional[UserContext]:
    """Get the user context for the current request."""
    return _user_context.get()


def clear_user_context():
    """Clear the user context."""
    _user_context.set(None)
