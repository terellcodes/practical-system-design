"""
Contact API endpoints
"""

from typing import List

from fastapi import APIRouter, Depends, status, Header, Query

from common.models import ContactWithUser, ContactCheckResponse
from src.repositories.contact_repository import ContactRepository

router = APIRouter(prefix="/contacts", tags=["Contacts"])


def get_contact_repository() -> ContactRepository:
    """Dependency injection for ContactRepository"""
    return ContactRepository()


@router.get("", response_model=List[ContactWithUser])
async def get_contacts(
    x_user_id: int = Header(..., description="ID of the user"),
    repo: ContactRepository = Depends(get_contact_repository)
):
    """
    Get all contacts for the current user.
    
    Returns a list of contacts with user details.
    """
    return await repo.get_contacts_for_user(x_user_id)


@router.get("/check", response_model=ContactCheckResponse)
async def check_contacts(
    user_id_1: int = Query(..., description="First user ID"),
    user_id_2: int = Query(..., description="Second user ID"),
    repo: ContactRepository = Depends(get_contact_repository)
):
    """
    Check if two users are contacts.
    
    This endpoint is used by chat-service to verify contact relationships
    before adding participants to chats.
    """
    are_contacts = await repo.are_contacts(user_id_1, user_id_2)
    
    return ContactCheckResponse(
        are_contacts=are_contacts,
        user_id_1=user_id_1,
        user_id_2=user_id_2
    )


@router.get("/check-by-username")
async def check_contacts_by_username(
    username_1: str = Query(..., description="First username"),
    username_2: str = Query(..., description="Second username"),
    repo: ContactRepository = Depends(get_contact_repository)
):
    """
    Check if two users are contacts by username.
    
    Used by chat-service which identifies users by username.
    Returns 404 if either user not found.
    """
    are_contacts = await repo.are_contacts_by_username(username_1, username_2)
    
    return {
        "are_contacts": are_contacts,
        "username_1": username_1,
        "username_2": username_2
    }

