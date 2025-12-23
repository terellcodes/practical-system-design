"""
PostgreSQL repository using asyncpg
"""

import logging
from typing import Optional, List

from fastapi import HTTPException, status

from common.models import User
from src.database import get_pg_pool

logger = logging.getLogger(__name__)


class PostgresRepository:
    """Repository for PostgreSQL operations"""
    
    async def create(self, name: str, email: str) -> User:
        """Create a new user in PostgreSQL."""
        pool = get_pg_pool()
        
        try:
            async with pool.acquire() as conn:
                row = await conn.fetchrow(
                    """
                    INSERT INTO users (name, email, created_at)
                    VALUES ($1, $2, NOW())
                    RETURNING id, name, email, created_at
                    """,
                    name, email
                )
                
                user = User(
                    id=row['id'],
                    name=row['name'],
                    email=row['email'],
                    created_at=row['created_at'],
                )
                
                logger.info(f"User {user.id} created in PostgreSQL")
                return user
                
        except Exception as e:
            logger.error(f"Failed to create user: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to create user: {str(e)}"
            )
    
    async def get_by_id(self, user_id: int) -> Optional[User]:
        """Get a user by ID from PostgreSQL."""
        pool = get_pg_pool()
        
        try:
            async with pool.acquire() as conn:
                row = await conn.fetchrow(
                    "SELECT id, name, email, created_at FROM users WHERE id = $1",
                    user_id
                )
                
                if row is None:
                    logger.info(f"User {user_id} not found in PostgreSQL")
                    return None
                
                logger.info(f"User {user_id} found in PostgreSQL")
                return User(
                    id=row['id'],
                    name=row['name'],
                    email=row['email'],
                    created_at=row['created_at'],
                )
                
        except Exception as e:
            logger.error(f"Failed to get user {user_id}: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to retrieve user: {str(e)}"
            )
    
    async def update(self, user_id: int, name: Optional[str], email: Optional[str]) -> Optional[User]:
        """Update a user in PostgreSQL."""
        pool = get_pg_pool()
        
        try:
            async with pool.acquire() as conn:
                updates = []
                params = []
                param_idx = 1
                
                if name is not None:
                    updates.append(f"name = ${param_idx}")
                    params.append(name)
                    param_idx += 1
                
                if email is not None:
                    updates.append(f"email = ${param_idx}")
                    params.append(email)
                    param_idx += 1
                
                if not updates:
                    return await self.get_by_id(user_id)
                
                params.append(user_id)
                query = f"""
                    UPDATE users 
                    SET {', '.join(updates)}
                    WHERE id = ${param_idx}
                    RETURNING id, name, email, created_at
                """
                
                row = await conn.fetchrow(query, *params)
                
                if row is None:
                    return None
                
                logger.info(f"User {user_id} updated in PostgreSQL")
                return User(
                    id=row['id'],
                    name=row['name'],
                    email=row['email'],
                    created_at=row['created_at'],
                )
                
        except Exception as e:
            logger.error(f"Failed to update user {user_id}: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to update user: {str(e)}"
            )
    
    async def delete(self, user_id: int) -> bool:
        """Delete a user from PostgreSQL."""
        pool = get_pg_pool()
        
        try:
            async with pool.acquire() as conn:
                result = await conn.execute(
                    "DELETE FROM users WHERE id = $1",
                    user_id
                )
                
                rows_deleted = int(result.split()[-1])
                
                if rows_deleted > 0:
                    logger.info(f"User {user_id} deleted from PostgreSQL")
                    return True
                return False
                
        except Exception as e:
            logger.error(f"Failed to delete user {user_id}: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to delete user: {str(e)}"
            )
    
    async def list_all(self, limit: int = 100, offset: int = 0) -> List[User]:
        """List all users with pagination."""
        pool = get_pg_pool()
        
        try:
            async with pool.acquire() as conn:
                rows = await conn.fetch(
                    """
                    SELECT id, name, email, created_at 
                    FROM users 
                    ORDER BY id 
                    LIMIT $1 OFFSET $2
                    """,
                    limit, offset
                )
                
                return [
                    User(
                        id=row['id'],
                        name=row['name'],
                        email=row['email'],
                        created_at=row['created_at'],
                    )
                    for row in rows
                ]
                
        except Exception as e:
            logger.error(f"Failed to list users: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to list users: {str(e)}"
            )
