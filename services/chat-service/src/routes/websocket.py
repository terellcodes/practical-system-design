"""
WebSocket API endpoints for real-time chat.

Usage:
    ws://localhost/api/chats/ws/{chat_id}
    
    Client connects, then sends/receives JSON messages:
    
    Send: {"type": "message", "content": "Hello!", "sender_id": "user-123"}
    Receive: {"type": "message", "content": "Hello!", "sender_id": "user-123", "chat_id": "..."}
"""

import json
import logging
from datetime import datetime

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query

from src.websocket import manager
from src.repositories.dynamodb import DynamoDBRepository

logger = logging.getLogger(__name__)

router = APIRouter(tags=["WebSocket"])


@router.websocket("/ws/{chat_id}")
async def websocket_chat(
    websocket: WebSocket,
    chat_id: str,
    user_id: str = Query(..., description="User ID connecting to chat"),
):
    """
    WebSocket endpoint for real-time chat.
    
    Connect: ws://host/chats/ws/{chat_id}?user_id={user_id}
    
    Message format (send):
        {"type": "message", "content": "Hello world!"}
    
    Message format (receive):
        {"type": "message", "content": "Hello!", "sender_id": "user-123", 
         "chat_id": "chat-abc", "timestamp": "2024-01-15T10:30:00"}
    
    System messages:
        {"type": "system", "content": "user-123 joined the chat"}
    """
    
    # Accept connection first (required before any WebSocket operations)
    await manager.connect(websocket, chat_id)
    
    # Then verify chat exists
    repo = DynamoDBRepository()
    chat = repo.get_chat(chat_id)
    
    if not chat:
        # Now we can properly close the accepted connection
        await websocket.close(code=4004, reason=f"Chat {chat_id} not found")
        manager.disconnect(websocket, chat_id)
        return
    
    try:
        # Announce user joined
        join_message = json.dumps({
            "type": "system",
            "content": f"{user_id} joined the chat",
            "chat_id": chat_id,
            "timestamp": datetime.utcnow().isoformat(),
        })
        await manager.broadcast(chat_id, join_message)
        
        # Handle incoming messages
        while True:
            data = await websocket.receive_text()
            
            try:
                message = json.loads(data)
                msg_type = message.get("type", "message")
                content = message.get("content", "")
                
                if msg_type == "message" and content:
                    # Broadcast message to all in chat room
                    outgoing = json.dumps({
                        "type": "message",
                        "content": content,
                        "sender_id": user_id,
                        "chat_id": chat_id,
                        "timestamp": datetime.utcnow().isoformat(),
                    })
                    await manager.broadcast(chat_id, outgoing)
                    logger.info(f"Message in {chat_id} from {user_id}: {content[:50]}...")
                    
                elif msg_type == "ping":
                    # Respond to ping with pong
                    await manager.send_personal(websocket, json.dumps({
                        "type": "pong",
                        "timestamp": datetime.utcnow().isoformat(),
                    }))
                    
            except json.JSONDecodeError:
                await manager.send_personal(websocket, json.dumps({
                    "type": "error",
                    "content": "Invalid JSON format",
                }))
                
    except WebSocketDisconnect:
        manager.disconnect(websocket, chat_id)
        
        # Announce user left
        leave_message = json.dumps({
            "type": "system",
            "content": f"{user_id} left the chat",
            "chat_id": chat_id,
            "timestamp": datetime.utcnow().isoformat(),
        })
        await manager.broadcast(chat_id, leave_message)
        
        logger.info(f"User {user_id} disconnected from chat {chat_id}")


@router.get("/ws/stats")
async def websocket_stats():
    """
    Get WebSocket connection statistics.
    
    Useful for monitoring and debugging.
    """
    return {
        "total_connections": manager.get_total_connections(),
        "active_rooms": manager.get_active_rooms(),
        "rooms_count": len(manager.get_active_rooms()),
    }

