# WebSocket Testing Guide

## The Problem You Hit

The WebSocket endpoint validates that the chat room exists **before** accepting connections. You got a 403 because `room123` didn't exist in DynamoDB yet.

## Solution: Create Chat First, Then Connect

### Step 1: Create a Chat Room

```bash
curl -X POST http://localhost/api/chats \
  -H "Content-Type: application/json" \
  -d '{"name":"Test Room","created_by":"alice"}'
```

**Response:**
```json
{"id":"chat-7c53bb2ef816","name":"Test Room","metadata":{},"created_at":"2025-12-23T22:12:34.229030"}
```

**Copy the `id` value** - this is your `CHAT_ID`

### Step 2: Add Participants

```bash
# Replace CHAT_ID with your actual chat ID
curl -X POST "http://localhost/api/chats/CHAT_ID/participants" \
  -H "Content-Type: application/json" \
  -d '{"participant_ids": ["alice", "bob", "charlie"]}'
```

### Step 3: Connect via WebSocket

Open **3 separate terminal windows** and run:

**Terminal 1 (Alice):**
```bash
websocat 'ws://localhost/api/chats/ws/CHAT_ID?user_id=alice'
```

**Terminal 2 (Bob):**
```bash
websocat 'ws://localhost/api/chats/ws/CHAT_ID?user_id=bob'
```

**Terminal 3 (Charlie):**
```bash
websocat 'ws://localhost/api/chats/ws/CHAT_ID?user_id=charlie'
```

### Step 4: Send Messages

Messages must be in JSON format:

```json
{"type":"message","content":"Hello everyone!"}
```

Just type that in any terminal and press Enter. **It will appear in all connected terminals!**

---

## Important Notes

### Message Format

**Correct:**
```json
{"type":"message","content":"Your message here"}
```

**What you'll receive:**
```json
{
  "type": "message",
  "content": "Your message here",
  "sender_id": "alice",
  "chat_id": "chat-123...",
  "timestamp": "2025-12-23T22:12:57.198004"
}
```

### System Messages

When someone joins/leaves:
```json
{
  "type": "system",
  "content": "alice joined the chat",
  "chat_id": "chat-123...",
  "timestamp": "2025-12-23T22:12:57.198004"
}
```

---

## Quick Test Script

Run this for automated setup:

```bash
./test-websocket-complete.sh
```

This will:
1. Create a chat room
2. Add participants
3. Show you the exact commands to run in 3 terminals

---

## Checking Stats

```bash
curl http://localhost/api/chats/ws/stats
```

Returns:
```json
{
  "total_connections": 3,
  "active_rooms": ["chat-7c53bb2ef816"],
  "rooms_count": 1
}
```

---

## Testing Different Scenarios

### Test 1: Room Isolation

Create two different chat rooms:

```bash
# Room 1
CHAT1=$(curl -s -X POST http://localhost/api/chats \
  -H "Content-Type: application/json" \
  -d '{"name":"Room 1","created_by":"alice"}' | jq -r '.id')

# Room 2  
CHAT2=$(curl -s -X POST http://localhost/api/chats \
  -H "Content-Type: application/json" \
  -d '{"name":"Room 2","created_by":"bob"}' | jq -r '.id')

# Add participants
curl -X POST "http://localhost/api/chats/$CHAT1/participants" \
  -H "Content-Type: application/json" \
  -d '{"participant_ids": ["alice"]}'

curl -X POST "http://localhost/api/chats/$CHAT2/participants" \
  -H "Content-Type: application/json" \
  -d '{"participant_ids": ["bob"]}'

# Connect to different rooms
websocat "ws://localhost/api/chats/ws/$CHAT1?user_id=alice"  # Terminal 1
websocat "ws://localhost/api/chats/ws/$CHAT2?user_id=bob"    # Terminal 2
```

**Result:** Messages in Room 1 won't appear in Room 2 ✅

### Test 2: Sticky Sessions

Make multiple connections and check stats:

```bash
# Terminal 1
websocat 'ws://localhost/api/chats/ws/CHAT_ID?user_id=alice'

# Terminal 2 (while Terminal 1 is still connected)
curl http://localhost/api/chats/ws/stats
```

The stats should show the same chat-service instance is handling your connections (due to `ip_hash` in NGINX).

---

## Browser Testing

Open `test_websocket.html` in your browser:

```bash
open test_websocket.html
```

This gives you a visual interface with 3 clients side-by-side!

---

## Common Issues

### 403 Forbidden

**Problem:** Chat room doesn't exist  
**Solution:** Create the chat room first (Step 1 above)

### 4004 Close Code

**Problem:** Chat ID is invalid  
**Solution:** Double-check you copied the correct chat ID

### "Connection closed"

**Problem:** Chat-service might have crashed  
**Solution:** Check logs:
```bash
docker-compose logs chat-service
```

### Messages not appearing

**Problem:** Wrong message format  
**Solution:** Use JSON format:
```json
{"type":"message","content":"text here"}
```

---

## Architecture Notes

### Current Setup (Option B: Sticky Sessions)

```
Client A (Alice) ──► NGINX (ip_hash) ──► chat-service-1
                                            ▲
Client B (Bob)   ──► NGINX (ip_hash) ──┘   │
                                            │
Messages stay in memory on each instance
```

**Limitation:** Users on `chat-service-1` can't see messages from users on `chat-service-2`.

### For Production

You'd implement **Option C: Redis Pub/Sub** to broadcast messages across all instances:

```
chat-service-1 ──┐
                 ├──► Redis Pub/Sub ──► Broadcast to all
chat-service-2 ──┘
```

This allows messages to reach all users regardless of which server instance they're connected to.

