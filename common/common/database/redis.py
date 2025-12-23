"""
Redis connection utilities

Usage:
    from common.database import create_redis_client, RedisConfig
    
    config = RedisConfig(host="redis", port=6379)
    client = await create_redis_client(config)
"""

import logging
from dataclasses import dataclass
from typing import Optional

import redis.asyncio as redis

logger = logging.getLogger(__name__)


@dataclass
class RedisConfig:
    """Redis connection configuration"""
    host: str = "localhost"
    port: int = 6379
    db: int = 0
    password: Optional[str] = None
    decode_responses: bool = True
    
    @property
    def url(self) -> str:
        """Return connection URL"""
        if self.password:
            return f"redis://:{self.password}@{self.host}:{self.port}/{self.db}"
        return f"redis://{self.host}:{self.port}/{self.db}"
    
    @classmethod
    def from_url(cls, url: str) -> "RedisConfig":
        """
        Create config from REDIS_URL.
        Format: redis://[:password@]host:port/db
        """
        url = url.replace("redis://", "")
        
        password = None
        if "@" in url:
            auth, url = url.split("@")
            password = auth.replace(":", "")
        
        host_port, db = url.split("/") if "/" in url else (url, "0")
        
        if ":" in host_port:
            host, port = host_port.split(":")
            port = int(port)
        else:
            host = host_port
            port = 6379
        
        return cls(
            host=host,
            port=port,
            db=int(db),
            password=password,
        )


async def create_redis_client(config: RedisConfig) -> redis.Redis:
    """
    Create a Redis client.
    
    Args:
        config: Redis configuration
        
    Returns:
        redis.Redis: Async Redis client
        
    Example:
        client = await create_redis_client(config)
        await client.set("key", "value")
        value = await client.get("key")
    """
    logger.info(f"Connecting to Redis at {config.host}:{config.port}/{config.db}")
    
    client = redis.from_url(
        config.url,
        encoding="utf-8",
        decode_responses=config.decode_responses,
    )
    
    # Test connection
    await client.ping()
    
    logger.info("Redis connection established")
    return client

