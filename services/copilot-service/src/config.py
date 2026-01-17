"""
Copilot Service configuration
"""

import os
import logging

# Service info
SERVICE_NAME = "copilot-service"
SERVICE_VERSION = "1.0.0"

# LLM Configuration
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
ANTHROPIC_MODEL = os.getenv("ANTHROPIC_MODEL", "claude-sonnet-4-20250514")

# Database URL for LangGraph checkpoint persistence
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://dapruser:daprpassword@postgres:5432/daprdb"
)

# Service URLs
USER_SERVICE_URL = os.getenv("USER_SERVICE_URL", "http://user-service:8001")
CHAT_SERVICE_URL = os.getenv("CHAT_SERVICE_URL", "http://chat-service:8002")
CHAT_SERVICE_WS_URL = os.getenv("CHAT_SERVICE_WS_URL", "ws://chat-service:8002")

# Redis URL (for publishing messages)
REDIS_URL = os.getenv("REDIS_URL", "redis://redis:6379/0")

# Logging configuration
LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
LOG_LEVEL = logging.INFO


def setup_logging():
    """Configure application logging"""
    logging.basicConfig(
        level=LOG_LEVEL,
        format=LOG_FORMAT
    )
