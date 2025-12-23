"""
User CRUD API endpoints
"""

from fastapi import APIRouter, Depends, status

from src.models.user import User, UserCreate, UserUpdate, MessageResponse
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
    """
    Create a new user.
    
    Implements Write-Through pattern:
    1. Generate new user ID
    2. Save to state store (PostgreSQL)
    3. Update cache (Redis)
    """
    return service.create(user_data)


@router.get("/{user_id}", response_model=User)
async def get_user(
    user_id: int,
    service: UserService = Depends(get_user_service)
):
    """
    Get a user by ID.
    
    Implements Cache-Aside pattern:
    1. Check cache (Redis) first
    2. If cache miss, fetch from state store (PostgreSQL)
    3. Populate cache with TTL
    4. Return data
    """
    return service.get_by_id(user_id)


@router.put("/{user_id}", response_model=User)
async def update_user(
    user_id: int,
    user_data: UserUpdate,
    service: UserService = Depends(get_user_service)
):
    """
    Update an existing user.
    
    Implements Write-Through pattern with cache invalidation:
    1. Fetch existing user from state store
    2. Update fields
    3. Save to state store (PostgreSQL)
    4. Update cache (Redis)
    """
    return service.update(user_id, user_data)


@router.delete("/{user_id}", response_model=MessageResponse)
async def delete_user(
    user_id: int,
    service: UserService = Depends(get_user_service)
):
    """
    Delete a user.
    
    Implements Cache Invalidation:
    1. Verify user exists
    2. Delete from state store (PostgreSQL)
    3. Delete from cache (Redis)
    """
    service.delete(user_id)
    return MessageResponse(
        message=f"User {user_id} deleted successfully",
        user_id=user_id
    )

