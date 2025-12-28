"""
SQLModel PostgreSQL repository
"""

import logging
from typing import Optional, List
import secrets
import string

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession as SQLModelAsyncSession

from common.models import User
from src.database import get_async_engine

logger = logging.getLogger(__name__)


def generate_connect_pin() -> str:
    """Generate a unique 8-character hexadecimal connect pin"""
    return ''.join(secrets.choice('0123456789ABCDEF') for _ in range(8))


class SQLModelPostgresRepository:
    """Repository for SQLModel PostgreSQL operations"""
    
    async def create(self, name: str, email: str, username: str) -> User:
        """Create a new user in PostgreSQL."""
        engine = get_async_engine()
        
        try:
            async with AsyncSession(engine) as session:
                # Check if username already exists
                statement = select(User).where(User.username == username)
                result = await session.execute(statement)
                existing = result.scalars().first()
                if existing:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"Username '{username}' already exists"
                    )
                
                # Generate unique connect_pin
                connect_pin = generate_connect_pin()
                while True:
                    pin_statement = select(User).where(User.connect_pin == connect_pin)
                    pin_result = await session.execute(pin_statement)
                    existing_pin = pin_result.scalars().first()
                    if not existing_pin:
                        break
                    connect_pin = generate_connect_pin()
                
                # Create new user
                user = User(
                    name=name,
                    email=email,
                    username=username,
                    connect_pin=connect_pin
                )
                
                session.add(user)
                await session.commit()
                await session.refresh(user)
                
                logger.info(f"User {user.id} created in PostgreSQL")
                return user
                
        except IntegrityError as e:
            logger.error(f"Failed to create user due to constraint violation: {e}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"User with username '{username}' already exists"
            )
        except Exception as e:
            logger.error(f"Failed to create user: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to create user: {str(e)}"
            )
    
    async def get_by_id(self, user_id: int) -> Optional[User]:
        """Get a user by ID from PostgreSQL."""
        engine = get_async_engine()
        
        try:
            async with AsyncSession(engine) as session:
                statement = select(User).where(User.id == user_id)
                result = await session.execute(statement)
                user = result.scalars().first()
                
                if not user:
                    logger.info(f"User {user_id} not found in PostgreSQL")
                    return None
                
                logger.info(f"User {user_id} found in PostgreSQL")
                return user
                
        except Exception as e:
            logger.error(f"Failed to get user {user_id}: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to retrieve user: {str(e)}"
            )
    
    async def get_by_username(self, username: str) -> Optional[User]:
        """Get a user by username from PostgreSQL."""
        engine = get_async_engine()
        
        try:
            async with AsyncSession(engine) as session:
                statement = select(User).where(User.username == username)
                result = await session.execute(statement)
                user = result.scalars().first()
                
                if not user:
                    logger.info(f"User '{username}' not found in PostgreSQL")
                    return None
                
                logger.info(f"User '{username}' found in PostgreSQL")
                return user
                
        except Exception as e:
            logger.error(f"Failed to get user by username '{username}': {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to retrieve user: {str(e)}"
            )
    
    async def update(self, user_id: int, name: Optional[str], email: Optional[str]) -> Optional[User]:
        """Update a user in PostgreSQL."""
        engine = get_async_engine()
        
        try:
            async with AsyncSession(engine) as session:
                statement = select(User).where(User.id == user_id)
                result = await session.execute(statement)
                user = result.scalars().first()
                
                if not user:
                    return None
                
                # Update fields
                if name is not None:
                    user.name = name
                if email is not None:
                    user.email = email
                
                session.add(user)
                await session.commit()
                await session.refresh(user)
                
                logger.info(f"User {user_id} updated in PostgreSQL")
                return user
                
        except Exception as e:
            logger.error(f"Failed to update user {user_id}: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to update user: {str(e)}"
            )
    
    async def delete(self, user_id: int) -> bool:
        """Delete a user from PostgreSQL."""
        engine = get_async_engine()
        
        try:
            async with AsyncSession(engine) as session:
                statement = select(User).where(User.id == user_id)
                result = await session.execute(statement)
                user = result.scalars().first()
                
                if not user:
                    return False
                
                await session.delete(user)
                await session.commit()
                
                logger.info(f"User {user_id} deleted from PostgreSQL")
                return True
                
        except Exception as e:
            logger.error(f"Failed to delete user {user_id}: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to delete user: {str(e)}"
            )
    
    async def list_all(self, limit: int = 100, offset: int = 0) -> List[User]:
        """List all users with pagination."""
        engine = get_async_engine()
        
        try:
            async with AsyncSession(engine) as session:
                statement = select(User).order_by(User.id).offset(offset).limit(limit)
                result = await session.execute(statement)
                users = result.scalars().all()
                
                return users
                
        except Exception as e:
            logger.error(f"Failed to list users: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to list users: {str(e)}"
            )