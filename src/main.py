"""
FastAPI Application Entry Point

A distributed service using:
- Dapr for state management (Users: PostgreSQL + Redis cache)
- DynamoDB via LocalStack (Chats: with GSI for efficient queries)
"""

import logging

from fastapi import FastAPI

from src.config import (
    setup_logging,
    STATESTORE_NAME,
    CACHE_NAME,
    CACHE_TTL_SECONDS,
    DYNAMODB_ENDPOINT,
    CHATS_TABLE,
    CHAT_PARTICIPANTS_TABLE,
)
from src.routes import users_router, health_router, chats_router

# Configure logging
setup_logging()
logger = logging.getLogger(__name__)

# FastAPI app initialization
app = FastAPI(
    title="Distributed Service",
    description="A distributed service demonstrating multiple data store patterns: PostgreSQL, Redis, and DynamoDB",
    version="2.0.0"
)

# Include routers
app.include_router(health_router)
app.include_router(users_router)
app.include_router(chats_router)


# ============================================================================
# Application Lifecycle Events
# ============================================================================

@app.on_event("startup")
async def startup_event():
    """Log application startup"""
    logger.info("=" * 60)
    logger.info("Distributed Service starting up...")
    logger.info("-" * 60)
    logger.info("User Domain (Dapr):")
    logger.info(f"  State Store: {STATESTORE_NAME} (PostgreSQL)")
    logger.info(f"  Cache: {CACHE_NAME} (Redis)")
    logger.info(f"  Cache TTL: {CACHE_TTL_SECONDS} seconds")
    logger.info("-" * 60)
    logger.info("Chat Domain (boto3 + DynamoDB):")
    logger.info(f"  DynamoDB Endpoint: {DYNAMODB_ENDPOINT}")
    logger.info(f"  Chats Table: {CHATS_TABLE}")
    logger.info(f"  Participants Table: {CHAT_PARTICIPANTS_TABLE}")
    logger.info("=" * 60)


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

