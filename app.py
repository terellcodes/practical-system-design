"""
FastAPI Application with Dapr State Management
Implements Cache-Aside and Write-Through patterns for User CRUD operations
"""

import logging
import json
from datetime import datetime
from typing import Optional

from fastapi import FastAPI, HTTPException, status
from pydantic import BaseModel, EmailStr, Field
from dapr.clients import DaprClient

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# FastAPI app initialization
app = FastAPI(
    title="User Service",
    description="A distributed user management service using Dapr for state management",
    version="1.0.0"
)

# Dapr component names
STATESTORE_NAME = "statestore"  # PostgreSQL
CACHE_NAME = "cache"            # Redis

# Cache TTL in seconds (1 hour)
CACHE_TTL_SECONDS = 3600


# ============================================================================
# Pydantic Models
# ============================================================================

class UserCreate(BaseModel):
    """Request model for creating a user"""
    name: str = Field(..., min_length=1, max_length=100, description="User's full name")
    email: str = Field(..., description="User's email address")

    class Config:
        json_schema_extra = {
            "example": {
                "name": "John Doe",
                "email": "john.doe@example.com"
            }
        }


class UserUpdate(BaseModel):
    """Request model for updating a user"""
    name: Optional[str] = Field(None, min_length=1, max_length=100, description="User's full name")
    email: Optional[str] = Field(None, description="User's email address")

    class Config:
        json_schema_extra = {
            "example": {
                "name": "Jane Doe",
                "email": "jane.doe@example.com"
            }
        }


class User(BaseModel):
    """Response model for a user"""
    id: int = Field(..., description="User's unique identifier")
    name: str = Field(..., description="User's full name")
    email: str = Field(..., description="User's email address")
    created_at: datetime = Field(..., description="Timestamp when user was created")

    class Config:
        json_schema_extra = {
            "example": {
                "id": 1,
                "name": "John Doe",
                "email": "john.doe@example.com",
                "created_at": "2024-01-15T10:30:00"
            }
        }


class HealthResponse(BaseModel):
    """Response model for health check"""
    status: str
    service: str
    timestamp: datetime


class MessageResponse(BaseModel):
    """Generic message response"""
    message: str
    user_id: Optional[int] = None


# ============================================================================
# Helper Functions
# ============================================================================

def get_user_key(user_id: int) -> str:
    """Generate a consistent key for user storage"""
    return f"user-{user_id}"


def get_next_id_key() -> str:
    """Key for storing the next available user ID"""
    return "next-user-id"


def user_to_dict(user: User) -> dict:
    """Convert User model to dictionary for storage"""
    return {
        "id": user.id,
        "name": user.name,
        "email": user.email,
        "created_at": user.created_at.isoformat()
    }


def dict_to_user(data: dict) -> User:
    """Convert dictionary to User model"""
    return User(
        id=data["id"],
        name=data["name"],
        email=data["email"],
        created_at=datetime.fromisoformat(data["created_at"])
    )


# ============================================================================
# State Management Functions
# ============================================================================

def get_from_cache(user_id: int) -> Optional[User]:
    """
    Attempt to get user from Redis cache
    Returns None if not found or on error
    """
    try:
        with DaprClient() as client:
            key = get_user_key(user_id)
            response = client.get_state(store_name=CACHE_NAME, key=key)
            
            if response.data:
                data = json.loads(response.data.decode('utf-8'))
                logger.info(f"CACHE HIT: User {user_id} found in cache")
                return dict_to_user(data)
            
            logger.info(f"CACHE MISS: User {user_id} not in cache")
            return None
    except Exception as e:
        logger.warning(f"Cache lookup failed for user {user_id}: {e}")
        return None


def set_in_cache(user: User) -> bool:
    """
    Store user in Redis cache with TTL
    """
    try:
        with DaprClient() as client:
            key = get_user_key(user.id)
            data = json.dumps(user_to_dict(user))
            
            # Set state with TTL metadata
            client.save_state(
                store_name=CACHE_NAME,
                key=key,
                value=data,
                state_metadata={"ttlInSeconds": str(CACHE_TTL_SECONDS)}
            )
            logger.info(f"User {user.id} cached with TTL {CACHE_TTL_SECONDS}s")
            return True
    except Exception as e:
        logger.warning(f"Failed to cache user {user.id}: {e}")
        return False


def delete_from_cache(user_id: int) -> bool:
    """
    Remove user from Redis cache
    """
    try:
        with DaprClient() as client:
            key = get_user_key(user_id)
            client.delete_state(store_name=CACHE_NAME, key=key)
            logger.info(f"User {user_id} removed from cache")
            return True
    except Exception as e:
        logger.warning(f"Failed to remove user {user_id} from cache: {e}")
        return False


def get_from_statestore(user_id: int) -> Optional[User]:
    """
    Get user from PostgreSQL state store
    """
    try:
        with DaprClient() as client:
            key = get_user_key(user_id)
            response = client.get_state(store_name=STATESTORE_NAME, key=key)
            
            if response.data:
                data = json.loads(response.data.decode('utf-8'))
                logger.info(f"User {user_id} found in state store")
                return dict_to_user(data)
            
            logger.info(f"User {user_id} not found in state store")
            return None
    except Exception as e:
        logger.error(f"State store lookup failed for user {user_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve user: {str(e)}"
        )


def save_to_statestore(user: User) -> bool:
    """
    Save user to PostgreSQL state store
    """
    try:
        with DaprClient() as client:
            key = get_user_key(user.id)
            data = json.dumps(user_to_dict(user))
            
            client.save_state(store_name=STATESTORE_NAME, key=key, value=data)
            logger.info(f"User {user.id} saved to state store")
            return True
    except Exception as e:
        logger.error(f"Failed to save user {user.id} to state store: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to save user: {str(e)}"
        )


