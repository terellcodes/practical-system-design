/**
 * TypeScript types matching backend Pydantic models
 */

export interface Chat {
  id: string;
  name: string;
  metadata: Record<string, unknown>;
  created_at: string;
}

export interface ChatParticipant {
  chat_id: string;
  participant_id: string;
  joined_at: string;
}

export interface ChatWithParticipants {
  chat: Chat;
  participants: ChatParticipant[];
}

export interface Message {
  message_id: string;
  chat_id: string;
  sender_id: string;
  content: string;
  created_at: string;
  type: "message" | "system";
}

export interface User {
  id: number;
  name: string;
  email: string;
  created_at: string;
}

// WebSocket message types
export interface WSMessage {
  type: "message" | "system" | "pong" | "error";
  content?: string;
  message_id?: string;
  sender_id?: string;
  chat_id?: string;
  created_at?: string;
  timestamp?: string;
}

export interface WSAckMessage {
  type: "ack-message-recieved";
  message_id: string;
  recipient_id: string;
}

export interface WSSendMessage {
  type: "message";
  content: string;
}

