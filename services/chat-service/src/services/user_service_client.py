"""
HTTP client for user-service API calls

Used to verify contact relationships before adding participants to chats.
"""

import logging
import os
from typing import Optional

import httpx

logger = logging.getLogger(__name__)

# User service URL (internal Docker network)
USER_SERVICE_URL = os.getenv("USER_SERVICE_URL", "http://user-service:8001")


async def check_contacts(username_1: str, username_2: str) -> bool:
    """
    Check if two users are contacts by calling user-service.
    
    Args:
        username_1: First username
        username_2: Second username
        
    Returns:
        True if they are contacts, False otherwise
    """
    url = f"{USER_SERVICE_URL}/api/contacts/check-by-username"
    params = {"username_1": username_1, "username_2": username_2}
    
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(url, params=params)
            
            if response.status_code == 200:
                data = response.json()
                return data.get("are_contacts", False)
            else:
                logger.warning(f"Contact check failed: {response.status_code} - {response.text}")
                return False
                
    except httpx.TimeoutException:
        logger.error(f"Timeout calling user-service: {url}")
        return False
    except Exception as e:
        logger.error(f"Error calling user-service: {e}")
        return False


async def check_contacts_batch(current_user: str, participants: list[str]) -> dict[str, bool]:
    """
    Check if current user is contacts with multiple participants.
    
    Args:
        current_user: The user adding participants
        participants: List of usernames to check
        
    Returns:
        Dict mapping username -> is_contact
    """
    results = {}
    
    for participant in participants:
        # Skip checking self
        if participant == current_user:
            results[participant] = True
            continue
            
        results[participant] = await check_contacts(current_user, participant)
    
    return results

