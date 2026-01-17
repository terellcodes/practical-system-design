"""
Context/read-only tools for the copilot agent
"""

import logging

from langchain_core.tools import tool

from src.services.user_service_client import get_user_service_client
from src.services.chat_service_client import get_chat_service_client
from src.agent.context import get_user_context

logger = logging.getLogger(__name__)


@tool
async def list_contacts() -> str:
    """
    Get the list of user's contacts.

    Use this tool when the user wants to:
    - See their contacts
    - Know who they can add to chats
    - Check if someone is a contact
    - Get contact IDs for adding to chats

    Returns:
        A formatted list of contacts with their IDs, names, and usernames
    """
    ctx = get_user_context()
    if not ctx:
        return "Error: User context not available. Cannot list contacts."

    user_id = ctx.user_id
    client = get_user_service_client()

    try:
        contacts = await client.get_contacts(user_id)

        if not contacts:
            return "You don't have any contacts yet. Use invite_user to connect with others!"

        lines = ["Your contacts:"]
        for contact in contacts:
            # ContactWithUser includes 'contact' with user details
            user_info = contact.get("contact", contact)
            cid = user_info.get("id", "?")
            name = user_info.get("name", "Unknown")
            username = user_info.get("username", "unknown")
            lines.append(f"- {name} (@{username}) [ID: {cid}]")

        return "\n".join(lines)

    except Exception as e:
        logger.error(f"Failed to list contacts: {e}")
        return f"Error listing contacts: {str(e)}"


@tool
async def list_pending_invites() -> str:
    """
    Get pending invites received by the user.

    Use this tool when the user wants to:
    - See who has invited them
    - Check for pending friend requests
    - Find invite IDs to accept or reject

    Returns:
        A formatted list of pending invites with IDs and invitor details
    """
    ctx = get_user_context()
    if not ctx:
        return "Error: User context not available. Cannot list invites."

    user_id = ctx.user_id
    client = get_user_service_client()

    try:
        invites = await client.get_pending_invites(user_id)

        if not invites:
            return "You don't have any pending invites."

        lines = ["Your pending invites:"]
        for invite in invites:
            invite_id = invite.get("id", "?")
            invitor = invite.get("invitor", {})
            name = invitor.get("name", "Unknown")
            username = invitor.get("username", "unknown")
            lines.append(f"- From {name} (@{username}) [Invite ID: {invite_id}]")

        lines.append("\nUse accept_invite with the invite ID to accept an invite.")

        return "\n".join(lines)

    except Exception as e:
        logger.error(f"Failed to list invites: {e}")
        return f"Error listing invites: {str(e)}"


@tool
async def list_chats() -> str:
    """
    Get the list of user's chats.

    Use this tool when the user wants to:
    - See their chat groups
    - Find a chat to send a message to
    - Get chat IDs
    - Check what chats they're in

    Returns:
        A formatted list of chats with their IDs and names
    """
    ctx = get_user_context()
    if not ctx:
        return "Error: User context not available. Cannot list chats."

    user_id = ctx.user_id
    client = await get_chat_service_client()

    try:
        chats = await client.get_chats_for_user(user_id)

        if not chats:
            return "You're not in any chats yet. Use create_chat to start one!"

        lines = ["Your chats:"]
        for chat in chats:
            chat_id = chat.get("id", "?")
            name = chat.get("name", "Unnamed Chat")
            participant_ids = chat.get("participant_ids", [])
            participant_count = len(participant_ids) if isinstance(participant_ids, list) else 0
            lines.append(f"- {name} ({participant_count} participants) [ID: {chat_id}]")

        return "\n".join(lines)

    except Exception as e:
        logger.error(f"Failed to list chats: {e}")
        return f"Error listing chats: {str(e)}"
