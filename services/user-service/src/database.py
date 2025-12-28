"""
Database connection management for User Service

Uses SQLModel with SQLAlchemy async engine.
"""

import logging
from typing import Optional

import redis.asyncio as redis
from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine
from sqlmodel import SQLModel

from common.database import create_redis_client
from src.config import POSTGRES_CONFIG, REDIS_CONFIG
from common.models import User

logger = logging.getLogger(__name__)

# Connection pools (initialized on startup)
_async_engine: Optional[AsyncEngine] = None
_redis_client: Optional[redis.Redis] = None


async def init_postgres() -> AsyncEngine:
    """Initialize PostgreSQL async engine"""
    global _async_engine
    
    # Create SQLAlchemy async engine
    database_url = f"postgresql+asyncpg://{POSTGRES_CONFIG.user}:{POSTGRES_CONFIG.password}@{POSTGRES_CONFIG.host}:{POSTGRES_CONFIG.port}/{POSTGRES_CONFIG.database}"
    
    _async_engine = create_async_engine(database_url, echo=False)
    
    # Create all tables (SQLModel will handle this)
    async with _async_engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)
    
    logger.info("PostgreSQL initialized with SQLModel tables")
    return _async_engine


async def init_redis() -> redis.Redis:
    """Initialize Redis connection"""
    global _redis_client
    _redis_client = await create_redis_client(REDIS_CONFIG)
    return _redis_client


async def close_postgres():
    """Close PostgreSQL async engine"""
    global _async_engine
    if _async_engine:
        await _async_engine.dispose()
        _async_engine = None
        logger.info("PostgreSQL async engine closed")


async def close_redis():
    """Close Redis connection"""
    global _redis_client
    if _redis_client:
        await _redis_client.close()
        _redis_client = None
        logger.info("Redis connection closed")


def get_async_engine() -> AsyncEngine:
    """Get the PostgreSQL async engine"""
    if _async_engine is None:
        raise RuntimeError("PostgreSQL async engine not initialized")
    return _async_engine


def get_redis_client() -> redis.Redis:
    """Get the Redis client"""
    if _redis_client is None:
        raise RuntimeError("Redis client not initialized")
    return _redis_client
