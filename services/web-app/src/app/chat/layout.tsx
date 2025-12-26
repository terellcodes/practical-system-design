"use client";

import { useEffect, useState, useCallback } from "react";
import { useRouter } from "next/navigation";
import { useChatStore } from "@/store/chat-store";
import { chatApi } from "@/lib/api";
import { ChatSidebar } from "@/components/chat/chat-sidebar";
import { CreateChatDialog } from "@/components/chat/create-chat-dialog";
import { WebSocketProvider, useWebSocket } from "@/contexts/websocket-context";
import { Loader2, Wifi, WifiOff } from "lucide-react";

function ChatLayoutContent({
  children,
}: {
  children: React.ReactNode;
}) {
  const router = useRouter();
  const { userId, setChats, addChat, _hasHydrated } = useChatStore();
  const { isConnected, subscribeToChat } = useWebSocket();
  const [loading, setLoading] = useState(true);
  const [createDialogOpen, setCreateDialogOpen] = useState(false);

  // Fetch user's chats
  const fetchChats = useCallback(async () => {
    if (!userId) return;
    
    try {
      const chats = await chatApi.getChatsForParticipant(userId);
      setChats(chats);
    } catch (error) {
      console.error("Failed to fetch chats:", error);
    } finally {
      setLoading(false);
    }
  }, [userId, setChats]);

  useEffect(() => {
    if (_hasHydrated && !userId) {
      router.push("/");
    } else if (_hasHydrated && userId) {
      fetchChats();
    }
  }, [_hasHydrated, userId, router, fetchChats]);

  const handleCreateChat = async (name: string) => {
    if (!userId) return;

    // Create the chat
    const newChat = await chatApi.createChat(name);
    
    // Add the creator as a participant
    await chatApi.addParticipants(newChat.id, [userId]);
    
    // Add to local store
    addChat(newChat);
    
    // Subscribe to the new chat via WebSocket
    subscribeToChat(newChat.id);
    
    // Navigate to the new chat
    router.push(`/chat/${newChat.id}`);
  };

  if (!_hasHydrated || !userId) {
    return null;
  }

  if (loading) {
    return (
      <div className="h-screen flex items-center justify-center bg-background">
        <Loader2 className="w-8 h-8 animate-spin text-primary" />
      </div>
    );
  }

  return (
    <div className="h-screen flex bg-background">
      <ChatSidebar onCreateChat={() => setCreateDialogOpen(true)} />
      <main className="flex-1 flex flex-col">
        {/* Global connection status bar */}
        <div className="h-8 px-4 flex items-center justify-end border-b border-border bg-card/50 text-xs">
          {isConnected ? (
            <div className="flex items-center gap-1.5 text-primary">
              <Wifi className="w-3 h-3" />
              <span>Connected</span>
            </div>
          ) : (
            <div className="flex items-center gap-1.5 text-muted-foreground">
              <WifiOff className="w-3 h-3" />
              <span>Connecting...</span>
            </div>
          )}
        </div>
        {children}
      </main>
      
      <CreateChatDialog
        open={createDialogOpen}
        onOpenChange={setCreateDialogOpen}
        onCreateChat={handleCreateChat}
      />
    </div>
  );
}

export default function ChatLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <WebSocketProvider>
      <ChatLayoutContent>{children}</ChatLayoutContent>
    </WebSocketProvider>
  );
}
