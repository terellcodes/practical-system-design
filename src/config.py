"""
Application configuration and constants
"""

import logging

# Dapr component names
STATESTORE_NAME = "statestore"  # PostgreSQL
CACHE_NAME = "cache"            # Redis

# Cache TTL in seconds (1 hour)
CACHE_TTL_SECONDS = 3600

# Logging configuration
LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
LOG_LEVEL = logging.INFO


def setup_logging():
    """Configure application logging"""
    logging.basicConfig(
        level=LOG_LEVEL,
        format=LOG_FORMAT
    )

