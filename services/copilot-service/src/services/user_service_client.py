"""
HTTP client for user-service API calls
"""

import logging
from typing import Optional

import httpx

from src.config import USER_SERVICE_URL
from common.observability import CORRELATION_ID_HEADER

logger = logging.getLogger(__name__)


class UserServiceClient:
    """Client for interacting with user-service endpoints."""

    def __init__(self, base_url: str = USER_SERVICE_URL):
        self.base_url = base_url
        self.timeout = httpx.Timeout(10.0)
        self.client = httpx.AsyncClient(timeout=self.timeout)

    async def close(self):
        """Close the HTTP client."""
        await self.client.aclose()

    async def send_invite(
        self, user_id: int, connect_pin: str, correlation_id: Optional[str] = None
    ) -> dict:
        """
        Send an invite to another user by their connect PIN.

        Args:
            user_id: ID of the user sending the invite
            connect_pin: 8-character connect PIN of the invitee
            correlation_id: Optional correlation ID for tracing

        Returns:
            Invite details if successful

        Raises:
            httpx.HTTPStatusError: If the request fails
        """
        headers = {"X-User-Id": str(user_id)}
        if correlation_id:
            headers[CORRELATION_ID_HEADER] = correlation_id

        response = await self.client.post(
            f"{self.base_url}/api/invites",
            json={"connect_pin": connect_pin},
            headers=headers
        )
        response.raise_for_status()
        return response.json()

    async def accept_invite(
        self, user_id: int, invite_id: int, correlation_id: Optional[str] = None
    ) -> dict:
        """
        Accept a pending invite.

        Args:
            user_id: ID of the user accepting (must be the invitee)
            invite_id: ID of the invite to accept
            correlation_id: Optional correlation ID for tracing

        Returns:
            Updated invite details

        Raises:
            httpx.HTTPStatusError: If the request fails
        """
        headers = {"X-User-Id": str(user_id)}
        if correlation_id:
            headers[CORRELATION_ID_HEADER] = correlation_id

        response = await self.client.put(
            f"{self.base_url}/api/invites/{invite_id}",
            json={"status": "accepted"},
            headers=headers
        )
        response.raise_for_status()
        return response.json()

    async def get_pending_invites(
        self, user_id: int, correlation_id: Optional[str] = None
    ) -> list:
        """
        Get all pending invites received by the user.

        Args:
            user_id: ID of the user
            correlation_id: Optional correlation ID for tracing

        Returns:
            List of pending invites with invitor details
        """
        headers = {"X-User-Id": str(user_id)}
        if correlation_id:
            headers[CORRELATION_ID_HEADER] = correlation_id

        response = await self.client.get(
            f"{self.base_url}/api/invites",
            headers=headers
        )
        response.raise_for_status()
        return response.json()

    async def get_contacts(
        self, user_id: int, correlation_id: Optional[str] = None
    ) -> list:
        """
        Get all contacts for the user.

        Args:
            user_id: ID of the user
            correlation_id: Optional correlation ID for tracing

        Returns:
            List of contacts with user details
        """
        headers = {"X-User-Id": str(user_id)}
        if correlation_id:
            headers[CORRELATION_ID_HEADER] = correlation_id

        response = await self.client.get(
            f"{self.base_url}/api/contacts",
            headers=headers
        )
        response.raise_for_status()
        return response.json()

    async def get_user(
        self, user_id: int, correlation_id: Optional[str] = None
    ) -> Optional[dict]:
        """
        Get user details by ID.

        Args:
            user_id: ID of the user
            correlation_id: Optional correlation ID for tracing

        Returns:
            User details or None if not found
        """
        headers = {}
        if correlation_id:
            headers[CORRELATION_ID_HEADER] = correlation_id

        try:
            response = await self.client.get(
                f"{self.base_url}/api/users/{user_id}",
                headers=headers if headers else None
            )
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                return None
            raise


# Global client instance
user_service_client: Optional[UserServiceClient] = None


def get_user_service_client() -> UserServiceClient:
    """Get or create the user service client."""
    global user_service_client
    if user_service_client is None:
        user_service_client = UserServiceClient()
    return user_service_client


async def close_user_service_client():
    """Close the user service client."""
    global user_service_client
    if user_service_client:
        await user_service_client.close()
        user_service_client = None
