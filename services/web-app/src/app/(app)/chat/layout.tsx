"use client";

import { useEffect, useState, useCallback } from "react";
import { useRouter } from "next/navigation";
import { useChatStore } from "@/store/chat-store";
import { useContactStore } from "@/store/contact-store";
import { chatApi, contactApi } from "@/lib/api";
import { ChatSidebar } from "@/components/chat/chat-sidebar";
import { CreateChatDialog } from "@/components/chat/create-chat-dialog";
import { ContactPickerDialog } from "@/components/chat/contact-picker-dialog";
import { WebSocketProvider, useWebSocket } from "@/contexts/websocket-context";
import { Loader2, Wifi, WifiOff } from "lucide-react";

function ChatLayoutContent({
  children,
}: {
  children: React.ReactNode;
}) {
  const router = useRouter();
  const { userId, setChats, addChat, _hasHydrated } = useChatStore();
  const { setContacts, setLoading: setContactsLoading } = useContactStore();
  const { isConnected, isSyncing, subscribeToChat } = useWebSocket();
  const [loading, setLoading] = useState(true);
  const [createDialogOpen, setCreateDialogOpen] = useState(false);
  const [contactPickerOpen, setContactPickerOpen] = useState(false);
  const [newChatId, setNewChatId] = useState<string | null>(null);

  // Fetch user's chats and contacts in parallel
  const fetchChatsAndContacts = useCallback(async () => {
    if (!userId) return;

    setLoading(true);
    setContactsLoading(true);

    try {
      const [chats, contacts] = await Promise.all([
        chatApi.getChatsForParticipant(userId),
        contactApi.getContacts(userId),
      ]);

      setChats(chats);
      setContacts(contacts);
    } catch (error) {
      console.error("Failed to fetch chats/contacts:", error);
    } finally {
      setLoading(false);
      setContactsLoading(false);
    }
  }, [userId, setChats, setContacts, setContactsLoading]);

  useEffect(() => {
    if (_hasHydrated && !userId) {
      router.push("/");
    } else if (_hasHydrated && userId) {
      fetchChatsAndContacts();
    }
  }, [_hasHydrated, userId, router, fetchChatsAndContacts]);

  const handleCreateChat = async (name: string) => {
    if (!userId) return;

    // Create the chat
    const newChat = await chatApi.createChat(name);

    // Add the creator as a participant (using numeric user ID)
    await chatApi.addParticipants(newChat.id, [userId], userId);

    // Add to local store
    addChat(newChat);

    // Subscribe to the new chat via WebSocket
    subscribeToChat(newChat.id);

    // Store chat ID and open contact picker
    setNewChatId(newChat.id);
    setContactPickerOpen(true);
  };

  const handleAddContactsToChat = async (contactIds: number[]) => {
    if (!userId || !newChatId) return;

    // Add participants to backend
    await chatApi.addParticipants(newChatId, contactIds, userId);

    // Navigate to the new chat
    router.push(`/chat/${newChatId}`);

    // Reset state
    setNewChatId(null);
  };

  const handleContactPickerClose = (open: boolean) => {
    setContactPickerOpen(open);

    // If closing without adding contacts, navigate to chat
    if (!open && newChatId) {
      router.push(`/chat/${newChatId}`);
      setNewChatId(null);
    }
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
      <main className="flex-1 flex flex-col overflow-hidden">
        {/* Global connection status bar */}
        <div className="h-8 px-4 flex items-center justify-end border-b border-border bg-card/50 text-xs">
          {isSyncing ? (
            <div className="flex items-center gap-1.5 text-amber-400">
              <Wifi className="w-3 h-3" />
              <span>Syncing…</span>
            </div>
          ) : isConnected ? (
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
        <div className="flex-1 min-h-0 overflow-auto flex flex-col">
          {children}
        </div>
      </main>
      
      <CreateChatDialog
        open={createDialogOpen}
        onOpenChange={setCreateDialogOpen}
        onCreateChat={handleCreateChat}
      />

      <ContactPickerDialog
        open={contactPickerOpen}
        onOpenChange={handleContactPickerClose}
        onSelectContacts={handleAddContactsToChat}
        excludeUserIds={userId ? [userId] : []}
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
