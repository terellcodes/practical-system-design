# Practical System Design

## Brainstorm Notes 
- **Diagram So Far**
- **Key Deep Dives**
  - Supporting real-time messaging over WebSocket
  - Supporting offline syncs with inbox
  - Supporting media in messages with blob storage uploads
- **Technology Learnings**
  - DynamoDB
    - Primary key
    - GSI, LSI
  - Lambda

## WebSocket Implementation

### 1. Connection Management & Auto-Reconnect

**Initial Connection:**
```typescript
// use-websocket.ts:276-293
useEffect(() => {
  if (!userId) return;

  shouldReconnect.current = true;
  connect();

  return () => {
    shouldReconnect.current = false; // Prevent reconnect on unmount
    if (reconnectTimeout.current) {
      clearTimeout(reconnectTimeout.current);
    }
    if (wsRef.current) {
      wsRef.current.close();
    }
  };
}, [userId, connect]);
```

**Stateful Connections in Chat Service**
```python
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
```

**Auto-Reconnect with Exponential Backoff:**
```typescript
// use-websocket.ts:249-272
ws.onclose = (event) => {
  setIsConnected(false);
  setSubscribedChats([]);

  // Auto-reconnect on unexpected disconnect
  if (!event.wasClean && shouldReconnect.current &&
      reconnectAttempts.current < MAX_RECONNECT_ATTEMPTS) {
    const delay = BASE_RECONNECT_DELAY * Math.pow(2, reconnectAttempts.current);

    reconnectTimeout.current = setTimeout(() => {
      reconnectAttempts.current++;
      connect();
    }, delay);
  }
};
```

### 2. Context Provider Pattern

**Global WebSocket Provider:**
```tsx
// contexts/websocket-context.tsx:22-31
export function WebSocketProvider({ children }: WebSocketProviderProps) {
  const { userId } = useChatStore();
  const ws = useUserWebSocket(userId);

  return (
    <WebSocketContext.Provider value={ws}>
      {children}
    </WebSocketContext.Provider>
  );
}
```

**Usage Pattern:**
```tsx
// chat/layout.tsx:113-123
export default function ChatLayout({ children }) {
  return (
    <WebSocketProvider>
      <ChatLayoutContent>{children}</ChatLayoutContent>
    </WebSocketProvider>
  );
}
```

3. Message Persistence with Zustand

The application uses **Zustand with custom persistence** to store messages locally, ensuring offline access and performance:

```tsx
export const useChatStore = create<ChatState>()(
  persist(
    (set, get) => ({
        userId: ...,
        messagesByChat: ...,
        chats: [],
        setChats: ...,
        addChat: ...,
        addMessage: ...,
        ...
    }),
    {
        name: "chat-storage", // logical name; actual storage keys are custom below
        storage: createNamespacedStorage(),
        partialize: (state) => ({
            userId: state.userId,
            messagesByChat: state.messagesByChat,
        })
    }
  )
)
```

**Custom Namespaced Storage:**
```typescript
// store/chat-store.ts:137-198
function createNamespacedStorage(): PersistStorage<PersistedShape> {
  return {
    getItem: () => {
      const userId = sessionStorage.getItem(USER_KEY);
      const rawMessages = userId !== null ? localStorage.getItem(messagesKey(userId)) : null;
      
      let messagesByChat: Record<string, Message[]> = {};
      if (rawMessages) {
        const parsed = JSON.parse(rawMessages);
        messagesByChat = parsed.messagesByChat || {};
      }
      
      return { state: { userId, messagesByChat }, version: 0 };
    },
    setItem: (name, value) => {
      const { userId, messagesByChat } = value?.state || {};
      
      // Store userId in sessionStorage
      if (userId) sessionStorage.setItem(USER_KEY, userId);
      
      // Store messages in user-namespaced localStorage key
      const key = messagesKey(userId);
      localStorage.setItem(key, JSON.stringify({ messagesByChat }));
    }
  };
}
```

### 4. Sending abd Delivering Messages

## Message Flow Architecture

