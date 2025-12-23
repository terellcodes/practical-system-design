"""
Chat Service - API routes
"""

from src.routes.chats import router as chats_router
from src.routes.health import router as health_router
from src.routes.websocket import router as websocket_router

__all__ = [
    "chats_router",
    "health_router",
    "websocket_router",
]
