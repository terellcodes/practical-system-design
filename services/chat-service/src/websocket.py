"""
WebSocket Connection Manager with Redis Pub/Sub - User-Centric Model

Handles real-time WebSocket connections for users (not chat rooms).
Each user has ONE WebSocket connection that receives messages from ALL their chats.

Architecture:
- Each user has one WebSocket connection
- On connect: subscribe to Redis channels for ALL chats user is part of
- Messages from any chat are routed through the user's single connection
- Supports dynamic subscription when user joins/leaves chats
"""

import asyncio
import logging
from typing import Dict, Set, Optional, List
from fastapi import WebSocket
import redis.asyncio as aioredis

logger = logging.getLogger(__name__)


class ConnectionManager:
    """
    User-centric WebSocket manager with Redis pub/sub.
    
    Data structure:
        - user_connections: user_id -> WebSocket connection
        - user_subscriptions: user_id -> Set of chat_ids they're subscribed to
        - user_pubsubs: user_id -> PubSub object handling all their subscriptions
        - user_tasks: user_id -> asyncio.Task for listening to messages
    
    Example:
        user_connections = {
            "alice": ws1,
            "bob": ws2,
        }
        user_subscriptions = {
            "alice": {"chat-abc", "chat-def", "chat-xyz"},
            "bob": {"chat-abc", "chat-ghi"},
        }

        // message mailbox for each user
        user_pubsubs = {
            "alice": <PubSub listening to ["chat:chat-abc","chat:chat-def", "chat:chat-xyz"]>,
            "bob": <PubSub listening to ["chat:chat-abc","chat:chat-ghi"]>,
        }

        // background tasks listening for messages on each user's pubsub and routing to the user's WebSocket connection
        user_tasks = {
            "alice": <Task listening for messages on alice's pubsub>,
            "bob": <Task listening for messages on bob's pubsub>,
        }
    """
    
    def __init__(self, redis_url: str):
        # user_id -> WebSocket connection (one per user)
        self.user_connections: Dict[str, WebSocket] = {}
        
        # user_id -> Set of chat_ids they're subscribed to
        self.user_subscriptions: Dict[str, Set[str]] = {}
        
        # user_id -> Redis PubSub object
        self.user_pubsubs: Dict[str, aioredis.client.PubSub] = {}
        
        # user_id -> asyncio.Task for the listener
        self.user_tasks: Dict[str, asyncio.Task] = {}
        
        # Redis client for publishing
        self.redis_url = redis_url
        self.redis_client: Optional[aioredis.Redis] = None
        
    async def initialize(self):
        """Initialize Redis connection. Call this on startup."""
        self.redis_client = await aioredis.from_url(
            self.redis_url,
            encoding="utf-8",
            decode_responses=True
        )
        logger.info(f"Redis connection initialized for WebSocket pub/sub: {self.redis_url}")
    
    async def close(self):
        """Close all Redis connections. Call this on shutdown."""
        # Cancel all listener tasks
        for task in self.user_tasks.values():
            task.cancel()
        
        # Close all pubsub connections
        for pubsub in self.user_pubsubs.values():
            await pubsub.close()
        
        # Close main Redis client
        if self.redis_client:
            await self.redis_client.close()
        
        logger.info("Redis connections closed")
    
    async def connect(self, websocket: WebSocket, user_id: str, chat_ids: List[str]) -> None:
        """
        Accept a new WebSocket connection for a user.
        Subscribes to Redis channels for all their chats.
        
        Args:
            websocket: The WebSocket connection
            user_id: The user's ID
            chat_ids: List of chat IDs the user is part of
        """
        await websocket.accept()
        
        # Store the connection
        self.user_connections[user_id] = websocket
        self.user_subscriptions[user_id] = set(chat_ids)
        
        # Create pubsub and subscribe to all chat channels
        pubsub = self.redis_client.pubsub()
        self.user_pubsubs[user_id] = pubsub
        
        # Subscribe to all chat channels
        if chat_ids:
            channels = [f"chat:{chat_id}" for chat_id in chat_ids]
            await pubsub.subscribe(*channels)
            logger.info(f"User {user_id} subscribed to {len(chat_ids)} channels: {channels}")
        
        # Start background task to listen for messages
        task = asyncio.create_task(self._listen_for_user(user_id, pubsub))
        self.user_tasks[user_id] = task
        
        logger.info(f"User {user_id} connected. Total users: {len(self.user_connections)}")
    
    async def disconnect(self, user_id: str) -> None:
        """
        Remove a user's WebSocket connection and cleanup.
        """
        # Cancel listener task
        if user_id in self.user_tasks:
            self.user_tasks[user_id].cancel()
            del self.user_tasks[user_id]
        
        # Close pubsub
        if user_id in self.user_pubsubs:
            pubsub = self.user_pubsubs[user_id]
            await pubsub.unsubscribe()
            await pubsub.close()
            del self.user_pubsubs[user_id]
        
        # Remove connection and subscriptions
        if user_id in self.user_connections:
            del self.user_connections[user_id]
        if user_id in self.user_subscriptions:
            del self.user_subscriptions[user_id]
        
        logger.info(f"User {user_id} disconnected. Total users: {len(self.user_connections)}")
    
    async def subscribe_to_chat(self, user_id: str, chat_id: str) -> bool:
        """
        Dynamically subscribe a connected user to a new chat.
        Called when user joins a chat while already connected.
        
        Returns True if subscription was added, False if user not connected.
        """
        if user_id not in self.user_pubsubs:
            logger.warning(f"Cannot subscribe {user_id} to {chat_id}: user not connected")
            return False
        
        # Add to subscriptions set
        if user_id not in self.user_subscriptions:
            self.user_subscriptions[user_id] = set()
        
        if chat_id in self.user_subscriptions[user_id]:
            logger.debug(f"User {user_id} already subscribed to {chat_id}")
            return True
        
        # Subscribe to the new channel
        channel = f"chat:{chat_id}"
        await self.user_pubsubs[user_id].subscribe(channel)
        self.user_subscriptions[user_id].add(chat_id)
        
        logger.info(f"User {user_id} dynamically subscribed to {chat_id}")
        return True
    
    async def unsubscribe_from_chat(self, user_id: str, chat_id: str) -> bool:
        """
        Dynamically unsubscribe a connected user from a chat.
        Called when user leaves a chat while still connected.
        
        Returns True if unsubscribed, False if user not connected.
        """
        if user_id not in self.user_pubsubs:
            return False
        
        if chat_id not in self.user_subscriptions.get(user_id, set()):
            return True  # Already not subscribed
        
        # Unsubscribe from the channel
        channel = f"chat:{chat_id}"
        await self.user_pubsubs[user_id].unsubscribe(channel)
        self.user_subscriptions[user_id].discard(chat_id)
        
        logger.info(f"User {user_id} unsubscribed from {chat_id}")
        return True
    
    async def _listen_for_user(self, user_id: str, pubsub: aioredis.client.PubSub) -> None:
        """
        Background task that listens for messages on all subscribed channels.
        Routes messages to the user's WebSocket connection.
        """
        logger.info(f"Started listening for user {user_id}")
        
        try:
            async for message in pubsub.listen():
                logger.info(f"Recived message for {user_id}", message)
                # Ignore subscription confirmation messages
                if message["type"] != "message":
                    continue
                
                # Get the message data and send to user's WebSocket
                message_data = message["data"]
                
                if user_id in self.user_connections:
                    try:
                        await self.user_connections[user_id].send_text(message_data)
                    except Exception as e:
                        logger.warning(f"Failed to send message to {user_id}: {e}")
                        
        except asyncio.CancelledError:
            logger.info(f"Listener task cancelled for user {user_id}")
        except Exception as e:
            logger.error(f"Error in listener task for user {user_id}: {e}")
    
    async def publish_message(self, chat_id: str, message: str) -> None:
        """
        Publish a message to a chat's Redis channel.
        All users subscribed to this chat will receive it.
        
        Args:
            chat_id: The chat room to broadcast to
            message: The message to send (should be JSON string)
        """
        channel = f"chat:{chat_id}"
        try:
            await self.redis_client.publish(channel, message)
            logger.debug(f"Published message to Redis channel {channel}")
        except Exception as e:
            logger.error(f"Failed to publish to Redis: {e}")
    
    async def send_personal(self, user_id: str, message: str) -> None:
        """
        Send a message directly to a specific user.
        """
        if user_id in self.user_connections:
            try:
                await self.user_connections[user_id].send_text(message)
            except Exception as e:
                logger.warning(f"Failed to send personal message to {user_id}: {e}")
    
    def is_user_connected(self, user_id: str) -> bool:
        """Check if a user is currently connected."""
        return user_id in self.user_connections
    
    def get_user_subscriptions(self, user_id: str) -> Set[str]:
        """Get the set of chat_ids a user is subscribed to."""
        return self.user_subscriptions.get(user_id, set())
    
    def get_total_connections(self) -> int:
        """Get total number of connected users."""
        return len(self.user_connections)
    
    def get_connected_users(self) -> list:
        """Get list of connected user IDs."""
        return list(self.user_connections.keys())


# Global connection manager instance (initialized in main.py on startup)
manager: Optional[ConnectionManager] = None


def create_connection_manager(redis_url: str) -> ConnectionManager:
    """Factory function to create and return a ConnectionManager instance."""
    return ConnectionManager(redis_url)
