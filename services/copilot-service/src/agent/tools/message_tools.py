"""
Message sending tools for the copilot agent
"""

import logging

from langchain_core.tools import tool

from src.services.chat_service_client import get_chat_service_client
from src.agent.context import get_user_context

logger = logging.getLogger(__name__)


@tool
async def send_chat_message(chat_id: str, content: str) -> str:
    """
    Send a message to a chat on behalf of the user.

    Use this tool when the user wants to:
    - Send a message to a chat
    - Post a message to a group
    - Say something in a conversation

    The message will appear as if the user sent it.

    Args:
        chat_id: The ID of the chat to send the message to
        content: The message content to send

    Returns:
        A message indicating success or describing any error
    """
    ctx = get_user_context()
    if not ctx:
        return "Error: User context not available. Cannot send message."

    user_id = ctx.user_id
    username = ctx.username
    user_name = ctx.user_name

    if not chat_id:
        return "Error: Chat ID is required."

    if not content or not content.strip():
        return "Error: Message content cannot be empty."

    client = await get_chat_service_client()

    try:
        result = await client.send_message(
            chat_id=chat_id,
            sender_id=user_id,
            sender_name=user_name or "Unknown",
            sender_username=username or "unknown",
            content=content.strip()
        )

        message_id = result.get("message_id", "unknown")

        return (
            f"Successfully sent message to chat {chat_id}. "
            f"Message ID: {message_id}"
        )

    except Exception as e:
        error_msg = str(e)

        if "not initialized" in error_msg.lower():
            return "Error: Message service not ready. Please try again."
        else:
            logger.error(f"Failed to send message: {e}")
            return f"Error sending message: {error_msg}"
