"""
User Service - API routes
"""

from src.routes.users import router as users_router
from src.routes.health import router as health_router
from src.routes.invites import router as invites_router

__all__ = [
    "users_router",
    "health_router",
    "invites_router",
]
