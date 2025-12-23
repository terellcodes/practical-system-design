"""
Redis cache repository using Dapr state store
"""

import json
import logging
from typing import Optional

from dapr.clients import DaprClient

from src.config import CACHE_NAME, CACHE_TTL_SECONDS
from src.models.user import User
from src.utils import get_user_key, user_to_dict, dict_to_user

logger = logging.getLogger(__name__)


class CacheRepository:
    """Repository for Redis cache operations via Dapr"""
    
    def __init__(self, store_name: str = CACHE_NAME, ttl_seconds: int = CACHE_TTL_SECONDS):
        self.store_name = store_name
        self.ttl_seconds = ttl_seconds
    
    def get(self, user_id: int) -> Optional[User]:
        """
        Attempt to get user from Redis cache.
        Returns None if not found or on error.
        """
        try:
            with DaprClient() as client:
                key = get_user_key(user_id)
                response = client.get_state(store_name=self.store_name, key=key)
                
                if response.data:
                    data = json.loads(response.data.decode('utf-8'))
                    logger.info(f"CACHE HIT: User {user_id} found in cache")
                    return dict_to_user(data)
                
                logger.info(f"CACHE MISS: User {user_id} not in cache")
                return None
        except Exception as e:
            logger.warning(f"Cache lookup failed for user {user_id}: {e}")
            return None
    
    def set(self, user: User) -> bool:
        """
        Store user in Redis cache with TTL.
        """
        try:
            with DaprClient() as client:
                key = get_user_key(user.id)
                data = json.dumps(user_to_dict(user))
                
                client.save_state(
                    store_name=self.store_name,
                    key=key,
                    value=data,
                    state_metadata={"ttlInSeconds": str(self.ttl_seconds)}
                )
                logger.info(f"User {user.id} cached with TTL {self.ttl_seconds}s")
                return True
        except Exception as e:
            logger.warning(f"Failed to cache user {user.id}: {e}")
            return False
    
    def delete(self, user_id: int) -> bool:
        """
        Remove user from Redis cache.
        """
        try:
            with DaprClient() as client:
                key = get_user_key(user_id)
                client.delete_state(store_name=self.store_name, key=key)
                logger.info(f"User {user_id} removed from cache")
                return True
        except Exception as e:
            logger.warning(f"Failed to remove user {user_id} from cache: {e}")
            return False

