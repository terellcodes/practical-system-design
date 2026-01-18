"""
Copilot Service - FastAPI Application Entry Point

AI-powered assistant using LangGraph for user management and chat operations.
"""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.config import setup_logging, SERVICE_NAME, SERVICE_VERSION
from src.routes import health_router, copilot_router
from src.agent.graph import get_copilot_agent, close_copilot_agent
from src.services.chat_service_client import get_chat_service_client, close_chat_service_client
from src.services.user_service_client import close_user_service_client
from common.observability import setup_tracing, instrument_fastapi, CorrelationIdMiddleware

setup_logging()
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    logger.info("=" * 60)
    logger.info(f"{SERVICE_NAME} v{SERVICE_VERSION} starting up...")
    logger.info("=" * 60)

    # Initialize distributed tracing
    setup_tracing(service_name=SERVICE_NAME, filter_asgi_spans=False)

    try:
        # Initialize the copilot agent (and PostgresSaver checkpointer)
        await get_copilot_agent()
        logger.info("Copilot agent initialized")

        # Initialize chat service client (for Redis messaging)
        await get_chat_service_client()
        logger.info("Chat service client initialized")

        logger.info("All connections initialized")
    except Exception as e:
        logger.error(f"Failed to initialize: {e}")
        raise

    yield

    logger.info("Shutting down...")
    await close_copilot_agent()
    await close_chat_service_client()
    await close_user_service_client()
    logger.info("Shutdown complete")


app = FastAPI(
    title="Copilot Service",
    description="AI-powered assistant for managing users and chats",
    version=SERVICE_VERSION,
    lifespan=lifespan,
)

# Instrument FastAPI for distributed tracing
instrument_fastapi(app)

# CORS middleware - allows browser requests from any origin
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Correlation ID middleware for request tracking
app.add_middleware(CorrelationIdMiddleware)

app.include_router(health_router)
app.include_router(copilot_router, prefix="/api")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8003)
