"""
User business logic service

Implements caching patterns:
- Cache-Aside for reads
- Write-Through for writes
- Cache Invalidation for deletes
"""

import logging
from datetime import datetime
from typing import Optional

from fastapi import HTTPException, status

from src.models.user import User, UserCreate, UserUpdate
from src.repositories.cache import CacheRepository
from src.repositories.state_store import StateStoreRepository

logger = logging.getLogger(__name__)


class UserService:
    """Service layer for user operations with caching patterns"""
    
    def __init__(
        self,
        state_store: Optional[StateStoreRepository] = None,
        cache: Optional[CacheRepository] = None
    ):
        self.state_store = state_store or StateStoreRepository()
        self.cache = cache or CacheRepository()
    
    def create(self, user_data: UserCreate) -> User:
        """
        Create a new user.
        
        Implements Write-Through pattern:
        1. Generate new user ID
        2. Save to state store (PostgreSQL)
        3. Update cache (Redis)
        """
        logger.info(f"Creating new user: {user_data.name}")
        
        # Generate new user ID
        user_id = self.state_store.get_next_id()
        
        # Create user object
        user = User(
            id=user_id,
            name=user_data.name,
            email=user_data.email,
            created_at=datetime.now()
        )
        
        # Write-Through: Save to state store first
        self.state_store.save(user)
        
        # Then update cache
        self.cache.set(user)
        
        logger.info(f"User {user_id} created successfully")
        return user
    
    def get_by_id(self, user_id: int) -> User:
        """
        Get a user by ID.
        
        Implements Cache-Aside pattern:
        1. Check cache (Redis) first
        2. If cache miss, fetch from state store (PostgreSQL)
        3. Populate cache with TTL
        4. Return data
        """
        logger.info(f"Fetching user {user_id}")
        
        # Step 1: Check cache first
        user = self.cache.get(user_id)
        
        if user:
            # Cache hit - return immediately
            return user
        
        # Step 2: Cache miss - fetch from state store
        user = self.state_store.get(user_id)
        
        if not user:
            logger.warning(f"User {user_id} not found")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"User with ID {user_id} not found"
            )
        
        # Step 3: Populate cache for future requests
        self.cache.set(user)
        
        return user
    
    def update(self, user_id: int, user_data: UserUpdate) -> User:
        """
        Update an existing user.
        
        Implements Write-Through pattern with cache invalidation:
        1. Fetch existing user from state store
        2. Update fields
        3. Save to state store (PostgreSQL)
        4. Update cache (Redis)
        """
        logger.info(f"Updating user {user_id}")
        
        # Get existing user from state store
        existing_user = self.state_store.get(user_id)
        
        if not existing_user:
            logger.warning(f"User {user_id} not found for update")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"User with ID {user_id} not found"
            )
        
        # Update fields if provided
        updated_name = user_data.name if user_data.name is not None else existing_user.name
        updated_email = user_data.email if user_data.email is not None else existing_user.email
        
        # Create updated user object
        updated_user = User(
            id=existing_user.id,
            name=updated_name,
            email=updated_email,
            created_at=existing_user.created_at
        )
        
        # Write-Through: Save to state store
        self.state_store.save(updated_user)
        
        # Update cache with new data
        self.cache.set(updated_user)
        
        logger.info(f"User {user_id} updated successfully")
        return updated_user
    
    def delete(self, user_id: int) -> bool:
        """
        Delete a user.
        
        Implements Cache Invalidation:
        1. Verify user exists
        2. Delete from state store (PostgreSQL)
        3. Delete from cache (Redis)
        """
        logger.info(f"Deleting user {user_id}")
        
        # Verify user exists
        existing_user = self.state_store.get(user_id)
        
        if not existing_user:
            logger.warning(f"User {user_id} not found for deletion")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"User with ID {user_id} not found"
            )
        
        # Delete from state store
        self.state_store.delete(user_id)
        
        # Delete from cache
        self.cache.delete(user_id)
        
        logger.info(f"User {user_id} deleted successfully")
        return True

