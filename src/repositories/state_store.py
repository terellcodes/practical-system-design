"""
PostgreSQL state store repository using Dapr
"""

import json
import logging
from typing import Optional

from fastapi import HTTPException, status
from dapr.clients import DaprClient

from src.config import STATESTORE_NAME
from src.models.user import User
from src.utils import get_user_key, get_next_id_key, user_to_dict, dict_to_user

logger = logging.getLogger(__name__)


class StateStoreRepository:
    """Repository for PostgreSQL state store operations via Dapr"""
    
    def __init__(self, store_name: str = STATESTORE_NAME):
        self.store_name = store_name
    
    def get(self, user_id: int) -> Optional[User]:
        """
        Get user from PostgreSQL state store.
        """
        try:
            with DaprClient() as client:
                key = get_user_key(user_id)
                response = client.get_state(store_name=self.store_name, key=key)
                
                if response.data:
                    data = json.loads(response.data.decode('utf-8'))
                    logger.info(f"User {user_id} found in state store")
                    return dict_to_user(data)
                
                logger.info(f"User {user_id} not found in state store")
                return None
        except Exception as e:
            logger.error(f"State store lookup failed for user {user_id}: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to retrieve user: {str(e)}"
            )
    
    def save(self, user: User) -> bool:
        """
        Save user to PostgreSQL state store.
        """
        try:
            with DaprClient() as client:
                key = get_user_key(user.id)
                data = json.dumps(user_to_dict(user))
                
                client.save_state(store_name=self.store_name, key=key, value=data)
                logger.info(f"User {user.id} saved to state store")
                return True
        except Exception as e:
            logger.error(f"Failed to save user {user.id} to state store: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to save user: {str(e)}"
            )
    
    def delete(self, user_id: int) -> bool:
        """
        Delete user from PostgreSQL state store.
        """
        try:
            with DaprClient() as client:
                key = get_user_key(user_id)
                client.delete_state(store_name=self.store_name, key=key)
                logger.info(f"User {user_id} deleted from state store")
                return True
        except Exception as e:
            logger.error(f"Failed to delete user {user_id} from state store: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to delete user: {str(e)}"
            )
    
    def get_next_id(self) -> int:
        """
        Get and increment the next available user ID.
        Uses the state store to maintain a counter.
        """
        try:
            with DaprClient() as client:
                key = get_next_id_key()
                
                # Get current ID
                response = client.get_state(store_name=self.store_name, key=key)
                
                if response.data:
                    next_id = int(response.data.decode('utf-8'))
                else:
                    next_id = 1
                
                # Increment and save
                client.save_state(
                    store_name=self.store_name,
                    key=key,
                    value=str(next_id + 1)
                )
                
                return next_id
        except Exception as e:
            logger.error(f"Failed to get next user ID: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to generate user ID: {str(e)}"
            )

