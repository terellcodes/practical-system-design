"""
Chat Service configuration
"""

import os
import logging

from common.database import DynamoDBConfig

# Service info
SERVICE_NAME = "chat-service"
SERVICE_VERSION = "1.0.0"

# Table names
CHATS_TABLE = os.getenv("CHATS_TABLE", "Chats")
CHAT_PARTICIPANTS_TABLE = os.getenv("CHAT_PARTICIPANTS_TABLE", "ChatParticipants")
MESSAGES_TABLE = os.getenv("MESSAGES_TABLE", "Messages")
INBOX_TABLE = os.getenv("INBOX_TABLE", "Inbox")
PARTICIPANT_INDEX = "participantId-index"

# DynamoDB configuration (using common utilities)
DYNAMODB_CONFIG = DynamoDBConfig(
    region=os.getenv("AWS_REGION", "us-east-1"),
    endpoint_url=os.getenv("DYNAMODB_ENDPOINT", "http://localstack:4566") if os.getenv("IS_LOCAL", "true").lower() == "true" else None,
    access_key_id=os.getenv("AWS_ACCESS_KEY_ID", "test"),
    secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY", "test"),
)

# Redis configuration (for WebSocket pub/sub)
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
