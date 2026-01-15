"use client";

import { useEffect, useRef, useCallback, useState } from "react";
import { useChatStore } from "@/store/chat-store";
import { useInviteStore } from "@/store/invite-store";
import { useNotificationStore, type Notification } from "@/store/notification-store";
import { getWebSocketUrl } from "@/lib/api";
import { chatApi } from "@/lib/api";
import type { Message, InviteWithUsers } from "@/types";

/**
 * WebSocket message types from server
 */
interface WSConnectedMessage {
  type: "connected";
  user_id: number;
  subscribed_chats: string[];
  timestamp: string;
}

interface WSChatMessage {
  type: "message";
  message_id: string;
  chat_id: string;
  sender_id: number;
  sender_username?: string;
  sender_name?: string;
  content: string;
  created_at: string;
  upload_status?: "PENDING" | "COMPLETED" | "FAILED";
  s3_bucket?: string;
  s3_key?: string;
}

interface WSSystemMessage {
  type: "system";
  content: string;
  chat_id: string;
  timestamp: string;
}

interface WSSubscribedMessage {
  type: "subscribed" | "unsubscribed";
  chat_id: string;
  success: boolean;
}

interface WSErrorMessage {
  type: "error";
  content: string;
}

interface WSPongMessage {
  type: "pong";
  timestamp: string;
}

// Invite event types (from user-service via Redis pub/sub)
interface WSInviteReceivedMessage {
  type: "invite_received";
  data: {
    invite_id: number;
    invitor_id: number;
    invitor_username: string;
    invitor_name: string;
    created_at: string;
  };
}

interface WSInviteAcceptedMessage {
  type: "invite_accepted";
  data: {
    invite_id: number;
    invitee_id: number;
    invitee_username: string;
    invitee_name: string;
    status: string;
  };
}

interface WSInviteRejectedMessage {
  type: "invite_rejected";
  data: {
    invite_id: number;
    invitee_id: number;
    invitee_username: string;
    invitee_name: string;
    status: string;
  };
}

type WSMessage = 
  | WSConnectedMessage 
  | WSChatMessage 
  | WSSystemMessage 
  | WSSubscribedMessage 
  | WSErrorMessage 
  | WSPongMessage
  | WSInviteReceivedMessage
  | WSInviteAcceptedMessage
  | WSInviteRejectedMessage;

interface UseUserWebSocketReturn {
  isConnected: boolean;
  isSyncing: boolean;
  subscribedChats: string[];
  sendMessage: (chatId: string, content: string) => void;
  subscribeToChat: (chatId: string) => void;
  unsubscribeFromChat: (chatId: string) => void;
}

// Reconnection config
const MAX_RECONNECT_ATTEMPTS = 5;
const BASE_RECONNECT_DELAY = 1000; // 1 second

/**
 * User-centric WebSocket hook.
 * 
 * Creates ONE WebSocket connection per user that receives messages
 * from ALL chats they're part of. Should be used at the app/layout level.
 * 
 * Auto-reconnects on unexpected disconnects with exponential backoff.
 */
