"""
User Service - API routes
"""

from src.routes.users import router as users_router
from src.routes.health import router as health_router
from src.routes.invites import router as invites_router
from src.routes.contacts import router as contacts_router

__all__ = [
    "users_router",
    "health_router",
    "invites_router",
    "contacts_router",
]
