"""
Invite PostgreSQL repository
"""

import logging
from datetime import datetime, timezone
from typing import Optional, List

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from common.models import Invite, InviteStatus, InviteWithUsers, User
from src.database import get_async_engine

logger = logging.getLogger(__name__)


class InviteRepository:
    """Repository for Invite PostgreSQL operations"""
    
    async def create(self, invitor_id: int, invitee_id: int) -> Invite:
        """Create a new invite in PostgreSQL."""
        engine = get_async_engine()
        
        try:
            async with AsyncSession(engine) as session:
                invite = Invite(
                    invitor_id=invitor_id,
                    invitee_id=invitee_id,
                    status=InviteStatus.PENDING.value
                )
                
                session.add(invite)
                await session.commit()
                await session.refresh(invite)
                
                logger.info(f"Invite {invite.id} created: {invitor_id} -> {invitee_id}")
                return invite
                
        except Exception as e:
            logger.error(f"Failed to create invite: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to create invite: {str(e)}"
            )
    
    async def get_by_id(self, invite_id: int) -> Optional[Invite]:
        """Get an invite by ID."""
        engine = get_async_engine()
        
        try:
            async with AsyncSession(engine) as session:
                statement = select(Invite).where(Invite.id == invite_id)
                result = await session.execute(statement)
                invite = result.scalars().first()
                
                return invite
                
        except Exception as e:
            logger.error(f"Failed to get invite {invite_id}: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to retrieve invite: {str(e)}"
            )
    
    async def get_pending_for_user(self, user_id: int) -> List[InviteWithUsers]:
        """Get all pending invites for a user (as invitee) with user details."""
        engine = get_async_engine()
        
        try:
            async with AsyncSession(engine) as session:
                # Query invites with joined user data
                statement = (
                    select(Invite)
                    .where(Invite.invitee_id == user_id)
                    .where(Invite.status == InviteStatus.PENDING.value)
                    .order_by(Invite.created_at.desc())
                )
                result = await session.execute(statement)
                invites = result.scalars().all()
                
                # Get user details for each invite
                invites_with_users = []
                for invite in invites:
                    # Get invitor
                    invitor_stmt = select(User).where(User.id == invite.invitor_id)
                    invitor_result = await session.execute(invitor_stmt)
                    invitor = invitor_result.scalars().first()
                    
                    # Get invitee
                    invitee_stmt = select(User).where(User.id == invite.invitee_id)
                    invitee_result = await session.execute(invitee_stmt)
                    invitee = invitee_result.scalars().first()
                    
                    if invitor and invitee:
                        invites_with_users.append(InviteWithUsers(
                            id=invite.id,
                            invitor_id=invite.invitor_id,
                            invitor_username=invitor.username,
                            invitor_name=invitor.name,
                            invitee_id=invite.invitee_id,
                            invitee_username=invitee.username,
                            invitee_name=invitee.name,
                            status=invite.status,
                            created_at=invite.created_at,
                            updated_at=invite.updated_at
                        ))
                
                return invites_with_users
                
        except Exception as e:
            logger.error(f"Failed to get pending invites for user {user_id}: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to retrieve invites: {str(e)}"
            )
    
    async def get_sent_by_user(self, user_id: int) -> List[InviteWithUsers]:
        """Get all invites sent by a user with user details."""
        engine = get_async_engine()
        
        try:
            async with AsyncSession(engine) as session:
                statement = (
                    select(Invite)
                    .where(Invite.invitor_id == user_id)
                    .order_by(Invite.created_at.desc())
                )
                result = await session.execute(statement)
                invites = result.scalars().all()
                
                # Get user details for each invite
                invites_with_users = []
                for invite in invites:
                    # Get invitor
                    invitor_stmt = select(User).where(User.id == invite.invitor_id)
                    invitor_result = await session.execute(invitor_stmt)
                    invitor = invitor_result.scalars().first()
                    
                    # Get invitee
                    invitee_stmt = select(User).where(User.id == invite.invitee_id)
                    invitee_result = await session.execute(invitee_stmt)
                    invitee = invitee_result.scalars().first()
                    
                    if invitor and invitee:
                        invites_with_users.append(InviteWithUsers(
                            id=invite.id,
                            invitor_id=invite.invitor_id,
                            invitor_username=invitor.username,
                            invitor_name=invitor.name,
                            invitee_id=invite.invitee_id,
                            invitee_username=invitee.username,
                            invitee_name=invitee.name,
                            status=invite.status,
                            created_at=invite.created_at,
                            updated_at=invite.updated_at
                        ))
                
                return invites_with_users
                
        except Exception as e:
            logger.error(f"Failed to get sent invites for user {user_id}: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to retrieve invites: {str(e)}"
            )
    
    async def update_status(self, invite_id: int, new_status: str) -> Optional[Invite]:
        """Update the status of an invite."""
        engine = get_async_engine()
        
        try:
            async with AsyncSession(engine) as session:
                statement = select(Invite).where(Invite.id == invite_id)
                result = await session.execute(statement)
                invite = result.scalars().first()
                
                if not invite:
                    return None
                
                invite.status = new_status
                invite.updated_at = datetime.now(timezone.utc).replace(tzinfo=None)
                
                session.add(invite)
                await session.commit()
                await session.refresh(invite)
                
                logger.info(f"Invite {invite_id} status updated to {new_status}")
                return invite
                
        except Exception as e:
            logger.error(f"Failed to update invite {invite_id}: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to update invite: {str(e)}"
            )
    
    async def check_existing_invite(self, invitor_id: int, invitee_id: int) -> Optional[Invite]:
        """Check if there's an existing pending invite between two users."""
        engine = get_async_engine()
        
        try:
            async with AsyncSession(engine) as session:
                # Check for pending invite in either direction
                statement = (
                    select(Invite)
                    .where(
                        ((Invite.invitor_id == invitor_id) & (Invite.invitee_id == invitee_id)) |
                        ((Invite.invitor_id == invitee_id) & (Invite.invitee_id == invitor_id))
                    )
                    .where(Invite.status == InviteStatus.PENDING.value)
                )
                result = await session.execute(statement)
                return result.scalars().first()
                
        except Exception as e:
            logger.error(f"Failed to check existing invite: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to check existing invite: {str(e)}"
            )

