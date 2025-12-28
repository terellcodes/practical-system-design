"""
User business logic service

Implements Cache-Aside pattern:
- GET: Check cache first, then database, populate cache on miss
- POST/PUT: Write to database, update cache
- DELETE: Remove from database and cache
"""

import logging
from typing import Optional, List

from fastapi import HTTPException, status

from common.models import User, UserCreate, UserUpdate
from src.repositories.sqlmodel_postgres import SQLModelPostgresRepository
from src.repositories.cache import CacheRepository

logger = logging.getLogger(__name__)


class UserService:
    """Service layer for user operations with caching"""
    
    def __init__(
        self,
        postgres_repo: Optional[SQLModelPostgresRepository] = None,
        cache_repo: Optional[CacheRepository] = None
    ):
        self.postgres = postgres_repo or SQLModelPostgresRepository()
        self.cache = cache_repo or CacheRepository()
    
    async def create(self, user_data: UserCreate) -> User:
        """Create a new user (write-through pattern)."""
        logger.info(f"Creating new user: {user_data.name}")
        
        user = await self.postgres.create(
            name=user_data.name,
            email=user_data.email,
            username=user_data.name.lower().replace(" ", ""),  # Generate username from name
        )
        
        await self.cache.set(user)
        
        logger.info(f"User {user.id} created successfully")
        return user
    
    async def get_by_id(self, user_id: int) -> User:
        """Get a user by ID (cache-aside pattern)."""
        logger.info(f"Fetching user {user_id}")
        
        # Check cache first
        user = await self.cache.get(user_id)
        
        if user:
            return user
        
        # Cache miss - fetch from database
        user = await self.postgres.get_by_id(user_id)
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"User with ID {user_id} not found"
            )
        
        # Populate cache
        await self.cache.set(user)
        
        return user
    
    async def update(self, user_id: int, user_data: UserUpdate) -> User:
        """Update a user (write-through pattern)."""
        logger.info(f"Updating user {user_id}")
        
        user = await self.postgres.update(
            user_id=user_id,
            name=user_data.name,
            email=user_data.email,
        )
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"User with ID {user_id} not found"
            )
        
        await self.cache.set(user)
        
        return user
    
    async def delete(self, user_id: int) -> bool:
        """Delete a user (cache invalidation)."""
        logger.info(f"Deleting user {user_id}")
        
        deleted = await self.postgres.delete(user_id)
        
        if not deleted:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"User with ID {user_id} not found"
            )
        
        await self.cache.delete(user_id)
        
        return True
    
    async def list_all(self, limit: int = 100, offset: int = 0) -> List[User]:
        """List all users (bypasses cache)."""
        return await self.postgres.list_all(limit=limit, offset=offset)
    
    async def get_by_username(self, username: str) -> User:
        """Get a user by username."""
        logger.info(f"Fetching user by username: {username}")
        
        user = await self.postgres.get_by_username(username)
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"User with username '{username}' not found"
            )
        
        # Cache by ID for future lookups
        await self.cache.set(user)
        
        return user
    
    async def get_or_create_by_username(self, username: str) -> User:
        """Get user by username, or create if doesn't exist (for simple login)."""
        logger.info(f"Getting or creating user: {username}")
        
        try:
            # Try to get existing user
            return await self.get_by_username(username)
        except HTTPException as e:
            if e.status_code == status.HTTP_404_NOT_FOUND:
                # User doesn't exist, create new one
                logger.info(f"User '{username}' not found, creating new user")
                
                # Create user directly with username
                user = await self.postgres.create(
                    name=username,  # Use username as display name
                    email=f"{username}@example.com",  # Generate a dummy email
                    username=username
                )
                
                await self.cache.set(user)
                logger.info(f"User {user.id} created successfully")
                return user
            else:
                # Re-raise other errors
                raise
