"use client";

import { useEffect, useRef, useCallback, useState } from "react";
import { useChatStore } from "@/store/chat-store";
import { getWebSocketUrl } from "@/lib/api";
import { chatApi } from "@/lib/api";
import type { Message } from "@/types";

/**
 * WebSocket message types from server
 */
interface WSConnectedMessage {
  type: "connected";
  user_id: string;
  subscribed_chats: string[];
  timestamp: string;
}

interface WSChatMessage {
  type: "message";
  message_id: string;
  chat_id: string;
  sender_id: string;
  content: string;
  created_at: string;
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

type WSMessage = 
  | WSConnectedMessage 
  | WSChatMessage 
  | WSSystemMessage 
  | WSSubscribedMessage 
  | WSErrorMessage 
  | WSPongMessage;

interface UseUserWebSocketReturn {
  isConnected: boolean;
  isSyncing: boolean;
  subscribedChats: string[];
  sendMessage: (chatId: string, content: string) => void;
  subscribeToChat: (chatId: string) => void;
  unsubscribeFromChat: (chatId: string) => void;
}

/**
 * User-centric WebSocket hook.
 * 
 * Creates ONE WebSocket connection per user that receives messages
 * from ALL chats they're part of. Should be used at the app/layout level.
 */
export function useUserWebSocket(userId: string | null): UseUserWebSocketReturn {
  const wsRef = useRef<WebSocket | null>(null);
  const [isConnected, setIsConnected] = useState(false);
  const [isSyncing, setIsSyncing] = useState(false);
  const [subscribedChats, setSubscribedChats] = useState<string[]>([]);
  const { addMessage, bumpChat } = useChatStore();

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
              content: data.content,
              created_at: data.created_at,
              type: "message",
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
              sender_id: "system",
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
        }
      } catch (error) {
        console.error("Failed to parse WebSocket message:", error);
      }
    },
    [addMessage, bumpChat]
  );

  // Connect to WebSocket
  useEffect(() => {
    if (!userId) {
      return;
    }

    // Track if effect is still active (handles React Strict Mode)
    let isActive = true;

    const url = getWebSocketUrl(userId);
    console.log(`Connecting to WebSocket: ${url}`);
    
    const ws = new WebSocket(url);
    wsRef.current = ws;

    ws.onopen = () => {
      if (!isActive) return;
      console.log("WebSocket connection opened");
      setIsConnected(true);
      // Sync inbox on (re)connect
      syncInbox();
    };

    ws.onmessage = (event) => {
      if (!isActive) return;
      handleMessage(event);
    };

    ws.onerror = () => {
      // WebSocket error events don't contain useful info
      // The close event will provide the actual error details
      if (isActive) {
        console.warn("WebSocket connection error (details in close event)");
      }
    };

    ws.onclose = (event) => {
      if (!isActive) return;
      console.log(`WebSocket closed: ${event.code} ${event.reason}`);
      setIsConnected(false);
      setSubscribedChats([]);
    };

    return () => {
      isActive = false;
      if (ws.readyState === WebSocket.OPEN || ws.readyState === WebSocket.CONNECTING) {
        ws.close();
      }
      wsRef.current = null;
    };
  }, [userId, handleMessage, syncInbox]);

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
        })
      );

      // Bump chat to top when sending
      bumpChat(chatId);
    },
    [bumpChat]
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