### Message Delivery Flow Diagram

```
┌─────────────┐                                   ┌─────────────┐         ┌─────────────┐
│   Alice     │                                   │     Bob     │         │   Charlie   │
│  (Sender)   │                                   │(Participant)│         │(Participant)│
└─────┬───────┘                                   └─────┬───────┘         └─────┬───────┘
      │                                                 │                       │
      │ 1. WebSocket                                    │ 6. WebSocket          │ 6. WebSocket
      │    Message                                      │    Connection         │    Connection  
      │                                                 │                       │
      ▼                                                 ▼                       ▼
┌─────────────────────────────────┐           ┌─────────────────────────────────────────────┐
│      Chat Service Instance 1    │           │         Chat Service Instance 2             │
│ ┌─────────────────────────────┐ │           │ ┌─────────────────────────────────────────┐ │
│ │     Connection Manager      │ │           │ │        Connection Manager               │ │
│ │                             │ │           │ │                                         │ │
│ │ user_connections = {        │ │           │ │ user_connections = {                    │ │
│ │   "alice": <WebSocket>      │ │           │ │   "bob": <WebSocket>,                   │ │
│ │ }                           │ │           │ │   "charlie": <WebSocket>                │ │
│ │                             │ │           │ │ }                                       │ │
│ │ user_subscriptions = {      │ │           │ │                                         │ │
│ │   "alice": {"chat-abc"}     │ │           │ │ user_subscriptions = {                  │ │
│ │ }                           │ │           │ │   "bob": {"chat-abc"},                  │ │
│ │                             │ │           │ │   "charlie": {"chat-abc"}               │ │
│ │ user_pubsubs = {            │ │           │ │ }                                       │ │
│ │   "alice": <PubSub>         │ │           │ │                                         │ │
│ │ }                           │ │           │ │ user_pubsubs = {                        │ │
│ │                             │ │           │ │   "bob": <PubSub>,                      │ │
│ │ user_tasks = {              │ │           │ │   "charlie": <PubSub>                   │ │
│ │   "alice": <AsyncTask>      │ │           │ │ }                                       │ │
│ │ }                           │ │           │ │                                         │ │
│ └─────────────────────────────┘ │           │ │ user_tasks = {                          │ │
└─────────────┬───────────────────┘           │ │   "bob": <AsyncTask>,                   │ │
              │                               │ │   "charlie": <AsyncTask>                │ │
              │ 2. Write Message              │ │ }                                       │ │
              ▼                               │ └─────────────────────────────────────────┘ │
┌─────────────────────────────────────────────┴─────────────────────────────────────────────┐
│                                    DynamoDB                                               │
│  ┌─────────────────┐              ┌─────────────────────────┐                             │
│  │ Messages Table  │              │     Inbox Table         │                             │
│  │                 │              │                         │                             │
│  │ messageId: 123  │              │ recipientId: bob        │                             │
│  │ chatId: abc     │    3. Inbox  │ messageId: 123          │                             │
│  │ content: "hi"   │    ──Fanout──▶ createdAt: timestamp    │                             │
│  │ senderId: alice │              │                         │                             │
│  │ createdAt: ts   │              │ recipientId: charlie    │                             │
│  │                 │              │ messageId: 123          │                             │
│  │                 │              │ createdAt: timestamp    │                             │
│  └─────────────────┘              └─────────────────────────┘                             │
└─────────────┬─────────────────────────────────────────────────────────────────────────────┘
              │
              │ 4. Publish to Redis
              ▼
┌─────────────────────────────────────────────────────────────────────────────────────────────┐
│                                    Redis Pub/Sub                                            │
│                                                                                             │
│                           Channel: "chat:chat-abc"                                          │
│                           Message: {                                                        │
│                             "type": "message",                                              │
│                             "message_id": "123",                                            │
│                             "content": "hi",                                                │
│                             "sender_id": "alice",                                           │
│                             "chat_id": "chat-abc"                                           │
│                           }                                                                 │
└─────────────┬───────────────────────────────────────────────────────────────────────────────┘
              │
              │ 5. Fanout to Subscribers (Cross-Instance)
              ▼
┌─────────────────────────────────────────────────────────────────────────────────────────────┐
│                           User PubSub Listeners (Distributed)                               │
│                                                                                             │
│ Instance 1:                               Instance 2:                                       │
│ ┌─────────────┐                          ┌─────────────┐    ┌─────────────┐                 │
│ │Alice PubSub │                          │ Bob PubSub  │    │Charlie PubSub│                │
│ │             │                          │             │    │             │                 │
│ │Subscribed:  │                          │Subscribed:  │    │Subscribed:  │                 │
│ │"chat:abc"   │                          │"chat:abc"   │    │"chat:abc"   │                 │
│ │             │                          │             │    │             │                 │
│ │Task: Listen │                          │Task: Listen │    │Task: Listen │                 │
│ │& Forward    │                          │& Forward    │    │& Forward    │                 │
│ └─────┬───────┘                          └─────┬───────┘    └─────┬───────┘                 │
└───────┼────────────────────────────────────────┼──────────────────┼───────────────────────┘
        │                                        │                  │
        │ 6. Forward to                          │ 6. Forward to    │ 6. Forward to
        │    WebSocket                           │    WebSocket     │    WebSocket
        ▼                                        ▼                  ▼
┌─────────────┐                          ┌─────────────┐    ┌─────────────┐
│   Alice     │                          │     Bob     │    │   Charlie   │
│ ┌─────────┐ │                          │ ┌─────────┐ │    │ ┌─────────┐ │
│ │         │ │                          │ │         │ │    │ │         │ │
│ │Client   │ │                          │ │Client   │ │    │ │Client   │ │
│ │         │ │                          │ │         │ │    │ │         │ │
│ │Displays:│ │                          │ │Displays:│ │    │ │Displays:│ │
│ │ "hi"    │ │                          │ │ "hi"    │ │    │ │ "hi"    │ │
│ │(own msg)│ │                          │ │(from    │ │    │ │(from    │ │
│ │         │ │                          │ │ alice)  │ │    │ │ alice)  │ │
│ └─────────┘ │                          │ └─────────┘ │    │ └─────────┘ │
└─────────────┘                          └─────────────┘    └─────────────┘
      │                                        │                  │
      │ 7. Acknowledge                         │ 7. Acknowledge   │ 7. Acknowledge
      │    Message                             │    Message       │    Message
      ▼                                        ▼                  ▼
   
   WebSocket.send({                       WebSocket.send({      WebSocket.send({
     type: "ack-message-received",          type: "ack...",       type: "ack...",
     message_id: "123"                      message_id: "123"     message_id: "123"
   })                                     })                    })
```

