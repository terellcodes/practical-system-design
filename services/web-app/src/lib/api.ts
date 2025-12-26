/**
 * API client for backend services
 */

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost/api";

interface ApiError {
  detail: string;
}

async function handleResponse<T>(response: Response): Promise<T> {
  if (!response.ok) {
    const error: ApiError = await response.json().catch(() => ({
      detail: `HTTP ${response.status}: ${response.statusText}`,
    }));
    throw new Error(error.detail);
  }
  return response.json();
}

// Chat API
export const chatApi = {
  // Get all chats for a participant
  getChatsForParticipant: async (participantId: string) => {
    const response = await fetch(
      `${API_BASE}/chats/participant/${participantId}`
    );
    return handleResponse<
      Array<{
        id: string;
        name: string;
        metadata: Record<string, unknown>;
        created_at: string;
      }>
    >(response);
  },

  // Get a single chat with participants
  getChat: async (chatId: string) => {
    const response = await fetch(`${API_BASE}/chats/${chatId}`);
    return handleResponse<{
      chat: {
        id: string;
        name: string;
        metadata: Record<string, unknown>;
        created_at: string;
      };
      participants: Array<{
        chat_id: string;
        participant_id: string;
        joined_at: string;
      }>;
    }>(response);
  },

  // Create a new chat
  createChat: async (name: string, metadata?: Record<string, unknown>) => {
    const response = await fetch(`${API_BASE}/chats`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ name, metadata: metadata || {} }),
    });
    return handleResponse<{
      id: string;
      name: string;
      metadata: Record<string, unknown>;
      created_at: string;
    }>(response);
  },

  // Add participants to a chat
  addParticipants: async (chatId: string, participantIds: string[]) => {
    const response = await fetch(`${API_BASE}/chats/${chatId}/participants`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ participant_ids: participantIds }),
    });
    return handleResponse<
      Array<{
        chat_id: string;
        participant_id: string;
        joined_at: string;
      }>
    >(response);
  },

  // Sync undelivered messages from inbox
  syncMessages: async (chatId: string, userId: string) => {
    const response = await fetch(
      `${API_BASE}/chats/${chatId}/sync?user_id=${userId}`
    );
    return handleResponse<{
      items: Array<{
        message_id: string;
        chat_id: string;
        sender_id: string;
        content: string;
        created_at: string;
      }>;
      count: number;
      recipient_id: string;
    }>(response);
  },
};

// WebSocket URL helper
export function getWebSocketUrl(chatId: string, userId: string): string {
  const wsBase =
    process.env.NEXT_PUBLIC_WS_URL || "ws://localhost/api/chats";
  return `${wsBase}/ws/${chatId}?user_id=${userId}`;
}

