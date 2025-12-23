"""
Database connection management for User Service

Uses shared utilities from common package.
"""

import logging
from typing import Optional

import asyncpg
import redis.asyncio as redis

from common.database import create_postgres_pool, create_redis_client
from src.config import POSTGRES_CONFIG, REDIS_CONFIG

logger = logging.getLogger(__name__)

# Connection pools (initialized on startup)
_pg_pool: Optional[asyncpg.Pool] = None
_redis_client: Optional[redis.Redis] = None


async def init_postgres() -> asyncpg.Pool:
    """Initialize PostgreSQL connection pool"""
    global _pg_pool
    
    _pg_pool = await create_postgres_pool(POSTGRES_CONFIG)
    
    # Create users table if it doesn't exist
    async with _pg_pool.acquire() as conn:
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id SERIAL PRIMARY KEY,
                name VARCHAR(100) NOT NULL,
                email VARCHAR(255) NOT NULL,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
            )
        """)
        await conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_users_email ON users(email)
        """)
    
    logger.info("PostgreSQL initialized with users table")
    return _pg_pool


async def init_redis() -> redis.Redis:
    """Initialize Redis connection"""
    global _redis_client
    _redis_client = await create_redis_client(REDIS_CONFIG)
    return _redis_client


async def close_postgres():
    """Close PostgreSQL connection pool"""
    global _pg_pool
    if _pg_pool:
        await _pg_pool.close()
        _pg_pool = None
        logger.info("PostgreSQL connection pool closed")


async def close_redis():
    """Close Redis connection"""
    global _redis_client
    if _redis_client:
        await _redis_client.close()
        _redis_client = None
        logger.info("Redis connection closed")


def get_pg_pool() -> asyncpg.Pool:
    """Get the PostgreSQL connection pool"""
    if _pg_pool is None:
        raise RuntimeError("PostgreSQL pool not initialized")
    return _pg_pool


def get_redis_client() -> redis.Redis:
    """Get the Redis client"""
    if _redis_client is None:
        raise RuntimeError("Redis client not initialized")
    return _redis_client
