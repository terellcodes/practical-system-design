"""
User Service - FastAPI Application Entry Point

Manages users with PostgreSQL (primary) + Redis (cache).
"""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.config import setup_logging, SERVICE_NAME, SERVICE_VERSION
from src.database import init_postgres, init_redis, close_postgres, close_redis
from src.routes import users_router, health_router, invites_router, contacts_router

setup_logging()
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    logger.info("=" * 60)
    logger.info(f"{SERVICE_NAME} v{SERVICE_VERSION} starting up...")
    logger.info("=" * 60)
    
    try:
        await init_postgres()
        await init_redis()
        logger.info("All connections initialized")
    except Exception as e:
        logger.error(f"Failed to initialize: {e}")
        raise
    
    yield
    
    logger.info("Shutting down...")
    await close_redis()
    await close_postgres()


app = FastAPI(
    title="User Service",
    description="Manages users with PostgreSQL and Redis caching",
    version=SERVICE_VERSION,
    lifespan=lifespan,
)

# CORS middleware - allows browser requests from any origin

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True, 
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
)

app.include_router(health_router)
app.include_router(users_router, prefix="/api")
app.include_router(invites_router, prefix="/api")
app.include_router(contacts_router, prefix="/api")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