### Step-by-Step Message Flow

1. **Alice sends WebSocket message** → Chat Service receives
2. **Chat Service writes to Messages table** → Full message stored in DynamoDB
3. **Inbox fanout** → Create inbox record for Bob and Charlie (recipients)
4. **Publish to Redis** → Message published to "chat:chat-abc" channel
5. **PubSub fanout** → All users subscribed to "chat:chat-abc" receive message
6. **Listener tasks forward** → Each user's background task sends to their WebSocket


**Text Message Sending:**
```typescript
// use-websocket.ts:296-315
const sendMessage = useCallback((chatId: string, content: string) => {
  if (!wsRef.current || wsRef.current.readyState !== WebSocket.OPEN) {
    console.error("WebSocket not connected");
    return;
  }

  wsRef.current.send(JSON.stringify({
    type: "message",
    chat_id: chatId,
    content,
  }));

  bumpChat(chatId); // Move chat to top
}, [bumpChat]);
```

**Usage in Chat Page:**
```typescript
// chat/[chatId]/page.tsx:44
sendMessage(chatId, content);
```

**Real-time Message Handling:**
```typescript
// use-websocket.ts:148-174
case "message": {
  const message: Message = {
    message_id: data.message_id,
    chat_id: data.chat_id,
    sender_id: data.sender_id,
    content: data.content,
    created_at: data.created_at,
    type: "message",
    upload_status: data.upload_status,
    s3_bucket: data.s3_bucket,
    s3_key: data.s3_key,
  };

  addMessage(data.chat_id, message);
  bumpChat(data.chat_id);

  // Send acknowledgment
  wsRef.current.send(JSON.stringify({
    type: "ack-message-received",
    message_id: data.message_id,
  }));
  break;
}
```

