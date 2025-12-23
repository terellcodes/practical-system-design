"""
Health check endpoints
"""

from datetime import datetime

from fastapi import APIRouter

from src.models.user import HealthResponse

router = APIRouter(prefix="", tags=["Health"])


@router.get("/health", response_model=HealthResponse)
async def health_check():
    """
    Health check endpoint to verify service is running.
    """
    return HealthResponse(
        status="healthy",
        service="user-service",
        timestamp=datetime.now()
    )