export function useUserWebSocket(userId: number | null): UseUserWebSocketReturn {
  const wsRef = useRef<WebSocket | null>(null);
  const [isConnected, setIsConnected] = useState(false);
  const [isSyncing, setIsSyncing] = useState(false);
  const [subscribedChats, setSubscribedChats] = useState<string[]>([]);
  const { addMessage, bumpChat, username, name } = useChatStore();
  const { addPendingInvite, updateSentInviteStatus } = useInviteStore();
  // Use getState() to avoid re-render dependency chain issues
  const addNotification = useCallback(
    (notification: Omit<Notification, "id" | "createdAt">) => {
      useNotificationStore.getState().addNotification(notification);
    },
    []
  );

  // Reconnection state
  const reconnectAttempts = useRef(0);
  const reconnectTimeout = useRef<NodeJS.Timeout | null>(null);
  const shouldReconnect = useRef(true);

  const syncInbox = useCallback(async () => {
    if (!userId) return;
    if (!wsRef.current || wsRef.current.readyState !== WebSocket.OPEN) return;

    setIsSyncing(true);
    try {
      const response = await chatApi.syncInbox(userId);
      const items = response.items || [];

      for (const item of items) {
        const message: Message = {
          message_id: item.message_id,
          chat_id: item.chat_id,
          sender_id: item.sender_id,
          content: item.content,
          created_at: item.created_at,
          type: "message",
          upload_status: (item as any).upload_status,
          s3_bucket: (item as any).s3_bucket,
          s3_key: (item as any).s3_object_key || (item as any).s3_key,
        };

        addMessage(item.chat_id, message);
        bumpChat(item.chat_id);

        if (wsRef.current?.readyState === WebSocket.OPEN) {
          wsRef.current.send(
            JSON.stringify({
              type: "ack-message-received",
              message_id: item.message_id,
            })
          );
        }
      }
    } catch (error) {
      console.error("Failed to sync inbox:", error);
    } finally {
      setIsSyncing(false);
    }
  }, [userId, addMessage, bumpChat]);

  // Handle incoming WebSocket messages
  const handleMessage = useCallback(
    (event: MessageEvent) => {
      try {
        const data: WSMessage = JSON.parse(event.data);

        switch (data.type) {
          case "connected":
            console.log(`WebSocket connected for user ${data.user_id}, subscribed to ${data.subscribed_chats.length} chats`);
            setSubscribedChats(data.subscribed_chats);
            break;

          case "message": {
            const message: Message = {
              message_id: data.message_id,
              chat_id: data.chat_id,
              sender_id: data.sender_id,
              sender_username: data.sender_username,
              sender_name: data.sender_name,
              content: data.content,
              created_at: data.created_at,
              type: "message",
              upload_status: data.upload_status,
              s3_bucket: data.s3_bucket,
              s3_key: data.s3_key,
            };

            addMessage(data.chat_id, message);
            bumpChat(data.chat_id);

            // Acknowledge receipt
            if (wsRef.current?.readyState === WebSocket.OPEN) {
              wsRef.current.send(
                JSON.stringify({
                  type: "ack-message-received",
                  message_id: data.message_id,
                })
              );
            }
            break;
          }

          case "system": {
            const systemMessage: Message = {
              message_id: `system-${Date.now()}`,
              chat_id: data.chat_id,
              sender_id: 0,  // 0 represents system messages
              content: data.content,
              created_at: data.timestamp,
              type: "system",
            };
            addMessage(data.chat_id, systemMessage);
            break;
          }

          case "subscribed":
            if (data.success) {
              setSubscribedChats((prev) => 
                prev.includes(data.chat_id) ? prev : [...prev, data.chat_id]
              );
              console.log(`Subscribed to chat ${data.chat_id}`);
            }
            break;

          case "unsubscribed":
            if (data.success) {
              setSubscribedChats((prev) => prev.filter((id) => id !== data.chat_id));
              console.log(`Unsubscribed from chat ${data.chat_id}`);
            }
            break;

          case "error":
            console.error("WebSocket error:", data.content);
            break;

          case "pong":
            // Heartbeat response, can be used for connection health
            break;

          case "invite_received": {
            // Someone sent us an invite
            console.log("Invite received:", data.data);
            const inviteData = data.data;
            const invite: InviteWithUsers = {
              id: inviteData.invite_id,
              invitor_id: inviteData.invitor_id,
              invitor_username: inviteData.invitor_username,
              invitor_name: inviteData.invitor_name,
              invitee_id: userId || 0,  // We are the invitee
              invitee_username: "",  // Will be populated from store if needed
              invitee_name: "",
              status: "pending",
              created_at: inviteData.created_at,
              updated_at: inviteData.created_at,
            };
            // Add to pending invites list
            addPendingInvite(invite);
            // Show notification via unified notification system
            addNotification({
              type: "invite_received",
              source: "contacts",
              priority: "medium",
              category: "invites",
              title: "New Contact Invite",
              message: `${inviteData.invitor_name} wants to connect with you`,
              data: inviteData,
              expiresAt: new Date(Date.now() + 5000),
            });
            break;
          }

          case "invite_accepted": {
            // Someone accepted our invite
            console.log("Invite accepted:", data.data);
            updateSentInviteStatus(data.data.invite_id, "accepted");
            break;
          }

          case "invite_rejected": {
            // Someone rejected our invite
            console.log("Invite rejected:", data.data);
            updateSentInviteStatus(data.data.invite_id, "rejected");
            break;
          }
        }
      } catch (error) {
        console.error("Failed to parse WebSocket message:", error);
      }
    },
    [userId, addMessage, bumpChat, addPendingInvite, updateSentInviteStatus, addNotification]
  );

  // Connect function - can be called for initial connection or reconnection
  const connect = useCallback(() => {
    if (!userId) return;

    // Clean up any existing connection
    if (wsRef.current) {
      wsRef.current.close();
      wsRef.current = null;
    }

    const url = getWebSocketUrl(userId);
    console.log(`Connecting to WebSocket: ${url}`);

    const ws = new WebSocket(url);
    wsRef.current = ws;

    ws.onopen = () => {
      console.log("WebSocket connection opened");
      setIsConnected(true);
      reconnectAttempts.current = 0; // Reset on successful connection
      syncInbox();
    };

    ws.onmessage = handleMessage;

    ws.onerror = () => {
      console.warn("WebSocket connection error (details in close event)");
    };

    ws.onclose = (event) => {
      console.log(`WebSocket closed: code=${event.code} wasClean=${event.wasClean}`);
      setIsConnected(false);
      setSubscribedChats([]);

      // Auto-reconnect on unexpected disconnect
      if (
        !event.wasClean &&
        shouldReconnect.current &&
        reconnectAttempts.current < MAX_RECONNECT_ATTEMPTS
      ) {
        const delay = BASE_RECONNECT_DELAY * Math.pow(2, reconnectAttempts.current);
        console.log(
          `Reconnecting in ${delay}ms (attempt ${reconnectAttempts.current + 1}/${MAX_RECONNECT_ATTEMPTS})`
        );

        reconnectTimeout.current = setTimeout(() => {
          reconnectAttempts.current++;
          connect();
        }, delay);
      } else if (reconnectAttempts.current >= MAX_RECONNECT_ATTEMPTS) {
        console.error("Max reconnection attempts reached. Giving up.");
      }
    };
  }, [userId, handleMessage, syncInbox]);

  // Initial connection and cleanup
  useEffect(() => {
    if (!userId) return;

    shouldReconnect.current = true;
    connect();

    return () => {
      shouldReconnect.current = false; // Prevent reconnect on unmount
      if (reconnectTimeout.current) {
        clearTimeout(reconnectTimeout.current);
        reconnectTimeout.current = null;
      }
      if (wsRef.current) {
        wsRef.current.close();
        wsRef.current = null;
      }
    };
  }, [userId, connect]);

  // Send a message to a specific chat
  const sendMessage = useCallback(
    (chatId: string, content: string) => {
      if (!wsRef.current || wsRef.current.readyState !== WebSocket.OPEN) {
        console.error("WebSocket not connected");
        return;
      }

      wsRef.current.send(
        JSON.stringify({
          type: "message",
          chat_id: chatId,
          content,
          sender_username: username,  // Include for backend storage
          sender_name: name,          // Include for backend storage
        })
      );

      // Bump chat to top when sending
      bumpChat(chatId);
    },
    [bumpChat, username, name]
  );

  // Subscribe to a new chat (after joining)
  const subscribeToChat = useCallback((chatId: string) => {
    if (!wsRef.current || wsRef.current.readyState !== WebSocket.OPEN) {
      console.error("WebSocket not connected");
      return;
    }

    wsRef.current.send(
      JSON.stringify({
        type: "subscribe",
        chat_id: chatId,
      })
    );
  }, []);

  // Unsubscribe from a chat (after leaving)
  const unsubscribeFromChat = useCallback((chatId: string) => {
    if (!wsRef.current || wsRef.current.readyState !== WebSocket.OPEN) {
      console.error("WebSocket not connected");
      return;
    }

    wsRef.current.send(
      JSON.stringify({
        type: "unsubscribe",
        chat_id: chatId,
      })
    );
  }, []);

  return {
    isConnected,
    isSyncing,
    subscribedChats,
    sendMessage,
    subscribeToChat,
    unsubscribeFromChat,
  };
}
