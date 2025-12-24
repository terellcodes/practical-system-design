"""
WebSocket Connection Manager with Redis Pub/Sub

Handles real-time WebSocket connections for chat rooms.
This is Option C: Redis pub/sub - messages broadcast across all instances.

Architecture:
- Each instance maintains its own local WebSocket connections
- When a message is sent, it's published to Redis channel: "chat:{chat_id}"
- All instances subscribed to that channel receive the message
- Each instance broadcasts the message to its local WebSocket connections
"""

import asyncio
import logging
from typing import Dict, Set, Optional
from fastapi import WebSocket
import redis.asyncio as aioredis

logger = logging.getLogger(__name__)


class ConnectionManager:
    """
    Manages WebSocket connections for chat rooms with Redis pub/sub.
    
    Data structure:
        - active_connections: chat_id -> Set of local WebSocket connections
        - subscribed_channels: chat_id -> pubsub object for that channel
    
    Example:
        active_connections = {
            "chat-abc123": {ws1, ws2, ws3},
            "chat-def456": {ws4, ws5},
        }
        subscribed_channels = {
            "chat-abc123": <PubSub object>,
            "chat-def456": <PubSub object>,
        }
    """
    
    def __init__(self, redis_url: str):
        # chat_id -> set of active local WebSocket connections
        self.active_connections: Dict[str, Set[WebSocket]] = {}
        
        # chat_id -> Redis PubSub object for listening
        self.subscribed_channels: Dict[str, aioredis.client.PubSub] = {}
        
        # chat_id -> asyncio.Task for the listener
        self.listener_tasks: Dict[str, asyncio.Task] = {}
        
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
        for task in self.listener_tasks.values():
            task.cancel()
        
        # Unsubscribe from all channels
        for pubsub in self.subscribed_channels.values():
            await pubsub.unsubscribe()
            await pubsub.close()
        
        # Close main Redis client
        if self.redis_client:
            await self.redis_client.close()
        
        logger.info("Redis connections closed")
    
    async def _subscribe_to_channel(self, chat_id: str) -> None:
        """
        Subscribe to a Redis pub/sub channel for a chat room.
        Starts a background task to listen for messages.
        """
        channel = f"chat:{chat_id}"
        
        try:
            # Create a new pubsub object for this channel
            pubsub = self.redis_client.pubsub()
            await pubsub.subscribe(channel)
            
            # Store the pubsub object
            self.subscribed_channels[chat_id] = pubsub
            
            # Start background task to listen for messages
            task = asyncio.create_task(self._listen_to_channel(chat_id, pubsub))
            self.listener_tasks[chat_id] = task
            
            logger.info(f"Subscribed to Redis channel: {channel}")
        except Exception as e:
            logger.error(f"Failed to subscribe to Redis channel {channel}: {e}")
    
    async def _unsubscribe_from_channel(self, chat_id: str) -> None:
        """
        Unsubscribe from a Redis pub/sub channel and cleanup.
        """
        if chat_id in self.subscribed_channels:
            channel = f"chat:{chat_id}"
            
            try:
                # Cancel the listener task
                if chat_id in self.listener_tasks:
                    self.listener_tasks[chat_id].cancel()
                    del self.listener_tasks[chat_id]
                
                # Unsubscribe and close pubsub
                pubsub = self.subscribed_channels[chat_id]
                await pubsub.unsubscribe(channel)
                await pubsub.close()
                
                del self.subscribed_channels[chat_id]
                
                logger.info(f"Unsubscribed from Redis channel: {channel}")
            except Exception as e:
                logger.error(f"Failed to unsubscribe from Redis channel {channel}: {e}")
    
    async def _listen_to_channel(self, chat_id: str, pubsub: aioredis.client.PubSub) -> None:
        """
        Background task that listens for messages on a Redis pub/sub channel.
        When a message arrives, broadcasts it to all local WebSocket connections.
        """
        channel = f"chat:{chat_id}"
        logger.info(f"Started listening to Redis channel: {channel}")
        
        try:
            async for message in pubsub.listen():
                # Ignore subscription confirmation messages
                if message["type"] != "message":
                    continue
                
                # Get the message data
                message_data = message["data"]
                
                # Broadcast to all local WebSocket connections
                await self._broadcast_to_local_connections(chat_id, message_data)
                
        except asyncio.CancelledError:
            logger.info(f"Listener task cancelled for {channel}")
        except Exception as e:
            logger.error(f"Error in listener task for {channel}: {e}")
    
    async def connect(self, websocket: WebSocket, chat_id: str) -> None:
        """
        Accept a new WebSocket connection and add to chat room.
        If this is the first connection for this room, subscribe to Redis channel.
        """
        await websocket.accept()
        
        # Add to local connections
        if chat_id not in self.active_connections:
            self.active_connections[chat_id] = set()
        
        self.active_connections[chat_id].add(websocket)
        
        # Subscribe to Redis channel if this is the first connection for this room
        if chat_id not in self.subscribed_channels:
            await self._subscribe_to_channel(chat_id)
        
        logger.info(f"Client connected to chat {chat_id}. "
                    f"Total connections in room: {len(self.active_connections[chat_id])}")
    
    async def disconnect(self, websocket: WebSocket, chat_id: str) -> None:
        """
        Remove a WebSocket connection from chat room.
        If this was the last connection, unsubscribe from Redis channel.
        """
        if chat_id in self.active_connections:
            self.active_connections[chat_id].discard(websocket)
            
            # If no more local connections, unsubscribe from Redis
            if not self.active_connections[chat_id]:
                del self.active_connections[chat_id]
                await self._unsubscribe_from_channel(chat_id)
                logger.info(f"Chat room {chat_id} is now empty, unsubscribed from Redis")
            else:
                logger.info(f"Client disconnected from chat {chat_id}. "
                           f"Remaining connections: {len(self.active_connections[chat_id])}")
    
    async def publish_message(self, chat_id: str, message: str) -> None:
        """
        Publish a message to Redis pub/sub channel.
        All instances subscribed to this channel will receive and broadcast it.
        
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
    
    async def _broadcast_to_local_connections(self, chat_id: str, message: str) -> None:
        """
        Broadcast a message to all LOCAL WebSocket connections for this room.
        This is called when we receive a message from Redis pub/sub.
        
        Args:
            chat_id: The chat room
            message: The message to send to all local connections
        """
        if chat_id not in self.active_connections:
            return
        
        disconnected = set()
        
        for connection in self.active_connections[chat_id]:
            try:
                await connection.send_text(message)
            except Exception as e:
                logger.warning(f"Failed to send message to WebSocket: {e}")
                disconnected.add(connection)
        
        # Clean up any connections that failed
        for conn in disconnected:
            self.active_connections[chat_id].discard(conn)
        
        logger.debug(f"Broadcasted to {len(self.active_connections[chat_id])} local connections in {chat_id}")
    
    async def send_personal(self, websocket: WebSocket, message: str) -> None:
        """
        Send a message to a specific connection.
        """
        try:
            await websocket.send_text(message)
        except Exception as e:
            logger.warning(f"Failed to send personal message: {e}")
    
    def get_connection_count(self, chat_id: str) -> int:
        """Get number of connections in a chat room."""
        return len(self.active_connections.get(chat_id, set()))
    
    def get_total_connections(self) -> int:
        """Get total number of active connections across all rooms."""
        return sum(len(conns) for conns in self.active_connections.values())
    
    def get_active_rooms(self) -> list:
        """Get list of chat rooms with active connections."""
        return list(self.active_connections.keys())


# Global connection manager instance (initialized in main.py on startup)
manager: Optional[ConnectionManager] = None


def create_connection_manager(redis_url: str) -> ConnectionManager:
    """Factory function to create and return a ConnectionManager instance."""
    return ConnectionManager(redis_url)

