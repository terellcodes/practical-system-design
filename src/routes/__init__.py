"""
API routes
"""

from src.routes.users import router as users_router
from src.routes.health import router as health_router
from src.routes.chats import router as chats_router

__all__ = [
    "users_router",
    "health_router",
    "chats_router",
]

