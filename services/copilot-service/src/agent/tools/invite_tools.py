"""
Invite management tools for the copilot agent
"""

import logging

from langchain_core.tools import tool

from src.services.user_service_client import get_user_service_client
from src.agent.context import get_user_context

logger = logging.getLogger(__name__)


@tool
async def invite_user(connect_pin: str) -> str:
    """
    Send a connection invite to another user using their 8-character connect PIN.

    Use this tool when the user wants to:
    - Invite someone to connect
    - Add a new contact via their PIN code
    - Send a friend request

    Args:
        connect_pin: The 8-character connect PIN of the user to invite

    Returns:
        A message indicating success or describing any error
    """
    ctx = get_user_context()
    if not ctx:
        return "Error: User context not available. Cannot send invite."

    user_id = ctx.user_id

    # Validate PIN format
    if not connect_pin or len(connect_pin) != 8:
        return f"Error: Connect PIN must be exactly 8 characters. Received: '{connect_pin}'"

    client = get_user_service_client()

    try:
        result = await client.send_invite(user_id, connect_pin.upper())

        invitee = result.get("invitee", {})
        invitee_name = invitee.get("name", "Unknown")
        invitee_username = invitee.get("username", "unknown")

        return (
            f"Successfully sent invite to {invitee_name} (@{invitee_username}). "
            "They will see the invite in their pending invites."
        )

    except Exception as e:
        error_msg = str(e)

        # Parse common error cases
        if "404" in error_msg:
            return f"Error: No user found with connect PIN '{connect_pin}'. Please verify the PIN."
        elif "400" in error_msg:
            if "yourself" in error_msg.lower():
                return "Error: You cannot invite yourself."
            elif "contact" in error_msg.lower():
                return "Error: This user is already in your contacts."
            elif "pending" in error_msg.lower():
                return "Error: There is already a pending invite between you and this user."
            return f"Error: Invalid request - {error_msg}"
        else:
            logger.error(f"Failed to send invite: {e}")
            return f"Error sending invite: {error_msg}"


@tool
async def accept_invite(invite_id: int) -> str:
    """
    Accept a pending invite to become contacts with another user.

    Use this tool when the user wants to:
    - Accept a connection request
    - Confirm a friend request
    - Add someone who invited them

    Args:
        invite_id: The ID of the pending invite to accept

    Returns:
        A message indicating success or describing any error
    """
    ctx = get_user_context()
    if not ctx:
        return "Error: User context not available. Cannot accept invite."

    user_id = ctx.user_id
    client = get_user_service_client()

    try:
        result = await client.accept_invite(user_id, invite_id)

        return (
            f"Successfully accepted invite (ID: {invite_id}). "
            "You are now contacts and can chat with each other!"
        )

    except Exception as e:
        error_msg = str(e)

        if "404" in error_msg:
            return f"Error: Invite with ID {invite_id} not found."
        elif "403" in error_msg or "not the invitee" in error_msg.lower():
            return "Error: You can only accept invites that were sent to you."
        elif "400" in error_msg:
            if "pending" in error_msg.lower():
                return "Error: This invite has already been responded to."
            return f"Error: Invalid request - {error_msg}"
        else:
            logger.error(f"Failed to accept invite: {e}")
            return f"Error accepting invite: {error_msg}"
