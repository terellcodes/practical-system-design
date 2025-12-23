"""
WebSocket Connection Manager

Handles real-time WebSocket connections for chat rooms.
This is Option A: Single instance - all connections managed in memory.

For production (Option C), you'd use Redis pub/sub to broadcast
messages across multiple chat-service instances.
"""

import logging
from typing import Dict, Set
from fastapi import WebSocket

logger = logging.getLogger(__name__)


class ConnectionManager:
    """
    Manages WebSocket connections for chat rooms.
    
    Data structure:
        chat_id -> Set of WebSocket connections
    
    Example:
        {
            "chat-abc123": {ws1, ws2, ws3},
            "chat-def456": {ws4, ws5},
        }
    """
    
    def __init__(self):
        # chat_id -> set of active WebSocket connections
        self.active_connections: Dict[str, Set[WebSocket]] = {}
    
    async def connect(self, websocket: WebSocket, chat_id: str) -> None:
        """
        Accept a new WebSocket connection and add to chat room.
        """
        await websocket.accept()
        
        if chat_id not in self.active_connections:
            self.active_connections[chat_id] = set()
        
        self.active_connections[chat_id].add(websocket)
        
        logger.info(f"Client connected to chat {chat_id}. "
                    f"Total connections in room: {len(self.active_connections[chat_id])}")
    
    def disconnect(self, websocket: WebSocket, chat_id: str) -> None:
        """
        Remove a WebSocket connection from chat room.
        """
        if chat_id in self.active_connections:
            self.active_connections[chat_id].discard(websocket)
            
            # Clean up empty rooms
            if not self.active_connections[chat_id]:
                del self.active_connections[chat_id]
                logger.info(f"Chat room {chat_id} is now empty, removed from memory")
            else:
                logger.info(f"Client disconnected from chat {chat_id}. "
                           f"Remaining connections: {len(self.active_connections[chat_id])}")
    
    async def broadcast(self, chat_id: str, message: str, exclude: WebSocket = None) -> None:
        """
        Send a message to all connections in a chat room.
        
        Args:
            chat_id: The chat room to broadcast to
            message: The message to send
            exclude: Optional WebSocket to exclude (e.g., the sender)
        """
        if chat_id not in self.active_connections:
            logger.warning(f"Attempted to broadcast to non-existent chat {chat_id}")
            return
        
        disconnected = set()
        
        for connection in self.active_connections[chat_id]:
            if connection == exclude:
                continue
            try:
                await connection.send_text(message)
            except Exception as e:
                logger.warning(f"Failed to send message: {e}")
                disconnected.add(connection)
        
        # Clean up any connections that failed
        for conn in disconnected:
            self.active_connections[chat_id].discard(conn)
    
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


# Global connection manager instance
manager = ConnectionManager()

