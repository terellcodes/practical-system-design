"""
Copilot Agent Module
"""

from src.agent.graph import CopilotAgent, get_copilot_agent, close_copilot_agent
from src.agent.state import CopilotState
from src.agent.context import set_user_context, get_user_context, clear_user_context

__all__ = [
    "CopilotAgent",
    "get_copilot_agent",
    "close_copilot_agent",
    "CopilotState",
    "set_user_context",
    "get_user_context",
    "clear_user_context",
]
