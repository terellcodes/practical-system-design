"""
User CRUD API endpoints
"""

from typing import List

from fastapi import APIRouter, Depends, status, Query

from common.models import User, UserCreate, UserUpdate, UserLoginRequest, MessageResponse
from src.services.user_service import UserService

router = APIRouter(prefix="/users", tags=["Users"])


def get_user_service() -> UserService:
    """Dependency injection for UserService"""
    return UserService()


@router.post("", response_model=User, status_code=status.HTTP_201_CREATED)
async def create_user(
    user_data: UserCreate,
    service: UserService = Depends(get_user_service)
):
    """Create a new user."""
    return await service.create(user_data)


@router.get("", response_model=List[User])
async def list_users(
    limit: int = Query(default=100, ge=1, le=1000),
    offset: int = Query(default=0, ge=0),
    service: UserService = Depends(get_user_service)
):
    """List all users with pagination."""
    return await service.list_all(limit=limit, offset=offset)


@router.get("/{user_id}", response_model=User)
async def get_user(
    user_id: int,
    service: UserService = Depends(get_user_service)
):
    """Get a user by ID (uses cache-aside pattern)."""
    return await service.get_by_id(user_id)


@router.put("/{user_id}", response_model=User)
async def update_user(
    user_id: int,
    user_data: UserUpdate,
    service: UserService = Depends(get_user_service)
):
    """Update an existing user."""
    return await service.update(user_id, user_data)


@router.delete("/{user_id}", response_model=MessageResponse)
async def delete_user(
    user_id: int,
    service: UserService = Depends(get_user_service)
):
    """Delete a user."""
    await service.delete(user_id)
    return MessageResponse(
        message=f"User {user_id} deleted successfully",
        id=str(user_id)
    )


@router.post("/login", response_model=User, status_code=status.HTTP_200_OK)
async def login_user(
    login_request: UserLoginRequest,
    service: UserService = Depends(get_user_service)
):
    """
    Simple login - get user by username, or create if doesn't exist.
    For learning purposes only - no real authentication.
    """
    return await service.get_or_create_by_username(login_request.username)


@router.get("/username/{username}", response_model=User)
async def get_user_by_username(
    username: str,
    service: UserService = Depends(get_user_service)
):
    """Get a user by username."""
    return await service.get_by_username(username)
