"""
Health check endpoint
"""

from fastapi import APIRouter

from src.config import SERVICE_NAME, SERVICE_VERSION

router = APIRouter(tags=["Health"])


@router.get("/health")
async def health_check():
    """Health check endpoint for the copilot service."""
    return {
        "status": "healthy",
        "service": SERVICE_NAME,
        "version": SERVICE_VERSION,
    }
