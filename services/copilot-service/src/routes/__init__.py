"""
API Routes
"""

from src.routes.health import router as health_router
from src.routes.copilot import router as copilot_router

__all__ = ["health_router", "copilot_router"]
