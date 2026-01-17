"""
Copilot API endpoints
"""

import logging
from typing import Optional

from fastapi import APIRouter, Header, HTTPException
from pydantic import BaseModel

from src.agent.graph import get_copilot_agent

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/copilot", tags=["Copilot"])


class ChatRequest(BaseModel):
    """Request body for chat endpoint."""
    message: str


class ChatResponse(BaseModel):
    """Response body for chat endpoint."""
    response: str


class HistoryMessage(BaseModel):
    """A message in the conversation history."""
    role: str
    content: str


class HistoryResponse(BaseModel):
    """Response body for history endpoint."""
    messages: list[HistoryMessage]


class ClearHistoryResponse(BaseModel):
    """Response body for clear history endpoint."""
    success: bool
    message: str


@router.post("/chat", response_model=ChatResponse)
async def chat(
    request: ChatRequest,
    x_user_id: int = Header(..., description="ID of the user"),
    x_username: Optional[str] = Header(None, description="Username of the user"),
    x_user_name: Optional[str] = Header(None, description="Display name of the user"),
    x_conversation_version: int = Header(0, description="Conversation version for fresh threads"),
):
    """
    Process a chat message and return the AI copilot's response.

    The copilot can perform various actions on behalf of the user:
    - Send invites to other users
    - Accept pending invites
    - Create chats
    - Add participants to chats
    - Send messages to chats

    The conversation is persisted per-user using PostgreSQL.
    """
    if not request.message.strip():
        raise HTTPException(status_code=400, detail="Message cannot be empty")

    try:
        agent = await get_copilot_agent()
        response = await agent.process_message(
            message=request.message,
            user_id=x_user_id,
            username=x_username,
            user_name=x_user_name,
            conversation_version=x_conversation_version,
        )
        return ChatResponse(response=response)

    except Exception as e:
        logger.error(f"Error in chat endpoint: {e}")
        raise HTTPException(
            status_code=500,
            detail="An error occurred while processing your request"
        )


@router.get("/history", response_model=HistoryResponse)
async def get_history(
    x_user_id: int = Header(..., description="ID of the user"),
):
    """
    Get the conversation history for the current user.

    Returns all messages in the user's copilot conversation.
    """
    try:
        agent = await get_copilot_agent()
        messages = await agent.get_history(user_id=x_user_id)
        return HistoryResponse(
            messages=[HistoryMessage(**msg) for msg in messages]
        )

    except Exception as e:
        logger.error(f"Error in history endpoint: {e}")
        raise HTTPException(
            status_code=500,
            detail="An error occurred while retrieving history"
        )


@router.delete("/history", response_model=ClearHistoryResponse)
async def clear_history(
    x_user_id: int = Header(..., description="ID of the user"),
):
    """
    Clear the conversation history for the current user.

    This resets the copilot conversation to a fresh state.
    """
    try:
        agent = await get_copilot_agent()
        success = await agent.clear_history(user_id=x_user_id)
        return ClearHistoryResponse(
            success=success,
            message="History cleared successfully" if success else "Failed to clear history"
        )

    except Exception as e:
        logger.error(f"Error in clear history endpoint: {e}")
        raise HTTPException(
            status_code=500,
            detail="An error occurred while clearing history"
        )
