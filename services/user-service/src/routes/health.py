"""
Health check endpoint
"""

import logging
from datetime import datetime

from fastapi import APIRouter
from sqlalchemy import text

from common.models import HealthResponse
from src.config import SERVICE_NAME, SERVICE_VERSION
from src.database import get_async_engine, get_redis_client

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Health"])


@router.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint."""
    dependencies = {}
    
    # Check PostgreSQL
    try:
        engine = get_async_engine()
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        dependencies["postgres"] = "healthy"
    except Exception as e:
        logger.error(f"PostgreSQL health check failed: {e}")
        dependencies["postgres"] = "unhealthy"
    
    # Check Redis
    try:
        redis = get_redis_client()
        await redis.ping()
        dependencies["redis"] = "healthy"
    except Exception as e:
        logger.error(f"Redis health check failed: {e}")
        dependencies["redis"] = "unhealthy"
    
    all_healthy = all(v == "healthy" for v in dependencies.values())
    
    return HealthResponse(
        status="healthy" if all_healthy else "degraded",
        service=SERVICE_NAME,
        version=SERVICE_VERSION,
        timestamp=datetime.now(),
        dependencies=dependencies,
    )
