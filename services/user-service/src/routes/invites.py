"""
Invite API endpoints
"""

from typing import List

from fastapi import APIRouter, Depends, status, Query, Header

from common.models import Invite, InviteCreate, InviteUpdate, InviteWithUsers
from src.services.invite_service import InviteService

router = APIRouter(prefix="/invites", tags=["Invites"])


def get_invite_service() -> InviteService:
    """Dependency injection for InviteService"""
    return InviteService()


@router.post("", response_model=InviteWithUsers, status_code=status.HTTP_201_CREATED)
async def send_invite(
    invite_data: InviteCreate,
    x_user_id: int = Header(..., description="ID of the user sending the invite"),
    service: InviteService = Depends(get_invite_service)
):
    """
    Send an invite to another user by their connect PIN.
    
    Validations:
    - Connect PIN must exist
    - Cannot invite yourself
    - Cannot invite existing contacts
    - No existing pending invite between users
    """
    return await service.send_invite(x_user_id, invite_data)


@router.get("", response_model=List[InviteWithUsers])
async def get_pending_invites(
    x_user_id: int = Header(..., description="ID of the user"),
    service: InviteService = Depends(get_invite_service)
):
    """
    Get all pending invites received by the current user.
    
    Returns invites where:
    - User is the invitee
    - Status is 'pending'
    """
    return await service.get_pending_invites(x_user_id)


@router.get("/sent", response_model=List[InviteWithUsers])
async def get_sent_invites(
    x_user_id: int = Header(..., description="ID of the user"),
    service: InviteService = Depends(get_invite_service)
):
    """
    Get all invites sent by the current user.
    """
    return await service.get_sent_invites(x_user_id)


@router.put("/{invite_id}", response_model=Invite)
async def respond_to_invite(
    invite_id: int,
    update_data: InviteUpdate,
    x_user_id: int = Header(..., description="ID of the user responding"),
    service: InviteService = Depends(get_invite_service)
):
    """
    Accept or reject an invite.
    
    Validations:
    - Invite must exist
    - User must be the invitee
    - Invite must be pending
    - Status must be 'accepted' or 'rejected' (not 'pending')
    """
    return await service.respond_to_invite(x_user_id, invite_id, update_data)

