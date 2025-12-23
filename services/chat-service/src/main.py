"""
Chat Service - FastAPI Application Entry Point

Manages chat groups with DynamoDB (via LocalStack locally).
"""

import logging

from fastapi import FastAPI

from src.config import setup_logging, SERVICE_NAME, SERVICE_VERSION
from src.routes import chats_router, health_router

setup_logging()
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Chat Service",
    description="Manages chat groups with DynamoDB",
    version=SERVICE_VERSION,
)

app.include_router(health_router)
app.include_router(chats_router)


@app.on_event("startup")
async def startup_event():
    logger.info("=" * 60)
    logger.info(f"{SERVICE_NAME} v{SERVICE_VERSION} starting up...")
    logger.info("=" * 60)


@app.on_event("shutdown")
async def shutdown_event():
    logger.info("Shutting down...")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8002)
