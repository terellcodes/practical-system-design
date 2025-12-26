"use client";

import { createContext, useContext, ReactNode } from "react";
import { useUserWebSocket } from "@/hooks/use-websocket";
import { useChatStore } from "@/store/chat-store";

interface WebSocketContextValue {
  isConnected: boolean;
  isSyncing: boolean;
  subscribedChats: string[];
  sendMessage: (chatId: string, content: string) => void;
  subscribeToChat: (chatId: string) => void;
  unsubscribeFromChat: (chatId: string) => void;
}

const WebSocketContext = createContext<WebSocketContextValue | null>(null);

interface WebSocketProviderProps {
  children: ReactNode;
}

export function WebSocketProvider({ children }: WebSocketProviderProps) {
  const { userId } = useChatStore();
  const ws = useUserWebSocket(userId);

  return (
    <WebSocketContext.Provider value={ws}>
      {children}
    </WebSocketContext.Provider>
  );
}

export function useWebSocket(): WebSocketContextValue {
  const context = useContext(WebSocketContext);
  if (!context) {
    throw new Error("useWebSocket must be used within a WebSocketProvider");
  }
  return context;
}

