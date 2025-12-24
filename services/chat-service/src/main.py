"""
Chat Service - FastAPI Application Entry Point

Manages chat groups with DynamoDB (via LocalStack locally).
Supports real-time WebSocket connections for chat messaging.
"""

import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.config import setup_logging, SERVICE_NAME, SERVICE_VERSION, REDIS_URL, DYNAMODB_CONFIG
from src.routes import chats_router, health_router, websocket_router
from src import websocket as ws_module
from src.repositories.dynamodb import DynamoDBRepository
from common.database import create_dynamodb_resource

setup_logging()
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Chat Service",
    description="Manages chat groups with DynamoDB and real-time WebSocket messaging",
    version=SERVICE_VERSION,
)

# CORS middleware - allows browser requests from any origin
# In production, replace "*" with specific allowed origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins (use specific domains in production)
    allow_credentials=True,
    allow_methods=["*"],  # Allows all HTTP methods (GET, POST, PUT, DELETE, OPTIONS, etc.)
    allow_headers=["*"],  # Allows all headers
)

# REST API routes
app.include_router(health_router)
app.include_router(chats_router)

# WebSocket routes (mounted under /chats for NGINX routing)
app.include_router(websocket_router, prefix="/chats")


@app.on_event("startup")
async def startup_event():
    logger.info("=" * 60)
    logger.info(f"{SERVICE_NAME} v{SERVICE_VERSION} starting up...")
    logger.info("WebSocket endpoint: /chats/ws/{{chat_id}}?user_id={{user_id}}")
    
    # Initialize shared DynamoDB resource (reused across all requests)
    dynamodb_resource = create_dynamodb_resource(DYNAMODB_CONFIG)
    DynamoDBRepository.set_shared_resource(dynamodb_resource)
    logger.info("DynamoDB resource initialized and shared")
    
    # Initialize WebSocket connection manager with Redis pub/sub
    ws_module.manager = ws_module.create_connection_manager(REDIS_URL)
    await ws_module.manager.initialize()
    logger.info(f"WebSocket manager initialized with Redis pub/sub: {REDIS_URL}")
    
    logger.info("=" * 60)


@app.on_event("shutdown")
async def shutdown_event():
    logger.info("Shutting down...")
    
    # Close WebSocket manager and Redis connections
    if ws_module.manager:
        await ws_module.manager.close()
        logger.info("WebSocket manager closed")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8002)