### 6. Inbox Synchronization

**Sync on Connection:**
```typescript
// use-websocket.ts:236-241
ws.onopen = () => {
  console.log("WebSocket connection opened");
  setIsConnected(true);
  reconnectAttempts.current = 0;
  syncInbox(); // Sync missed messages
};
```


### Offline Sync Flow Diagram

```
┌─────────────┐                    ┌─────────────────────────────┐
│   Client    │                    │       Chat Service          │
│ (reconnects)│                    │                             │
└─────┬───────┘                    └─────┬───────────────────────┘
      │                                  │
      │ 1. WebSocket Connect             │
      │──────────────────────────────────▶
      │                                  │
      │ 2. HTTP GET /inbox/sync          │ 3. Query Inbox Table
      │──────────────────────────────────▶─────────────────┐
      │                                  │                 │
      │                                  │                 ▼
      │                                  │   ┌─────────────────────┐
      │                                  │   │   DynamoDB Inbox    │
      │                                  │   │                     │
      │                                  │   │ recipientId: alice  │
      │                                  │   │ messageId: [1,2,3]  │
      │                                  │   └─────────────────────┘
      │                                  │                 │
      │                                  │ 4. Hydrate      │
      │                                  │    Messages     │
      │                                  │◀────────────────┘
      │                                  │                 │
      │                                  │                 ▼
      │                                  │   ┌─────────────────────┐
      │ 5. Return Messages               │   │  DynamoDB Messages  │
      │◀─────────────────────────────────│   │                     │
      │                                  │   │ messageId: 1        │
      │ 6. Client stores in Zustand      │   │ content: "hello"    │
      │    localStorage                  │   │ chatId: abc         │
      │                                  │   │                     │
      │ 7. Acknowledge each message      │   │ messageId: 2,3...   │
      │──────────────────────────────────▶   └─────────────────────┘
      │                                  │
      │                                  │ 8. Delete from Inbox
      │                                  │
```


**Inbox Sync Implementation:**
```typescript
// use-websocket.ts:95-134
const syncInbox = useCallback(async () => {
  if (!userId || !wsRef.current || wsRef.current.readyState !== WebSocket.OPEN) return;

  setIsSyncing(true);
  const response = await chatApi.syncInbox(userId);

  for (const item of response.items || []) {
    const message = { /* convert to Message format */ };
    addMessage(item.chat_id, message);
    bumpChat(item.chat_id);

    // Acknowledge each synced message
    wsRef.current.send(JSON.stringify({
      type: "ack-message-received",
      message_id: item.message_id,
    }));
  }
  setIsSyncing(false);
}, [userId, addMessage, bumpChat]);
```

### 7. Chat Subscription Management

**Subscribe to New Chat:**
```typescript
// use-websocket.ts:318-330
const subscribeToChat = useCallback((chatId: string) => {
  if (!wsRef.current || wsRef.current.readyState !== WebSocket.OPEN) return;

  wsRef.current.send(JSON.stringify({
    type: "subscribe",
    chat_id: chatId,
  }));
}, []);
```

**Usage After Chat Creation:**
```typescript
// chat/layout.tsx:57-58
// Subscribe to the new chat via WebSocket
subscribeToChat(newChat.id);
```

**Unsubscribe from Chat:**
```typescript
// use-websocket.ts:333-345
const unsubscribeFromChat = useCallback((chatId: string) => {
  if (!wsRef.current || wsRef.current.readyState !== WebSocket.OPEN) return;

  wsRef.current.send(JSON.stringify({
    type: "unsubscribe",
    chat_id: chatId,
  }));
}, []);
```