def delete_from_statestore(user_id: int) -> bool:
    """
    Delete user from PostgreSQL state store
    """
    try:
        with DaprClient() as client:
            key = get_user_key(user_id)
            client.delete_state(store_name=STATESTORE_NAME, key=key)
            logger.info(f"User {user_id} deleted from state store")
            return True
    except Exception as e:
        logger.error(f"Failed to delete user {user_id} from state store: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete user: {str(e)}"
        )


def get_next_user_id() -> int:
    """
    Get and increment the next available user ID
    Uses the state store to maintain a counter
    """
    try:
        with DaprClient() as client:
            key = get_next_id_key()
            
            # Get current ID
            response = client.get_state(store_name=STATESTORE_NAME, key=key)
            
            if response.data:
                next_id = int(response.data.decode('utf-8'))
            else:
                next_id = 1
            
            # Increment and save
            client.save_state(
                store_name=STATESTORE_NAME,
                key=key,
                value=str(next_id + 1)
            )
            
            return next_id
    except Exception as e:
        logger.error(f"Failed to get next user ID: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate user ID: {str(e)}"
        )


# ============================================================================
# API Endpoints
# ============================================================================

@app.get("/health", response_model=HealthResponse, tags=["Health"])
async def health_check():
    """
    Health check endpoint to verify service is running
    """
    return HealthResponse(
        status="healthy",
        service="user-service",
        timestamp=datetime.now()
    )


@app.post("/users", response_model=User, status_code=status.HTTP_201_CREATED, tags=["Users"])
async def create_user(user_data: UserCreate):
    """
    Create a new user
    
    Implements Write-Through pattern:
    1. Generate new user ID
    2. Save to state store (PostgreSQL)
    3. Update cache (Redis)
    """
    logger.info(f"Creating new user: {user_data.name}")
    
    # Generate new user ID
    user_id = get_next_user_id()
    
    # Create user object
    user = User(
        id=user_id,
        name=user_data.name,
        email=user_data.email,
        created_at=datetime.now()
    )
    
    # Write-Through: Save to state store first
    save_to_statestore(user)
    
    # Then update cache
    set_in_cache(user)
    
    logger.info(f"User {user_id} created successfully")
    return user


@app.get("/users/{user_id}", response_model=User, tags=["Users"])
async def get_user(user_id: int):
    """
    Get a user by ID
    
    Implements Cache-Aside pattern:
    1. Check cache (Redis) first
    2. If cache miss, fetch from state store (PostgreSQL)
    3. Populate cache with TTL
    4. Return data
    """
    logger.info(f"Fetching user {user_id}")
    
    # Step 1: Check cache first
    user = get_from_cache(user_id)
    
    if user:
        # Cache hit - return immediately
        return user
    
    # Step 2: Cache miss - fetch from state store
    user = get_from_statestore(user_id)
    
    if not user:
        logger.warning(f"User {user_id} not found")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with ID {user_id} not found"
        )
    
    # Step 3: Populate cache for future requests
    set_in_cache(user)
    
    return user


@app.put("/users/{user_id}", response_model=User, tags=["Users"])
async def update_user(user_id: int, user_data: UserUpdate):
    """
    Update an existing user
    
    Implements Write-Through pattern with cache invalidation:
    1. Fetch existing user from state store
    2. Update fields
    3. Save to state store (PostgreSQL)
    4. Update cache (Redis)
    """
    logger.info(f"Updating user {user_id}")
    
    # Get existing user from state store
    existing_user = get_from_statestore(user_id)
    
    if not existing_user:
        logger.warning(f"User {user_id} not found for update")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with ID {user_id} not found"
        )
    
    # Update fields if provided
    updated_name = user_data.name if user_data.name is not None else existing_user.name
    updated_email = user_data.email if user_data.email is not None else existing_user.email
    
    # Create updated user object
    updated_user = User(
        id=existing_user.id,
        name=updated_name,
        email=updated_email,
        created_at=existing_user.created_at
    )
    
    # Write-Through: Save to state store
    save_to_statestore(updated_user)
    
    # Update cache with new data
    set_in_cache(updated_user)
    
    logger.info(f"User {user_id} updated successfully")
    return updated_user


@app.delete("/users/{user_id}", response_model=MessageResponse, tags=["Users"])
async def delete_user(user_id: int):
    """
    Delete a user
    
    Implements Cache Invalidation:
    1. Verify user exists
    2. Delete from state store (PostgreSQL)
    3. Delete from cache (Redis)
    """
    logger.info(f"Deleting user {user_id}")
    
    # Verify user exists
    existing_user = get_from_statestore(user_id)
    
    if not existing_user:
        logger.warning(f"User {user_id} not found for deletion")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with ID {user_id} not found"
        )
    
    # Delete from state store
    delete_from_statestore(user_id)
    
    # Delete from cache
    delete_from_cache(user_id)
    
    logger.info(f"User {user_id} deleted successfully")
    return MessageResponse(
        message=f"User {user_id} deleted successfully",
        user_id=user_id
    )


# ============================================================================
# Application Startup/Shutdown Events
# ============================================================================

@app.on_event("startup")
async def startup_event():
    """Log application startup"""
    logger.info("=" * 50)
    logger.info("User Service starting up...")
    logger.info(f"State Store: {STATESTORE_NAME} (PostgreSQL)")
    logger.info(f"Cache: {CACHE_NAME} (Redis)")
    logger.info(f"Cache TTL: {CACHE_TTL_SECONDS} seconds")
    logger.info("=" * 50)


@app.on_event("shutdown")
async def shutdown_event():
    """Log application shutdown"""
    logger.info("User Service shutting down...")


# ============================================================================
# Main Entry Point
# ============================================================================

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)

