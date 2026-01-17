"""
LangGraph ReAct Agent Definition

This module defines the copilot agent using LangGraph's create_react_agent.
The agent uses Claude 3.5 Sonnet for reasoning and tool calling.
"""

import logging
from contextlib import AsyncExitStack
from typing import Optional

from langchain_anthropic import ChatAnthropic
from langchain_core.messages import SystemMessage, HumanMessage
from langgraph.prebuilt import create_react_agent
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver

from src.config import ANTHROPIC_API_KEY, ANTHROPIC_MODEL, DATABASE_URL
from src.agent.prompts import get_system_prompt
from src.agent.context import set_user_context, clear_user_context
from src.agent.tools.invite_tools import invite_user, accept_invite
from src.agent.tools.chat_tools import create_chat, add_chat_participants
from src.agent.tools.message_tools import send_chat_message
from src.agent.tools.context_tools import list_contacts, list_pending_invites, list_chats

logger = logging.getLogger(__name__)

# All available tools for the agent
TOOLS = [
    # Action tools
    invite_user,
    accept_invite,
    create_chat,
    add_chat_participants,
    send_chat_message,
    # Context/read-only tools
    list_contacts,
    list_pending_invites,
    list_chats,
]


class CopilotAgent:
    """
    Manages the LangGraph ReAct agent for the copilot service.

    Uses AsyncPostgresSaver for conversation persistence, allowing each user
    to have their own conversation thread.
    """

    def __init__(self):
        self.model: Optional[ChatAnthropic] = None
        self.checkpointer: Optional[AsyncPostgresSaver] = None
        self._exit_stack: Optional[AsyncExitStack] = None
        self._agent = None

    async def initialize(self):
        """Initialize the agent with model and checkpointer."""
        # Initialize the LLM
        self.model = ChatAnthropic(
            model=ANTHROPIC_MODEL,
            api_key=ANTHROPIC_API_KEY,
            max_tokens=4096,
        )

        # Initialize AsyncExitStack to manage async context managers
        self._exit_stack = AsyncExitStack()
        await self._exit_stack.__aenter__()

        # Initialize PostgreSQL checkpointer for persistence
        # AsyncPostgresSaver.from_conn_string returns an async context manager
        self.checkpointer = await self._exit_stack.enter_async_context(
            AsyncPostgresSaver.from_conn_string(DATABASE_URL)
        )
        await self.checkpointer.setup()

        logger.info(f"Copilot agent initialized with model: {ANTHROPIC_MODEL}")

    async def close(self):
        """Close connections."""
        if self._exit_stack:
            await self._exit_stack.__aexit__(None, None, None)
            logger.info("Checkpointer connection closed")

    def _create_agent(self):
        """
        Create a ReAct agent with tools.

        Returns:
            Compiled LangGraph agent
        """
        # Create the ReAct agent with tools
        agent = create_react_agent(
            model=self.model,
            tools=TOOLS,
            checkpointer=self.checkpointer,
        )

        return agent

    async def process_message(
        self,
        message: str,
        user_id: int,
        username: Optional[str] = None,
        user_name: Optional[str] = None,
        conversation_version: int = 0,
    ) -> str:
        """
        Process a user message and return the agent's response.

        Args:
            message: The user's message
            user_id: The user's ID (used for thread_id and context)
            username: The user's username for context
            user_name: The user's display name for context
            conversation_version: Version number for the conversation (incremented on clear)

        Returns:
            The agent's text response
        """
        # Create agent
        agent = self._create_agent()

        # Configuration with thread_id for conversation persistence
        # Include version so clearing history creates a fresh thread
        config = {
            "configurable": {
                "thread_id": f"copilot-user-{user_id}-v{conversation_version}",
            }
        }

        # Set user context for tools to access
        set_user_context(user_id, username, user_name)

        # Check if this is a new conversation (no existing checkpoint)
        existing_checkpoint = await self.checkpointer.aget(config)
        is_new_conversation = existing_checkpoint is None

        # Build the messages - only include system prompt for new conversations
        if is_new_conversation:
            system_prompt = get_system_prompt(user_id, username, user_name)
            input_state = {
                "messages": [
                    SystemMessage(content=system_prompt),
                    HumanMessage(content=message),
                ],
            }
        else:
            input_state = {
                "messages": [
                    HumanMessage(content=message),
                ],
            }

        try:
            # Invoke the agent
            result = await agent.ainvoke(input_state, config=config)

            # Extract the last assistant message
            messages = result.get("messages", [])
            for msg in reversed(messages):
                if hasattr(msg, "type") and msg.type == "ai":
                    # Skip tool call messages, get the final response
                    if not getattr(msg, "tool_calls", None):
                        return msg.content
                elif hasattr(msg, "role") and msg.role == "assistant":
                    return msg.content

            # Fallback if no assistant message found
            return "I processed your request but have no response to provide."

        except Exception as e:
            logger.error(f"Error processing message: {e}")
            raise
        finally:
            # Clear user context after processing
            clear_user_context()

    async def get_history(self, user_id: int) -> list:
        """
        Get conversation history for a user.

        Args:
            user_id: The user's ID

        Returns:
            List of messages in the conversation
        """
        config = {
            "configurable": {
                "thread_id": f"copilot-user-{user_id}",
            }
        }

        try:
            # Get the latest checkpoint
            checkpoint = await self.checkpointer.aget(config)
            if checkpoint and "channel_values" in checkpoint:
                messages = checkpoint["channel_values"].get("messages", [])
                # Convert to serializable format
                history = []
                for msg in messages:
                    if hasattr(msg, "type"):
                        msg_type = msg.type
                    elif hasattr(msg, "role"):
                        msg_type = msg.role
                    else:
                        continue

                    # Map types to roles
                    role = "assistant" if msg_type in ("ai", "assistant") else "user"

                    # Skip tool messages
                    if msg_type == "tool":
                        continue

                    # Skip AI messages that are tool calls
                    if role == "assistant" and getattr(msg, "tool_calls", None):
                        continue

                    content = msg.content if hasattr(msg, "content") else str(msg)
                    if content:  # Only include non-empty messages
                        history.append({
                            "role": role,
                            "content": content,
                        })

                return history

            return []

        except Exception as e:
            logger.error(f"Error getting history: {e}")
            return []

    async def clear_history(self, user_id: int) -> bool:
        """
        Clear conversation history for a user by incrementing version.

        LangGraph checkpoints are immutable, so we track a version number
        that gets incorporated into the thread_id. When clearing, we
        increment the version so the next conversation uses a fresh thread.

        Args:
            user_id: The user's ID

        Returns:
            True if successful
        """
        # Increment the version for this user in the database
        # This effectively starts a new conversation thread
        try:
            # For now, we'll use a simple approach - the version is tracked
            # on the frontend and passed via a header or stored in localStorage
            # The frontend clears localStorage which resets the conversation
            logger.info(f"History clear requested for user {user_id}")
            return True
        except Exception as e:
            logger.error(f"Error clearing history: {e}")
            return False


# Global agent instance (initialized in main.py)
copilot_agent: Optional[CopilotAgent] = None


async def get_copilot_agent() -> CopilotAgent:
    """Get or create the copilot agent."""
    global copilot_agent
    if copilot_agent is None:
        copilot_agent = CopilotAgent()
        await copilot_agent.initialize()
    return copilot_agent


async def close_copilot_agent():
    """Close the copilot agent."""
    global copilot_agent
    if copilot_agent:
        await copilot_agent.close()
        copilot_agent = None
