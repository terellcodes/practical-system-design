"use client";

import { useEffect, useMemo } from "react";
import { useParams } from "next/navigation";
import { MessageCircle, Wifi, WifiOff } from "lucide-react";
import { useChatStore } from "@/store/chat-store";
import { useWebSocket } from "@/hooks/use-websocket";
import { MessageList } from "@/components/chat/message-list";
import { MessageInput } from "@/components/chat/message-input";

export default function ChatConversationPage() {
  const params = useParams();
  const chatId = params.chatId as string;

  const { userId, chats, messagesByChat } = useChatStore();

  // Find the current chat to get its name
  const currentChat = useMemo(
    () => chats.find((c) => c.id === chatId),
    [chats, chatId]
  );

  // Get messages for this chat, sorted by timestamp
  const messages = useMemo(() => {
    const chatMessages = messagesByChat[chatId] || [];
    return [...chatMessages].sort(
      (a, b) =>
        new Date(a.created_at).getTime() - new Date(b.created_at).getTime()
    );
  }, [messagesByChat, chatId]);

  // Connect to WebSocket
  const { isConnected, sendMessage } = useWebSocket({
    chatId,
    userId: userId || "",
  });

  // Update document title with chat name
  useEffect(() => {
    if (currentChat) {
      document.title = `${currentChat.name} - Chat App`;
    }
    return () => {
      document.title = "Chat App";
    };
  }, [currentChat]);

  if (!userId) {
    return null;
  }

  return (
    <div className="flex-1 flex flex-col">
      {/* Header */}
      <div className="h-16 px-6 flex items-center justify-between border-b border-border bg-card">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-full bg-primary/20 flex items-center justify-center">
            <MessageCircle className="w-5 h-5 text-primary" />
          </div>
          <div>
            <h2 className="font-semibold">
              {currentChat?.name || "Chat"}
            </h2>
            <p className="text-xs text-muted-foreground font-mono">{chatId}</p>
          </div>
        </div>

        {/* Connection status */}
        <div className="flex items-center gap-2">
          {isConnected ? (
            <div className="flex items-center gap-1.5 text-xs text-primary">
              <Wifi className="w-4 h-4" />
              <span>Connected</span>
            </div>
          ) : (
            <div className="flex items-center gap-1.5 text-xs text-muted-foreground">
              <WifiOff className="w-4 h-4" />
              <span>Connecting...</span>
            </div>
          )}
        </div>
      </div>

      {/* Message List */}
      <MessageList messages={messages} currentUserId={userId} />

      {/* Message Input */}
      <MessageInput onSend={sendMessage} disabled={!isConnected} />
    </div>
  );
}
