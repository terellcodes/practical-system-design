"""
Chat management tools for the copilot agent
"""

import logging
from typing import Optional, List

from langchain_core.tools import tool

from src.services.chat_service_client import get_chat_service_client
from src.agent.context import get_user_context

logger = logging.getLogger(__name__)


@tool
async def create_chat(name: str, participant_ids: Optional[List[int]] = None) -> str:
    """
    Create a new chat group.

    Use this tool when the user wants to:
    - Create a new chat
    - Start a group conversation
    - Make a new chat room

    The user who creates the chat is automatically added as a participant.

    Args:
        name: The name of the chat (e.g., "Team Chat", "Project Discussion")
        participant_ids: Optional list of contact user IDs to add to the chat.
                        Only contacts can be added to chats.

    Returns:
        A message indicating success with chat details, or describing any error
    """
    ctx = get_user_context()
    if not ctx:
        return "Error: User context not available. Cannot create chat."

    user_id = ctx.user_id

    if not name or not name.strip():
        return "Error: Chat name is required."

    client = await get_chat_service_client()

    try:
        result = await client.create_chat(
            name=name.strip(),
            creator_id=user_id,
            participant_ids=participant_ids
        )

        chat_id = result.get("id", "unknown")
        chat_name = result.get("name", name)
        participants = result.get("participant_ids", [])

        participant_count = len(participants) if isinstance(participants, list) else 0

        return (
            f"Successfully created chat '{chat_name}' (ID: {chat_id}). "
            f"The chat has {participant_count} participant(s)."
        )

    except Exception as e:
        error_msg = str(e)
        logger.error(f"Failed to create chat: {e}")
        return f"Error creating chat: {error_msg}"


@tool
async def add_chat_participants(chat_id: str, participant_ids: List[int]) -> str:
    """
    Add participants to an existing chat.

    Use this tool when the user wants to:
    - Add people to a chat
    - Invite contacts to a group
    - Include more members in a conversation

    Note: Only contacts can be added to chats.

    Args:
        chat_id: The ID of the chat to add participants to
        participant_ids: List of user IDs to add to the chat

    Returns:
        A message indicating success or describing any error
    """
    ctx = get_user_context()
    if not ctx:
        return "Error: User context not available. Cannot add participants."

    user_id = ctx.user_id

    if not chat_id:
        return "Error: Chat ID is required."

    if not participant_ids:
        return "Error: At least one participant ID is required."

    client = await get_chat_service_client()

    try:
        result = await client.add_participants(
            chat_id=chat_id,
            participant_ids=participant_ids,
            user_id=user_id
        )

        added_count = len(result) if isinstance(result, list) else 0

        return (
            f"Successfully added {added_count} participant(s) to the chat. "
            "They can now see and send messages in this chat."
        )

    except Exception as e:
        error_msg = str(e)

        if "404" in error_msg:
            return f"Error: Chat with ID '{chat_id}' not found."
        elif "400" in error_msg:
            if "contact" in error_msg.lower():
                return "Error: You can only add your contacts to chats."
            return f"Error: Invalid request - {error_msg}"
        else:
            logger.error(f"Failed to add participants: {e}")
            return f"Error adding participants: {error_msg}"
