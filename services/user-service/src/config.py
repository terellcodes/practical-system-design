"""
User Service configuration
"""

import os
import logging

from common.database import PostgresConfig, RedisConfig

# Service info
SERVICE_NAME = "user-service"
SERVICE_VERSION = "1.0.0"

# Cache TTL in seconds (1 hour)
CACHE_TTL_SECONDS = int(os.getenv("CACHE_TTL_SECONDS", "3600"))

# Database configurations (using common utilities)
POSTGRES_CONFIG = PostgresConfig.from_url(
    os.getenv("DATABASE_URL", "postgresql://dapruser:daprpassword@postgres:5432/daprdb")
)

REDIS_CONFIG = RedisConfig.from_url(
    os.getenv("REDIS_URL", "redis://redis:6379/0")
)

# Logging configuration
LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
LOG_LEVEL = logging.INFO


def setup_logging():
    """Configure application logging"""
    logging.basicConfig(
        level=LOG_LEVEL,
        format=LOG_FORMAT
    )
