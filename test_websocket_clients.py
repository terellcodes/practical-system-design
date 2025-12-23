#!/usr/bin/env python3
"""
WebSocket Multi-Client Test Script

Tests multiple clients connecting to the same chat room and broadcasting messages.

Usage:
    pip install websockets asyncio
    python test_websocket_clients.py
"""

import asyncio
import websockets
import json
from datetime import datetime


async def client_session(user_id: str, chat_id: str, messages_to_send: list):
    """
    Simulates a single WebSocket client.
    
    Args:
        user_id: User identifier
        chat_id: Chat room identifier
        messages_to_send: List of messages this client will send
    """
    uri = f"ws://localhost/api/chats/ws/chat/{chat_id}?user_id={user_id}"
    
    try:
        async with websockets.connect(uri) as websocket:
            print(f"[{user_id}] Connected to {chat_id}")
            
            # Task to receive messages
            async def receive_messages():
                try:
                    while True:
                        message = await websocket.recv()
                        timestamp = datetime.now().strftime("%H:%M:%S")
                        print(f"[{user_id}] ({timestamp}) Received: {message}")
                except websockets.exceptions.ConnectionClosed:
                    print(f"[{user_id}] Connection closed")
            
            # Task to send messages
            async def send_messages():
                for msg in messages_to_send:
                    await asyncio.sleep(2)  # Wait 2 seconds between messages
                    await websocket.send(msg)
                    print(f"[{user_id}] Sent: {msg}")
                
                # Keep connection alive for a bit to receive other messages
                await asyncio.sleep(5)
            
            # Run both tasks concurrently
            await asyncio.gather(
                receive_messages(),
                send_messages(),
                return_exceptions=True
            )
            
    except Exception as e:
        print(f"[{user_id}] Error: {e}")


async def test_multiple_clients():
    """
    Test scenario: 3 users in the same chat room sending messages.
    """
    print("=" * 60)
    print("WebSocket Multi-Client Test")
    print("=" * 60)
    print()
    
    # Define what each client will say
    alice_messages = [
        "Hello everyone!",
        "How's it going?",
    ]
    
    bob_messages = [
        "Hey Alice!",
        "I'm doing great, thanks!",
    ]
    
    charlie_messages = [
        "Hi team!",
        "This WebSocket test is working!",
    ]
    
    # Create 3 clients for the same chat room
    chat_id = "room123"
    
    # Run all clients concurrently
    await asyncio.gather(
        client_session("alice", chat_id, alice_messages),
        client_session("bob", chat_id, bob_messages),
        client_session("charlie", chat_id, charlie_messages),
    )
    
    print()
    print("=" * 60)
    print("Test completed!")
    print("=" * 60)


async def test_different_rooms():
    """
    Test scenario: Users in different chat rooms (messages shouldn't cross).
    """
    print("=" * 60)
    print("Testing Room Isolation")
    print("=" * 60)
    print()
    
    # Alice and Bob in room123
    # Charlie in room456 (should not see Alice/Bob messages)
    
    await asyncio.gather(
        client_session("alice", "room123", ["Message in room123 from Alice"]),
        client_session("bob", "room123", ["Message in room123 from Bob"]),
        client_session("charlie", "room456", ["Message in room456 from Charlie"]),
    )
    
    print()
    print("Room isolation test completed!")
    print("Charlie should NOT have seen Alice/Bob messages")


async def check_stats():
    """
    Check WebSocket connection statistics.
    """
    import aiohttp
    
    async with aiohttp.ClientSession() as session:
        async with session.get('http://localhost/api/chats/ws/stats') as response:
            stats = await response.json()
            print("\n" + "=" * 60)
            print("WebSocket Stats")
            print("=" * 60)
            print(json.dumps(stats, indent=2))


if __name__ == "__main__":
    print("Choose a test:")
    print("1. Multiple clients in same room")
    print("2. Different rooms (isolation test)")
    print("3. Check current stats")
    
    choice = input("\nEnter choice (1-3): ").strip()
    
    if choice == "1":
        asyncio.run(test_multiple_clients())
    elif choice == "2":
        asyncio.run(test_different_rooms())
    elif choice == "3":
        asyncio.run(check_stats())
    else:
        print("Invalid choice")

