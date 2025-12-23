"""
FastAPI Application Entry Point

A distributed user management service using Dapr for state management.
Implements Cache-Aside and Write-Through caching patterns.
"""

import logging

from fastapi import FastAPI

from src.config import setup_logging, STATESTORE_NAME, CACHE_NAME, CACHE_TTL_SECONDS
from src.routes import users_router, health_router

# Configure logging
setup_logging()
logger = logging.getLogger(__name__)

# FastAPI app initialization
app = FastAPI(
    title="User Service",
    description="A distributed user management service using Dapr for state management",
    version="1.0.0"
)

# Include routers
app.include_router(health_router)
app.include_router(users_router)


# ============================================================================
# Application Lifecycle Events
# ============================================================================

@app.on_event("startup")
async def startup_event():
    """Log application startup"""
    logger.info("=" * 50)
    logger.info("User Service starting up...")
    logger.info(f"State Store: {STATESTORE_NAME} (PostgreSQL)")
    logger.info(f"Cache: {CACHE_NAME} (Redis)")
    logger.info(f"Cache TTL: {CACHE_TTL_SECONDS} seconds")
    logger.info("=" * 50)


@app.on_event("shutdown")
async def shutdown_event():
    """Log application shutdown"""
    logger.info("User Service shutting down...")


# ============================================================================
# Main Entry Point
# ============================================================================

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

