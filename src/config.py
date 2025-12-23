"""
Application configuration and constants
"""

import os
import logging

# Dapr component names
STATESTORE_NAME = "statestore"  # PostgreSQL
CACHE_NAME = "cache"            # Redis

# Cache TTL in seconds (1 hour)
CACHE_TTL_SECONDS = 3600

# DynamoDB Configuration (LocalStack)
DYNAMODB_ENDPOINT = os.getenv("DYNAMODB_ENDPOINT", "http://localhost:4566")
AWS_REGION = os.getenv("AWS_REGION", "us-east-1")
AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID", "test")
AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY", "test")

# DynamoDB Table Names
CHATS_TABLE = "Chats"
CHAT_PARTICIPANTS_TABLE = "ChatParticipants"
PARTICIPANT_INDEX = "participantId-index"

# Environment
IS_LOCAL = os.getenv("ENV", "local") == "local"

# Logging configuration
LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
LOG_LEVEL = logging.INFO


def setup_logging():
    """Configure application logging"""
    logging.basicConfig(
        level=LOG_LEVEL,
        format=LOG_FORMAT
    )

