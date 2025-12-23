"""
Redis cache repository
"""

import json
import logging
from typing import Optional

from common.models import User
from src.database import get_redis_client
from src.config import CACHE_TTL_SECONDS

logger = logging.getLogger(__name__)


def _user_cache_key(user_id: int) -> str:
    """Generate cache key for a user"""
    return f"user:{user_id}"


class CacheRepository:
    """Repository for Redis cache operations"""
    
    def __init__(self, ttl_seconds: int = CACHE_TTL_SECONDS):
        self.ttl_seconds = ttl_seconds
    
    async def get(self, user_id: int) -> Optional[User]:
        """Get user from Redis cache."""
        try:
            redis = get_redis_client()
            key = _user_cache_key(user_id)
            
            data = await redis.get(key)
            
            if data is None:
                logger.info(f"CACHE MISS: User {user_id} not in cache")
                return None
            
            user_dict = json.loads(data)
            logger.info(f"CACHE HIT: User {user_id} found in cache")
            
            return User(
                id=user_dict['id'],
                name=user_dict['name'],
                email=user_dict['email'],
                created_at=user_dict['created_at'],
            )
            
        except Exception as e:
            logger.warning(f"Cache lookup failed for user {user_id}: {e}")
            return None
    
    async def set(self, user: User) -> bool:
        """Store user in Redis cache with TTL."""
        try:
            redis = get_redis_client()
            key = _user_cache_key(user.id)
            
            user_dict = {
                'id': user.id,
                'name': user.name,
                'email': user.email,
                'created_at': user.created_at.isoformat(),
            }
            data = json.dumps(user_dict)
            
            await redis.setex(key, self.ttl_seconds, data)
            
            logger.info(f"User {user.id} cached with TTL {self.ttl_seconds}s")
            return True
            
        except Exception as e:
            logger.warning(f"Failed to cache user {user.id}: {e}")
            return False
    
    async def delete(self, user_id: int) -> bool:
        """Remove user from Redis cache."""
        try:
            redis = get_redis_client()
            key = _user_cache_key(user_id)
            await redis.delete(key)
            logger.info(f"User {user_id} removed from cache")
            return True
        except Exception as e:
            logger.warning(f"Failed to remove user {user_id} from cache: {e}")
            return False
