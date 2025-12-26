"use client";

import { useEffect, useRef, useCallback, useState } from "react";
import { useChatStore } from "@/store/chat-store";
import { getWebSocketUrl, chatApi } from "@/lib/api";
import type { Message, WSMessage } from "@/types";

interface UseWebSocketOptions {
  chatId: string;
  userId: string;
  onMessage?: (message: Message) => void;
}

interface UseWebSocketReturn {
  isConnected: boolean;
  sendMessage: (content: string) => void;
}

export function useWebSocket({
  chatId,
  userId,
  onMessage,
}: UseWebSocketOptions): UseWebSocketReturn {
  const wsRef = useRef<WebSocket | null>(null);
  const [isConnected, setIsConnected] = useState(false);
  const { addMessage, bumpChat } = useChatStore();

  // Sync undelivered messages from inbox on connect
  const syncInbox = useCallback(async () => {
    try {
      const response = await chatApi.syncMessages(chatId, userId);
      const messageIdsToAck: string[] = [];

      // Add each message to store
      response.items.forEach((item) => {
        const message: Message = {
          message_id: item.message_id,
          chat_id: item.chat_id,
          sender_id: item.sender_id,
          content: item.content,
          created_at: item.created_at,
          type: "message",
        };
        addMessage(chatId, message);
        messageIdsToAck.push(item.message_id);
      });

      // Acknowledge messages via WebSocket
      if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
        messageIdsToAck.forEach((messageId) => {
          wsRef.current?.send(
            JSON.stringify({
              type: "ack-message-recieved",
              message_id: messageId,
              recipient_id: userId,
            })
          );
        });
      }

      if (response.items.length > 0) {
        bumpChat(chatId);
      }
    } catch (error) {
      console.error("Failed to sync inbox:", error);
    }
  }, [chatId, userId, addMessage, bumpChat]);

  // Handle incoming WebSocket messages
  const handleMessage = useCallback(
    (event: MessageEvent) => {
      try {
        const data: WSMessage = JSON.parse(event.data);

        if (data.type === "message" && data.content) {
          const message: Message = {
            message_id: data.message_id || `msg-${Date.now()}`,
            chat_id: data.chat_id || chatId,
            sender_id: data.sender_id || "unknown",
            content: data.content,
            created_at: data.created_at || new Date().toISOString(),
            type: "message",
          };

          addMessage(chatId, message);
          bumpChat(chatId);
          onMessage?.(message);

          // Acknowledge receipt
          if (wsRef.current && data.message_id) {
            wsRef.current.send(
              JSON.stringify({
                type: "ack-message-recieved",
                message_id: data.message_id,
                recipient_id: userId,
              })
            );
          }
        } else if (data.type === "system" && data.content) {
          // Handle system messages (user joined/left)
          const message: Message = {
            message_id: `system-${Date.now()}`,
            chat_id: chatId,
            sender_id: "system",
            content: data.content,
            created_at: data.timestamp || new Date().toISOString(),
            type: "system",
          };
          addMessage(chatId, message);
        }
      } catch (error) {
        console.error("Failed to parse WebSocket message:", error);
      }
    },
    [chatId, userId, addMessage, bumpChat, onMessage]
  );

  // Connect to WebSocket
  useEffect(() => {
    if (!chatId || !userId) return;

    const url = getWebSocketUrl(chatId, userId);
    const ws = new WebSocket(url);
    wsRef.current = ws;

    ws.onopen = () => {
      console.log(`WebSocket connected to chat ${chatId}`);
      setIsConnected(true);
      // Sync inbox after connection
      syncInbox();
    };

    ws.onmessage = handleMessage;

    ws.onerror = (error) => {
      console.error("WebSocket error:", error);
    };

    ws.onclose = (event) => {
      console.log(`WebSocket closed: ${event.code} ${event.reason}`);
      setIsConnected(false);
    };

    return () => {
      if (ws.readyState === WebSocket.OPEN) {
        ws.close();
      }
      wsRef.current = null;
    };
  }, [chatId, userId, handleMessage, syncInbox]);

  // Send message function
  const sendMessage = useCallback(
    (content: string) => {
      if (!wsRef.current || wsRef.current.readyState !== WebSocket.OPEN) {
        console.error("WebSocket not connected");
        return;
      }

      wsRef.current.send(
        JSON.stringify({
          type: "message",
          content,
        })
      );

      // Bump chat to top when sending
      bumpChat(chatId);
    },
    [chatId, bumpChat]
  );

  return { isConnected, sendMessage };
}

