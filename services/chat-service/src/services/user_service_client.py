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


async def check_contacts(user_id_1: int, user_id_2: int) -> bool:
    """
    Check if two users are contacts by calling user-service.

    Args:
        user_id_1: First user ID
        user_id_2: Second user ID

    Returns:
        True if they are contacts, False otherwise
    """
    url = f"{USER_SERVICE_URL}/api/contacts/check"
    params = {"user_id_1": user_id_1, "user_id_2": user_id_2}

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


async def check_contacts_batch(current_user_id: int, participant_ids: list[int]) -> dict[int, bool]:
    """
    Check if current user is contacts with multiple participants.

    Args:
        current_user_id: The user ID adding participants
        participant_ids: List of user IDs to check

    Returns:
        Dict mapping user_id -> is_contact
    """
    results = {}

    for participant_id in participant_ids:
        # Skip checking self
        if participant_id == current_user_id:
            results[participant_id] = True
            continue

        results[participant_id] = await check_contacts(current_user_id, participant_id)

    return results



