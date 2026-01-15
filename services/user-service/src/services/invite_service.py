"""
Invite business logic service

Handles:
- Sending invites by connect_pin
- Validating invite constraints (self-invite, existing contacts)
- Accepting/rejecting invites
- Publishing real-time events via Redis pub/sub
"""

import logging
from typing import Optional, List

from fastapi import HTTPException, status

from common.models import Invite, InviteCreate, InviteUpdate, InviteStatus, InviteWithUsers
from src.repositories.invite_repository import InviteRepository
from src.repositories.contact_repository import ContactRepository
from src.repositories.sqlmodel_postgres import SQLModelPostgresRepository
from src.services.redis_publisher import get_publisher

logger = logging.getLogger(__name__)


class InviteService:
    """Service layer for invite operations"""
    
    def __init__(
        self,
        invite_repo: Optional[InviteRepository] = None,
        user_repo: Optional[SQLModelPostgresRepository] = None,
        contact_repo: Optional[ContactRepository] = None,
    ):
        self.invite_repo = invite_repo or InviteRepository()
        self.user_repo = user_repo or SQLModelPostgresRepository()
        self.contact_repo = contact_repo or ContactRepository()
    
    async def send_invite(self, invitor_id: int, invite_data: InviteCreate) -> InviteWithUsers:
        """
        Send an invite to a user by their connect_pin.
        
        Validations:
        - Connect PIN exists
        - Cannot invite yourself
        - Cannot invite existing contacts (Phase 2)
        - No existing pending invite
        """
        logger.info(f"User {invitor_id} sending invite to connect_pin {invite_data.connect_pin}")
        
        # 1. Look up user by connect_pin
        invitee = await self._get_user_by_connect_pin(invite_data.connect_pin)
        
        if not invitee:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"No user found with connect PIN '{invite_data.connect_pin}'"
            )
        
        invitee_id = invitee.id
        
        # 2. Prevent self-invite
        if invitor_id == invitee_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot send an invite to yourself"
            )
        
        # 3. Check if already contacts
        if await self.contact_repo.are_contacts(invitor_id, invitee_id):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="You are already contacts with this user"
            )
        
        # 4. Check for existing pending invite
        existing = await self.invite_repo.check_existing_invite(invitor_id, invitee_id)
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="There is already a pending invite between you and this user"
            )
        
        # 5. Create the invite
        invite = await self.invite_repo.create(invitor_id, invitee_id)
        
        # 6. Get invitor details for response
        invitor = await self.user_repo.get_by_id(invitor_id)
        
        logger.info(f"Invite {invite.id} created successfully")
        
        invite_with_users = InviteWithUsers(
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
        )
        
        # 7. Publish real-time notification to invitee
        try:
            publisher = get_publisher()
            await publisher.publish_to_user(
                user_id=str(invitee.id),  # Use numeric ID as string for WebSocket channel
                event_type="invite_received",
                data={
                    "invite_id": invite.id,
                    "invitor_id": invite.invitor_id,
                    "invitor_username": invitor.username,
                    "invitor_name": invitor.name,
                    "created_at": invite.created_at.isoformat()
                }
            )
        except Exception as e:
            # Don't fail the request if notification fails
            logger.warning(f"Failed to publish invite notification: {e}")
        
        return invite_with_users
    
    async def get_pending_invites(self, user_id: int) -> List[InviteWithUsers]:
        """Get all pending invites for a user (invites they received)."""
        logger.info(f"Fetching pending invites for user {user_id}")
        return await self.invite_repo.get_pending_for_user(user_id)
    
    async def get_sent_invites(self, user_id: int) -> List[InviteWithUsers]:
        """Get all invites sent by a user."""
        logger.info(f"Fetching sent invites for user {user_id}")
        return await self.invite_repo.get_sent_by_user(user_id)
    
    async def respond_to_invite(
        self, 
        user_id: int, 
        invite_id: int, 
        update_data: InviteUpdate
    ) -> Invite:
        """
        Accept or reject an invite.
        
        Validations:
        - Invite exists
        - User is the invitee
        - Invite is still pending
        - New status is accept or reject (not pending)
        """
        logger.info(f"User {user_id} responding to invite {invite_id} with {update_data.status}")
        
        # 1. Get the invite
        invite = await self.invite_repo.get_by_id(invite_id)
        
        if not invite:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Invite {invite_id} not found"
            )
        
        # 2. Verify user is the invitee
        if invite.invitee_id != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only respond to invites sent to you"
            )
        
        # 3. Check invite is still pending
        if invite.status != InviteStatus.PENDING.value:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invite has already been {invite.status}"
            )
        
        # 4. Validate new status
        if update_data.status == InviteStatus.PENDING:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Status must be 'accepted' or 'rejected'"
            )
        
        # 5. Update the invite status (convert enum to string value)
        new_status = update_data.status.value if isinstance(update_data.status, InviteStatus) else update_data.status
        updated_invite = await self.invite_repo.update_status(invite_id, new_status)
        
        # 6. If accepted, create contact
        if update_data.status == InviteStatus.ACCEPTED:
            await self.contact_repo.create(invite.invitor_id, invite.invitee_id)
            logger.info(f"Contact created between users {invite.invitor_id} and {invite.invitee_id}")
        
        logger.info(f"Invite {invite_id} {new_status}")
        
        # 7. Publish notification to invitor about the response
        try:
            # Get user details for the notification
            invitor = await self.user_repo.get_by_id(invite.invitor_id)
            invitee = await self.user_repo.get_by_id(invite.invitee_id)
            
            publisher = get_publisher()
            event_type = "invite_accepted" if update_data.status == InviteStatus.ACCEPTED else "invite_rejected"
            
            await publisher.publish_to_user(
                user_id=str(invite.invitor_id),  # Use numeric ID as string for WebSocket channel
                event_type=event_type,
                data={
                    "invite_id": invite.id,
                    "invitee_id": invite.invitee_id,
                    "invitee_username": invitee.username,
                    "invitee_name": invitee.name,
                    "status": new_status
                }
            )
        except Exception as e:
            # Don't fail the request if notification fails
            logger.warning(f"Failed to publish invite response notification: {e}")
        
        return updated_invite
    
    async def _get_user_by_connect_pin(self, connect_pin: str):
        """Look up a user by their connect PIN."""
        from sqlalchemy.ext.asyncio import AsyncSession
        from sqlmodel import select
        from common.models import User
        from src.database import get_async_engine
        
        engine = get_async_engine()
        
        async with AsyncSession(engine) as session:
            statement = select(User).where(User.connect_pin == connect_pin)
            result = await session.execute(statement)
            return result.scalars().first()
    

