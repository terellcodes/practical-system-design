# DynamoDB Inbox Pattern

## Overview

The **Inbox pattern** is a common DynamoDB design pattern for user-centric message views. It enables efficient queries like "Get all messages for user X" across multiple chats.

---

## Table Design

### Messages Table (Chat-Centric)
```
Primary Key:
  - chatId (HASH) - Partition key
  - createdAt (RANGE) - Sort key (timestamp in milliseconds)

Access Pattern: "Get all messages in a chat"
```

### Inbox Table (User-Centric)
```
Primary Key:
  - recipientId (HASH) - Partition key
  - createdAt (RANGE) - Sort key (timestamp in milliseconds)

Attributes:
  - chatId - Reference to the chat
  - messageId - Reference to the message

Access Pattern: "Get all messages for a user across all chats"
```

---

## How It Works

### 1. Message Creation (Fanout Write)

When a message is sent:

```python
# 1. Save to Messages table
messages_table.put_item({
    'chatId': 'chat-123',
    'createdAt': 1704067200000,
    'messageId': 'msg-abc',
    'senderId': 'alice',
    'content': 'Hello!'
})

# 2. Fanout to Inbox table for each recipient
for recipient in ['bob', 'charlie']:
    inbox_table.put_item({
        'recipientId': recipient,
        'createdAt': 1704067200000,
        'chatId': 'chat-123',
        'messageId': 'msg-abc'
    })
```

**Result:**
- 1 write to Messages table
- N writes to Inbox table (N = number of recipients)

---

### 2. Reading Messages

#### Query: "Get all messages in a chat"
```python
messages_table.query(
    KeyConditionExpression=Key('chatId').eq('chat-123'),
    ScanIndexForward=False,  # Newest first
    Limit=50
)
```

#### Query: "Get all messages for a user (across all chats)"
```python
inbox_table.query(
    KeyConditionExpression=Key('recipientId').eq('bob'),
    ScanIndexForward=False,  # Newest first
    Limit=50
)

# Returns:
# [
#   {'recipientId': 'bob', 'createdAt': 1704067300000, 'chatId': 'chat-456', 'messageId': 'msg-xyz'},
#   {'recipientId': 'bob', 'createdAt': 1704067200000, 'chatId': 'chat-123', 'messageId': 'msg-abc'},
# ]
```

---

## Trade-offs

### ✅ Advantages

1. **Fast User Inbox Queries**
   - Single query to get all messages for a user
   - No need to query multiple chats

2. **Efficient Pagination**
   - Built-in sorting by timestamp
   - Easy cursor-based pagination

3. **Scalable**
   - Each user's inbox is an independent partition
   - No hot partition issues (unless one user has millions of messages)

### ❌ Disadvantages

1. **Write Amplification**
   - One message = 1 + N writes (1 to Messages, N to Inbox)
   - For a chat with 100 participants = 101 writes!
   - **Cost:** DynamoDB charges per write

2. **Storage Duplication**
   - Message metadata stored N times (once per recipient)
   - **Mitigation:** Only store references (chatId, messageId), not full content

3. **Eventual Consistency**
   - Inbox writes happen after message write
   - Brief window where message exists but not in inboxes

---

## When to Use This Pattern

### ✅ Use When:
- You need "user inbox" / "user feed" queries
- Users need to see all their messages across chats
- Read performance is more critical than write cost
- You have moderate chat sizes (< 100 participants)

### ❌ Don't Use When:
- Very large group chats (1000+ participants) → Write amplification too high
- Budget-constrained (writes are expensive)
- Only need chat-centric views (just use Messages table)

---

## Alternative Patterns

### 1. GSI on Messages Table
```
Messages Table:
  - chatId (HASH)
  - createdAt (RANGE)
  
  GSI: recipientId-index
    - recipientId (HASH)
    - createdAt (RANGE)
```

**Problem:** How to store `recipientId` for each recipient in a single message item?
- Use a set: `recipientIds: ['bob', 'charlie']`
- But GSI can't index set members → Can't query by individual recipient!

### 2. Scan + Filter (Not Recommended)
```python
# BAD: Scans entire Messages table
messages_table.scan(
    FilterExpression=Attr('recipientIds').contains('bob')
)
```
- ❌ Slow (reads entire table)
- ❌ Expensive (charges for all scanned items)

### 3. Application-Level Join (Acceptable for small scale)
```python
# 1. Get all chats for user
chats = get_chats_for_user('bob')  # ['chat-123', 'chat-456']

# 2. Query messages for each chat
messages = []
for chat_id in chats:
    messages.extend(get_messages_for_chat(chat_id))

# 3. Sort in application
messages.sort(key=lambda m: m['createdAt'], reverse=True)
```
- ✅ No write amplification
- ❌ Multiple queries (N+1 problem)
- ❌ Application-side sorting

---

## Implementation in Our System

### On Message Send (WebSocket Handler)
```python
# 1. Get chat participants (excluding sender)
participants = repo.get_participants_for_chat(chat_id)
recipient_ids = [p.participant_id for p in participants if p.participant_id != sender_id]

# 2. Save message + fanout to inboxes
saved_message = repo.save_message(
    chat_id=chat_id,
    sender_id=sender_id,
    content=content,
    recipient_ids=recipient_ids  # Triggers inbox fanout
)
```

### On Inbox Query
```python
# Get user's inbox with pagination
result = repo.get_inbox_messages(
    recipient_id='bob',
    limit=50,
    last_evaluated_key=cursor  # For pagination
)
```

---

## Interview Talking Points

**Question:** "How would you design a messaging inbox feature with DynamoDB?"

**Answer:**
> "I'd use the **Inbox pattern** with two tables: Messages (chat-centric) and Inbox (user-centric). When a message is sent, I write once to Messages and fanout to each recipient's inbox. This creates write amplification (1 + N writes) but enables fast O(1) inbox queries with built-in sorting. For very large groups (1000+ users), I'd consider application-level joins or a streaming solution like Kafka to handle the fanout asynchronously."

**Follow-up:** "What if a group has 10,000 members?"

**Answer:**
> "Write amplification becomes prohibitive (10,001 writes per message!). Solutions:
> 1. **Async fanout:** Use DynamoDB Streams + Lambda to fanout asynchronously
> 2. **Lazy loading:** Only write to inbox when user opens the app
> 3. **Hybrid approach:** Store group messages separately, merge at read time
> 4. **Different storage:** Consider using a message queue or event stream (Kafka/Kinesis) for very large groups"

---

## Cost Analysis

### Example: 1 million messages/day, 5 participants per chat average

**Messages Table:**
- 1M writes/day

**Inbox Table:**
- 1M messages × 5 recipients = 5M writes/day

**Total:** 6M writes/day

**Cost (on-demand):**
- $1.25 per million writes
- 6M × $1.25 = **$7.50/day**
- **~$225/month** just for writes

**Optimization:**
- Use provisioned capacity if predictable load
- Batch writes when possible
- Consider async fanout for cost savings

---

## Summary

The Inbox pattern is a powerful DynamoDB design for user-centric message views, trading write cost for read performance. It's perfect for moderate-scale chat applications but requires careful consideration for very large group sizes. Understanding this pattern demonstrates strong NoSQL data modeling skills in interviews! 🎯

