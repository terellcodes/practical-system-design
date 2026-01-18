"""
HTTP and Redis client for chat-service API calls
"""

import json
import logging
from typing import Optional, List

import httpx
import redis.asyncio as aioredis

from src.config import CHAT_SERVICE_URL, REDIS_URL
from common.observability import CORRELATION_ID_HEADER

logger = logging.getLogger(__name__)


class ChatServiceClient:
    """Client for interacting with chat-service endpoints."""

    def __init__(
        self,
        base_url: str = CHAT_SERVICE_URL,
        redis_url: str = REDIS_URL
    ):
        self.base_url = base_url
        self.redis_url = redis_url
        self.timeout = httpx.Timeout(10.0)
        self.http_client = httpx.AsyncClient(timeout=self.timeout)
        self.redis_client: Optional[aioredis.Redis] = None

    async def initialize(self):
        """Initialize Redis connection for publishing messages."""
        self.redis_client = await aioredis.from_url(
            self.redis_url,
            encoding="utf-8",
            decode_responses=True
        )
        logger.info("Redis client initialized for chat message publishing")

    async def close(self):
        """Close HTTP and Redis connections."""
        await self.http_client.aclose()
        if self.redis_client:
            await self.redis_client.close()
            logger.info("Redis client closed")

    async def create_chat(
        self,
        name: str,
        creator_id: int,
        participant_ids: Optional[List[int]] = None,
        correlation_id: Optional[str] = None
    ) -> dict:
        """
        Create a new chat.

        Args:
            name: Name of the chat
            creator_id: ID of the user creating the chat
            participant_ids: Optional list of participant IDs to add
            correlation_id: Optional correlation ID for tracing

        Returns:
            Created chat details
        """
        # Build participant list - creator is always included
        participants = [creator_id]
        if participant_ids:
            for pid in participant_ids:
                if pid not in participants:
                    participants.append(pid)

        headers = {}
        if correlation_id:
            headers[CORRELATION_ID_HEADER] = correlation_id

        response = await self.http_client.post(
            f"{self.base_url}/chats",
            json={
                "name": name,
                "participant_ids": participants
            },
            headers=headers if headers else None
        )
        response.raise_for_status()
        return response.json()

    async def add_participants(
        self,
        chat_id: str,
        participant_ids: List[int],
        user_id: int,
        correlation_id: Optional[str] = None
    ) -> list:
        """
        Add participants to an existing chat.

        Args:
            chat_id: ID of the chat
            participant_ids: List of user IDs to add
            user_id: ID of the user making the request (for contact verification)
            correlation_id: Optional correlation ID for tracing

        Returns:
            List of added participants
        """
        headers = {"X-User-Id": str(user_id)}
        if correlation_id:
            headers[CORRELATION_ID_HEADER] = correlation_id

        response = await self.http_client.post(
            f"{self.base_url}/chats/{chat_id}/participants",
            json={"participant_ids": participant_ids},
            headers=headers
        )
        response.raise_for_status()
        return response.json()

    async def get_chat(
        self, chat_id: str, correlation_id: Optional[str] = None
    ) -> Optional[dict]:
        """
        Get chat details with participants.

        Args:
            chat_id: ID of the chat
            correlation_id: Optional correlation ID for tracing

        Returns:
            Chat details or None if not found
        """
        headers = {}
        if correlation_id:
            headers[CORRELATION_ID_HEADER] = correlation_id

        try:
            response = await self.http_client.get(
                f"{self.base_url}/chats/{chat_id}",
                headers=headers if headers else None
            )
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                return None
            raise

    async def get_chats_for_user(
        self, user_id: int, correlation_id: Optional[str] = None
    ) -> list:
        """
        Get all chats for a user.

        Args:
            user_id: ID of the user
            correlation_id: Optional correlation ID for tracing

        Returns:
            List of chats the user is a participant in
        """
        headers = {}
        if correlation_id:
            headers[CORRELATION_ID_HEADER] = correlation_id

        response = await self.http_client.get(
            f"{self.base_url}/chats/participant/{user_id}",
            headers=headers if headers else None
        )
        response.raise_for_status()
        return response.json()

    async def send_message(
        self,
        chat_id: str,
        sender_id: int,
        sender_name: str,
        sender_username: str,
        content: str
    ) -> dict:
        """
        Send a message to a chat via Redis pub/sub.

        The chat-service uses Redis pub/sub for real-time message delivery.
        This publishes directly to the chat channel.

        Args:
            chat_id: ID of the chat
            sender_id: ID of the message sender
            sender_name: Display name of the sender
            sender_username: Username of the sender
            content: Message content

        Returns:
            Message details
        """
        import uuid
        from datetime import datetime

        if not self.redis_client:
            raise RuntimeError("Redis client not initialized. Call initialize() first.")

        # Create message payload matching chat-service format
        message_id = str(uuid.uuid4())
        timestamp = datetime.utcnow().isoformat() + "Z"

        message = {
            "type": "chat_message",
            "data": {
                "message_id": message_id,
                "chat_id": chat_id,
                "sender_id": sender_id,
                "sender_name": sender_name,
                "sender_username": sender_username,
                "content": content,
                "timestamp": timestamp,
                "source": "copilot"
            }
        }

        # Publish to the chat channel
        channel = f"chat:{chat_id}"
        await self.redis_client.publish(channel, json.dumps(message))

        logger.info(f"Published message to {channel}")

        return {
            "message_id": message_id,
            "chat_id": chat_id,
            "content": content,
            "timestamp": timestamp
        }


# Global client instance
chat_service_client: Optional[ChatServiceClient] = None


async def get_chat_service_client() -> ChatServiceClient:
    """Get or create the chat service client."""
    global chat_service_client
    if chat_service_client is None:
        chat_service_client = ChatServiceClient()
        await chat_service_client.initialize()
    return chat_service_client


async def close_chat_service_client():
    """Close the chat service client."""
    global chat_service_client
    if chat_service_client:
        await chat_service_client.close()
        chat_service_client = None
