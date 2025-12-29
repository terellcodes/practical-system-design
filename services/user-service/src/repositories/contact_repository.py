"""
Contact PostgreSQL repository

Uses unidirectional design: contact_one_id is always min(user_a, user_b)
to ensure a single row represents the relationship between two users.
"""

import logging
from typing import Optional, List

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from sqlmodel import select

from common.models import Contact, ContactWithUser, User
from src.database import get_async_engine

logger = logging.getLogger(__name__)


class ContactRepository:
    """Repository for Contact PostgreSQL operations"""
    
    async def create(self, user_id_1: int, user_id_2: int) -> Contact:
        """
        Create a contact between two users.
        
        Automatically orders IDs so contact_one_id < contact_two_id.
        """
        engine = get_async_engine()
        
        # Ensure contact_one_id is always the smaller ID
        contact_one_id = min(user_id_1, user_id_2)
        contact_two_id = max(user_id_1, user_id_2)
        
        try:
            async with AsyncSession(engine) as session:
                contact = Contact(
                    contact_one_id=contact_one_id,
                    contact_two_id=contact_two_id
                )
                
                session.add(contact)
                await session.commit()
                await session.refresh(contact)
                
                logger.info(f"Contact created between users {contact_one_id} and {contact_two_id}")
                return contact
                
        except Exception as e:
            logger.error(f"Failed to create contact: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to create contact: {str(e)}"
            )
    
    async def get_contacts_for_user(self, user_id: int) -> List[ContactWithUser]:
        """
        Get all contacts for a user with user details.
        
        Uses UNION query to efficiently find contacts where user is either
        contact_one_id or contact_two_id.
        """
        engine = get_async_engine()
        
        try:
            async with AsyncSession(engine) as session:
                # Use raw SQL for the UNION query (more efficient)
                query = text("""
                    SELECT c.id, c.contact_two_id as contact_id, u.username, u.name, c.created_at
                    FROM contacts c
                    JOIN users u ON u.id = c.contact_two_id
                    WHERE c.contact_one_id = :user_id
                    UNION ALL
                    SELECT c.id, c.contact_one_id as contact_id, u.username, u.name, c.created_at
                    FROM contacts c
                    JOIN users u ON u.id = c.contact_one_id
                    WHERE c.contact_two_id = :user_id
                    ORDER BY created_at DESC
                """)
                
                result = await session.execute(query, {"user_id": user_id})
                rows = result.fetchall()
                
                contacts = [
                    ContactWithUser(
                        id=row[0],
                        contact_id=row[1],
                        contact_username=row[2],
                        contact_name=row[3],
                        created_at=row[4]
                    )
                    for row in rows
                ]
                
                return contacts
                
        except Exception as e:
            logger.error(f"Failed to get contacts for user {user_id}: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to retrieve contacts: {str(e)}"
            )
    
    async def are_contacts(self, user_id_1: int, user_id_2: int) -> bool:
        """
        Check if two users are contacts.
        
        Uses ordered IDs for direct lookup.
        """
        engine = get_async_engine()
        
        # Order IDs for lookup
        contact_one_id = min(user_id_1, user_id_2)
        contact_two_id = max(user_id_1, user_id_2)
        
        try:
            async with AsyncSession(engine) as session:
                statement = (
                    select(Contact)
                    .where(Contact.contact_one_id == contact_one_id)
                    .where(Contact.contact_two_id == contact_two_id)
                )
                result = await session.execute(statement)
                contact = result.scalars().first()
                
                return contact is not None
                
        except Exception as e:
            logger.error(f"Failed to check contact status: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to check contact status: {str(e)}"
            )
    
    async def delete(self, user_id_1: int, user_id_2: int) -> bool:
        """Delete a contact between two users."""
        engine = get_async_engine()
        
        # Order IDs for lookup
        contact_one_id = min(user_id_1, user_id_2)
        contact_two_id = max(user_id_1, user_id_2)
        
        try:
            async with AsyncSession(engine) as session:
                statement = (
                    select(Contact)
                    .where(Contact.contact_one_id == contact_one_id)
                    .where(Contact.contact_two_id == contact_two_id)
                )
                result = await session.execute(statement)
                contact = result.scalars().first()
                
                if not contact:
                    return False
                
                await session.delete(contact)
                await session.commit()
                
                logger.info(f"Contact deleted between users {contact_one_id} and {contact_two_id}")
                return True
                
        except Exception as e:
            logger.error(f"Failed to delete contact: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to delete contact: {str(e)}"
            )

