/**
 * API client for backend services
 */

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost/api";
const LOCALSTACK_HOST = process.env.NEXT_PUBLIC_LOCALSTACK_HOST || "localhost";
const S3_PUBLIC_BASE =
  process.env.NEXT_PUBLIC_S3_PUBLIC_URL || "http://localhost:4566";
export const S3_BUCKET =
  process.env.NEXT_PUBLIC_S3_BUCKET || "chat-media";

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
  getChatsForParticipant: async (participantId: number) => {
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
  addParticipants: async (chatId: string, participantIds: number[], userId: number) => {
    const response = await fetch(`${API_BASE}/chats/${chatId}/participants`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "X-User-Id": userId.toString(),  // Convert to string for HTTP header
      },
      body: JSON.stringify({ participant_ids: participantIds }),
    });
    return handleResponse<
      Array<{
        chat_id: string;
        participant_id: number;
        joined_at: string;
      }>
    >(response);
  },

  // Sync all undelivered messages (inbox) for a user across chats
  syncInbox: async (userId: number) => {
    const response = await fetch(`${API_BASE}/chats/inbox/sync?user_id=${userId}`);
    return handleResponse<{
      items: Array<{
        message_id: string;
        chat_id: string;
        sender_id: number;
        content: string;
        created_at: string;
      }>;
      count: number;
      recipient_id: number;
    }>(response);
  },

  // Request a presigned upload URL for an attachment
  requestUpload: async (chatId: string, params: {
    sender_id: number;
    filename: string;
    content_type: string;
    content?: string;
  }) => {
    const response = await fetch(`${API_BASE}/chats/${chatId}/messages/upload-request`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(params),
    });
    return handleResponse<{
      message_id: string;
      upload_url: string;
      s3_key: string;
      expires_in: number;
    }>(response);
  },
};

// Invite API
export const inviteApi = {
  // Send an invite to a user by their connect PIN
  sendInvite: async (userId: number, connectPin: string) => {
    const response = await fetch(`${API_BASE}/invites`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "X-User-Id": userId.toString(),
      },
      body: JSON.stringify({ connect_pin: connectPin }),
    });
    return handleResponse<{
      id: number;
      invitor_id: number;
      invitor_username: string;
      invitor_name: string;
      invitee_id: number;
      invitee_username: string;
      invitee_name: string;
      status: "pending" | "accepted" | "rejected";
      created_at: string;
      updated_at: string;
    }>(response);
  },

  // Get pending invites received by the user
  getPendingInvites: async (userId: number) => {
    const response = await fetch(`${API_BASE}/invites`, {
      headers: { "X-User-Id": userId.toString() },
    });
    return handleResponse<
      Array<{
        id: number;
        invitor_id: number;
        invitor_username: string;
        invitor_name: string;
        invitee_id: number;
        invitee_username: string;
        invitee_name: string;
        status: "pending" | "accepted" | "rejected";
        created_at: string;
        updated_at: string;
      }>
    >(response);
  },

  // Get invites sent by the user
  getSentInvites: async (userId: number) => {
    const response = await fetch(`${API_BASE}/invites/sent`, {
      headers: { "X-User-Id": userId.toString() },
    });
    return handleResponse<
      Array<{
        id: number;
        invitor_id: number;
        invitor_username: string;
        invitor_name: string;
        invitee_id: number;
        invitee_username: string;
        invitee_name: string;
        status: "pending" | "accepted" | "rejected";
        created_at: string;
        updated_at: string;
      }>
    >(response);
  },

  // Accept or reject an invite
  respondToInvite: async (
    userId: number,
    inviteId: number,
    status: "accepted" | "rejected"
  ) => {
    const response = await fetch(`${API_BASE}/invites/${inviteId}`, {
      method: "PUT",
      headers: {
        "Content-Type": "application/json",
        "X-User-Id": userId.toString(),
      },
      body: JSON.stringify({ status }),
    });
    return handleResponse<{
      id: number;
      invitor_id: number;
      invitee_id: number;
      status: string;
      created_at: string;
      updated_at: string;
    }>(response);
  },
};

// User API
export const userApi = {
  // Get user by username
  getUserByUsername: async (username: string) => {
    const response = await fetch(`${API_BASE}/users/username/${username}`);
    return handleResponse<{
      id: number;
      username: string;
      name: string;
      email: string;
      connect_pin: string;
      created_at: string;
    }>(response);
  },

  // Login or create a user by username
  loginOrCreateUser: async (username: string) => {
    const response = await fetch(`${API_BASE}/users/login`,
      {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ username }),
      }
    );
    return handleResponse<{
      id: number;
      username: string;
      name: string;
      email: string;
      connect_pin: string;
      created_at: string;
    }>(response);
  },
};

// WebSocket URL helper - User-centric (single connection per user)
export function getWebSocketUrl(userId: number): string {
  const wsBase =
    process.env.NEXT_PUBLIC_WS_URL || "ws://localhost/api/chats";
  return `${wsBase}/ws?user_id=${userId}`;
}

// Replace internal localstack host with host-accessible URL for uploads/downloads
export function normalizeLocalstackUrl(url: string): string {
  return url.replace("http://localstack", `http://${LOCALSTACK_HOST}`);
}

// Build a public S3 URL (LocalStack) for rendering attachments
export function buildS3PublicUrl(bucket: string, key: string): string {
  return `${S3_PUBLIC_BASE}/${bucket}/${key}`;
}

