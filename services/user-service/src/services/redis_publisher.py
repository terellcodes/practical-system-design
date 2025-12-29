"""
Redis Publisher for User Service Events

Publishes events to Redis pub/sub for real-time delivery via WebSocket.
The chat-service subscribes to these channels and forwards to connected users.
"""

import json
import logging
from typing import Optional

import redis.asyncio as aioredis

from common.database import RedisConfig

logger = logging.getLogger(__name__)


class RedisPublisher:
    """
    Publishes events to Redis pub/sub channels.
    
    Channel naming:
        - user:{user_id} - Personal channel for user-specific notifications
    """
    
    def __init__(self, config: RedisConfig):
        self.config = config
        self.client: Optional[aioredis.Redis] = None
    
    async def initialize(self):
        """Initialize Redis connection."""
        self.client = await aioredis.from_url(
            self.config.url,
            encoding="utf-8",
            decode_responses=True
        )
        logger.info(f"Redis publisher initialized: {self.config.host}:{self.config.port}")
    
    async def close(self):
        """Close Redis connection."""
        if self.client:
            await self.client.close()
            logger.info("Redis publisher closed")
    
    async def publish_to_user(self, user_id: str, event_type: str, data: dict) -> bool:
        """
        Publish an event to a user's personal channel.
        
        Args:
            user_id: The user to send the event to
            event_type: Type of event (e.g., "invite_received", "invite_accepted")
            data: Event payload
            
        Returns:
            True if published successfully, False otherwise
        """
        if not self.client:
            logger.error("Redis client not initialized")
            return False
        
        channel = f"user:{user_id}"
        message = json.dumps({
            "type": event_type,
            "data": data
        })
        
        try:
            await self.client.publish(channel, message)
            logger.info(f"Published {event_type} to channel {channel}")
            return True
        except Exception as e:
            logger.error(f"Failed to publish to {channel}: {e}")
            return False


# Global instance (initialized in main.py)
publisher: Optional[RedisPublisher] = None


def get_publisher() -> RedisPublisher:
    """Get the global Redis publisher instance."""
    if publisher is None:
        raise RuntimeError("Redis publisher not initialized")
    return publisher

