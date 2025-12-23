"""
PostgreSQL connection utilities

Usage:
    from common.database import create_postgres_pool, PostgresConfig
    
    config = PostgresConfig(
        host="postgres",
        port=5432,
        user="myuser",
        password="mypassword",
        database="mydb",
    )
    pool = await create_postgres_pool(config)
"""

import logging
from dataclasses import dataclass
from typing import Optional

import asyncpg

logger = logging.getLogger(__name__)


@dataclass
class PostgresConfig:
    """PostgreSQL connection configuration"""
    host: str = "localhost"
    port: int = 5432
    user: str = "postgres"
    password: str = "postgres"
    database: str = "postgres"
    min_connections: int = 5
    max_connections: int = 20
    command_timeout: int = 60
    
    @property
    def dsn(self) -> str:
        """Return connection string"""
        return f"postgresql://{self.user}:{self.password}@{self.host}:{self.port}/{self.database}"
    
    @classmethod
    def from_url(cls, url: str) -> "PostgresConfig":
        """
        Create config from DATABASE_URL.
        Format: postgresql://user:password@host:port/database
        """
        # Simple parsing - in production use urllib.parse
        url = url.replace("postgresql://", "")
        user_pass, host_db = url.split("@")
        user, password = user_pass.split(":")
        host_port, database = host_db.split("/")
        
        if ":" in host_port:
            host, port = host_port.split(":")
            port = int(port)
        else:
            host = host_port
            port = 5432
        
        return cls(
            host=host,
            port=port,
            user=user,
            password=password,
            database=database,
        )


async def create_postgres_pool(config: PostgresConfig) -> asyncpg.Pool:
    """
    Create a PostgreSQL connection pool.
    
    Args:
        config: PostgreSQL configuration
        
    Returns:
        asyncpg.Pool: Connection pool
        
    Example:
        pool = await create_postgres_pool(config)
        async with pool.acquire() as conn:
            result = await conn.fetch("SELECT * FROM users")
    """
    logger.info(f"Connecting to PostgreSQL at {config.host}:{config.port}/{config.database}")
    
    pool = await asyncpg.create_pool(
        config.dsn,
        min_size=config.min_connections,
        max_size=config.max_connections,
        command_timeout=config.command_timeout,
    )
    
    logger.info("PostgreSQL connection pool created")
    return pool

