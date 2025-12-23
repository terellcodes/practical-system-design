#!/bin/bash

# Complete WebSocket Test with Chat Room Setup
# This script creates a chat room and then shows how to connect via WebSocket

echo "========================================"
echo "WebSocket Testing Guide"
echo "========================================"
echo ""

# Step 1: Create a chat room
echo "Step 1: Creating a chat room..."
CHAT_RESPONSE=$(curl -s -X POST http://localhost/api/chats \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Test Room",
    "created_by": "alice"
  }')

CHAT_ID=$(echo $CHAT_RESPONSE | grep -o '"id":"[^"]*"' | cut -d'"' -f4)

if [ -z "$CHAT_ID" ]; then
  echo "❌ Failed to create chat room. Is the service running?"
  echo "Response: $CHAT_RESPONSE"
  exit 1
fi

echo "✅ Chat room created with ID: $CHAT_ID"
echo ""

# Step 2: Add participants
echo "Step 2: Adding participants to chat room..."
curl -s -X POST "http://localhost/api/chats/$CHAT_ID/participants" \
  -H "Content-Type: application/json" \
  -d '{"participant_ids": ["alice", "bob", "charlie"]}' > /dev/null

echo "✅ Added alice, bob, and charlie as participants"
echo ""

# Step 3: Instructions to connect
echo "========================================"
echo "Now open 3 SEPARATE terminal windows and run these commands:"
echo "========================================"
echo ""
echo "Terminal 1 (Alice):"
echo "  websocat 'ws://localhost/api/chats/ws/$CHAT_ID?user_id=alice'"
echo ""
echo "Terminal 2 (Bob):"
echo "  websocat 'ws://localhost/api/chats/ws/$CHAT_ID?user_id=bob'"
echo ""
echo "Terminal 3 (Charlie):"
echo "  websocat 'ws://localhost/api/chats/ws/$CHAT_ID?user_id=charlie'"
echo ""
echo "========================================"
echo "Then type messages in any terminal!"
echo "Note: Messages must be in JSON format:"
echo '  {"type":"message","content":"Hello everyone!"}'
echo "========================================"
echo ""
echo "To check WebSocket stats:"
echo "  curl http://localhost/api/chats/ws/stats"
echo ""
echo "Chat ID: $CHAT_ID"

