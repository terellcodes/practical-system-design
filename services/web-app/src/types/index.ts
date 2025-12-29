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

export type UploadStatus = "PENDING" | "COMPLETED" | "FAILED" | undefined;

export interface Message {
  message_id: string;
  chat_id: string;
  sender_id: string;
  content: string;
  created_at: string;
  type: "message" | "system";
  // Attachment fields (optional)
  upload_status?: UploadStatus;
  s3_bucket?: string;
  s3_key?: string;
}

export interface User {
  id: number;
  username: string;
  name: string;
  email: string;
  connect_pin: string;
  created_at: string;
}

// Invite types
export type InviteStatus = "pending" | "accepted" | "rejected";

export interface Invite {
  id: number;
  invitor_id: number;
  invitee_id: number;
  status: InviteStatus;
  created_at: string;
  updated_at: string;
}

export interface InviteWithUsers extends Invite {
  invitor_username: string;
  invitor_name: string;
  invitee_username: string;
  invitee_name: string;
}

// WebSocket invite event types
export interface WSInviteReceivedEvent {
  type: "invite_received";
  data: {
    invite_id: number;
    invitor_id: number;
    invitor_username: string;
    invitor_name: string;
    created_at: string;
  };
}

export interface WSInviteResponseEvent {
  type: "invite_accepted" | "invite_rejected";
  data: {
    invite_id: number;
    invitee_id: number;
    invitee_username: string;
    invitee_name: string;
    status: string;
  };
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

