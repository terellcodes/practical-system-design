"""
WebSocket API endpoints for real-time chat.

User-Centric Model:
    - Each user has ONE WebSocket connection
    - Receives messages from ALL chats they're part of
    - Connection persists across chat navigation

Usage:
    ws://localhost/api/chats/ws?user_id={user_id}
    
    Client connects once, then sends/receives JSON messages for any chat:
    
    Send: {"type": "message", "chat_id": "chat-abc", "content": "Hello!"}
    Receive: {"type": "message", "content": "Hello!", "sender_id": "user-123", "chat_id": "chat-abc"}
"""

import json
import logging
from datetime import datetime

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query

from src import websocket as ws_module
from src.repositories.dynamodb import DynamoDBRepository

logger = logging.getLogger(__name__)

router = APIRouter(tags=["WebSocket"])


@router.websocket("/ws")
async def websocket_user(
    websocket: WebSocket,
    user_id: int = Query(..., description="User ID connecting"),
):
    """
    User-centric WebSocket endpoint for real-time chat.
    
    Connect: ws://host/chats/ws?user_id={user_id}
    
    On connect:
        - Subscribes to ALL chats the user is part of
        - Receives messages from any of those chats
    
    Message format (send):
        {"type": "message", "chat_id": "chat-abc", "content": "Hello world!"}
    
    Message format (receive):
        {"type": "message", "content": "Hello!", "sender_id": "user-123", 
         "chat_id": "chat-abc", "created_at": "2024-01-15T10:30:00"}
    
    System messages:
        {"type": "system", "content": "user-123 joined the chat", "chat_id": "chat-abc"}
    
    Subscribe to new chat (after joining):
        {"type": "subscribe", "chat_id": "chat-new"}
    
    Unsubscribe from chat (after leaving):
        {"type": "unsubscribe", "chat_id": "chat-old"}
    """
    
    repo = DynamoDBRepository()
    
    # Get all chats this user is part of
    chat_ids = repo.get_chats_for_participant(user_id)
    logger.info(f"User {user_id} is part of {len(chat_ids)} chats: {chat_ids}")
    
    # Connect and subscribe to all chat channels
    await ws_module.manager.connect(websocket, user_id, chat_ids)
    
    try:
        # Send connection confirmation with list of subscribed chats
        await ws_module.manager.send_personal(user_id, json.dumps({
            "type": "connected",
            "user_id": user_id,
            "subscribed_chats": chat_ids,
            "timestamp": datetime.utcnow().isoformat(),
        }))
        
        # Handle incoming messages
        while True:
            data = await websocket.receive_text()
            
            try:
                message = json.loads(data)
                msg_type = message.get("type", "message")
                
                if msg_type == "message":
                    # Regular chat message
                    chat_id = message.get("chat_id")
                    content = message.get("content", "")
                    sender_username = message.get("sender_username", "")
                    sender_name = message.get("sender_name", "")
                    
                    if not chat_id:
                        await ws_module.manager.send_personal(user_id, json.dumps({
                            "type": "error",
                            "content": "chat_id is required for messages",
                        }))
                        continue
                    
                    if not content:
                        continue
                    
                    # Verify user is participant in this chat
                    if chat_id not in ws_module.manager.get_user_subscriptions(user_id):
                        await ws_module.manager.send_personal(user_id, json.dumps({
                            "type": "error",
                            "content": f"Not subscribed to chat {chat_id}",
                        }))
                        continue
                    
                    # Get chat participants for inbox fanout
                    participants = repo.get_participants_for_chat(chat_id)
                    recipient_ids = [p.participant_id for p in participants if p.participant_id != user_id]

                    # Write message to DynamoDB (Messages + Inbox tables)
                    saved_message = repo.save_message(
                        chat_id, user_id, content, recipient_ids,
                        sender_username=sender_username,
                        sender_name=sender_name,
                    )
                    
                    # Publish message to Redis (all subscribed users will receive)
                    outgoing = json.dumps({
                        "type": "message",
                        "message_id": saved_message['message_id'],
                        "content": content,
                        "sender_id": user_id,
                        "sender_username": sender_username,
                        "sender_name": sender_name,
                        "chat_id": chat_id,
                        "created_at": saved_message['created_at'],
                    })
                    await ws_module.manager.publish_message(chat_id, outgoing)
                    logger.info(f"Message {saved_message['message_id']} in {chat_id} from {sender_username or user_id}: {content[:50]}...")
                
                elif msg_type == "subscribe":
                    # Dynamically subscribe to a new chat
                    chat_id = message.get("chat_id")
                    if chat_id:
                        success = await ws_module.manager.subscribe_to_chat(user_id, chat_id)
                        await ws_module.manager.send_personal(user_id, json.dumps({
                            "type": "subscribed",
                            "chat_id": chat_id,
                            "success": success,
                        }))
                
                elif msg_type == "unsubscribe":
                    # Dynamically unsubscribe from a chat
                    chat_id = message.get("chat_id")
                    if chat_id:
                        success = await ws_module.manager.unsubscribe_from_chat(user_id, chat_id)
                        await ws_module.manager.send_personal(user_id, json.dumps({
                            "type": "unsubscribed",
                            "chat_id": chat_id,
                            "success": success,
                        }))
                
                elif msg_type == "ack-message-received":
                    # Acknowledge message receipt (removes from inbox)
                    message_id = message.get("message_id")
                    if message_id:
                        repo.delete_inbox_message(user_id, message_id)
                        logger.debug(f"Acknowledged message {message_id} for {user_id}")
                
                elif msg_type == "ping":
                    # Respond to ping with pong
                    await ws_module.manager.send_personal(user_id, json.dumps({
                        "type": "pong",
                        "timestamp": datetime.utcnow().isoformat(),
                    }))
                    
            except json.JSONDecodeError:
                await ws_module.manager.send_personal(user_id, json.dumps({
                    "type": "error",
                    "content": "Invalid JSON format",
                }))
            except Exception as err:
                logger.error(f"Error processing message from {user_id}: {err}")
                await ws_module.manager.send_personal(user_id, json.dumps({
                    "type": "error",
                    "content": str(err),
                }))
                
    except WebSocketDisconnect:
        await ws_module.manager.disconnect(user_id)
        logger.info(f"User {user_id} disconnected")


@router.get("/ws/stats")
async def websocket_stats():
    """
    Get WebSocket connection statistics.
    
    Useful for monitoring and debugging.
    """
    return {
        "total_connections": ws_module.manager.get_total_connections(),
        "connected_users": ws_module.manager.get_connected_users(),
    }
