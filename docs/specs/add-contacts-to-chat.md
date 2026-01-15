# Spec: Add Contacts to Chat

## Summary
Enable users to add contacts to a chat immediately after creation via a contact picker modal. Includes a unified notification system to notify users when they're added to chats.

## User Stories

**As a user creating a chat**, I want to add contacts to the chat right after creating it, so I can start conversations with multiple people immediately.

**As a user**, I want to be notified when someone adds me to a chat, so I know about new conversations I'm part of.

## Requirements

### Functional Requirements

1. **Contact Loading**
   - Contacts must be fetched when the chat page loads
   - Contacts available for selection without additional API calls

2. **Chat Creation Flow**
   - After creating a chat, contact picker modal opens automatically
   - User can select multiple contacts via checkboxes
   - User can search/filter contacts by name or username
   - User can skip adding contacts (proceeds to empty chat)
   - Selected contacts are added as chat participants

3. **Realtime Notifications**
   - When added to a chat, user receives toast notification
   - Notification shows chat name and auto-dismisses after 5 seconds
   - Chat appears in user's sidebar immediately (no refresh needed)
   - User is automatically subscribed to chat's WebSocket channel

### Non-Functional Requirements

1. **Architecture**
   - Unified notification system supporting multiple notification types
   - Future-proof for super app (games, social, etc.)
   - Clean separation between notification display and business logic

2. **Performance**
   - Contacts fetched in parallel with chats on page load
   - No additional API calls when opening contact picker

## Technical Design

### Frontend Components

| Component | Location | Purpose |
|-----------|----------|---------|
| `notification-store.ts` | `src/store/` | Unified notification queue |
| `contact-store.ts` | `src/store/` | Contact state management |
| `NotificationCenter` | `src/components/notifications/` | Renders all notifications |
| `ContactPickerDialog` | `src/components/chat/` | Contact selection modal |

### Backend Changes

| File | Change |
|------|--------|
| `chat_service.py` | Publish `chat_participant_added` event after adding participants |

### API Contracts

**Existing**: `GET /api/contacts` - Returns user's contacts with enriched user data

**Existing**: `POST /api/chats/{chat_id}/participants` - Adds participants to chat

**New WebSocket Event**: `chat_participant_added`
```json
{
  "type": "chat_participant_added",
  "data": {
    "chat_id": "chat-abc123",
    "chat_name": "Team Discussion",
    "added_by_user_id": 42
  }
}
```

### Data Models

**Notification** (frontend):
```typescript
interface Notification {
  id: string;
  type: string;
  source: "chat" | "contacts" | "games" | "social" | "system";
  priority: "low" | "medium" | "high" | "critical";
  category: string;
  title: string;
  message: string;
  data: Record<string, unknown>;
  actions?: NotificationAction[];
  createdAt: Date;
  expiresAt?: Date;
}
```

**ContactWithUser** (existing):
```typescript
interface ContactWithUser {
  contact_id: number;
  contact_username: string;
  contact_name: string;
}
```

## Edge Cases

| Scenario | Behavior |
|----------|----------|
| No contacts available | Show empty state in picker |
| User already in chat | Skip (no duplicate entry) |
| Network failure | Show error in picker, allow retry |
| User skips picker | Navigate to chat with only creator |
| User offline when added | Chat appears after reconnect/refresh |

## Testing

### Manual Test Cases

1. Create chat → picker opens → select contacts → verify added
2. Create chat → skip picker → verify navigates to empty chat
3. User A adds User B → User B sees notification + chat in sidebar
4. Send contact invite → verify notification still works (regression)
5. Search contacts by name/username in picker

## Implementation Phases

1. **Phase 1**: Unified notification system (migrate invite notifications)
2. **Phase 2**: Contact store and loading on page mount
3. **Phase 3**: Contact picker modal and chat creation flow
4. **Phase 4**: Backend WebSocket event + frontend handler
