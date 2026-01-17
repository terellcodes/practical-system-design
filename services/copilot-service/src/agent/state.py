"""
LangGraph Agent State Definition
"""

from typing import Annotated, Optional
from typing_extensions import TypedDict
from langgraph.graph.message import add_messages


class CopilotState(TypedDict):
    """State for the copilot agent.

    Attributes:
        messages: Conversation history with user and assistant messages
        user_id: ID of the user making requests (from X-User-Id header)
        username: Username for display/context
        user_name: User's display name for context
    """
    messages: Annotated[list, add_messages]
    user_id: int
    username: Optional[str]
    user_name: Optional[str]
