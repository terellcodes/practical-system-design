import { create } from "zustand";
import { persist, type PersistStorage } from "zustand/middleware";
import type { Chat, Message } from "@/types";

const USER_KEY = "chat-user-id";
const messagesKey = (userId: string | null) => `chat-storage-${userId ?? "guest"}`;
const isBrowser = typeof window !== "undefined";

function loadMessagesForUser(userId: string): Record<string, Message[]> {
  if (!isBrowser) return {};
  try {
    const raw = localStorage.getItem(messagesKey(userId));
    if (!raw) return {};
    const parsed = JSON.parse(raw);
    return parsed.messagesByChat || {};
  } catch {
    return {};
  }
}

interface ChatState {
  // Hydration state
  _hasHydrated: boolean;
  setHasHydrated: (hasHydrated: boolean) => void;

  // User identity
  userId: string | null;
  setUserId: (userId: string) => void;

  // Chats
  chats: Chat[];
  setChats: (chats: Chat[]) => void;
  addChat: (chat: Chat) => void;
  bumpChat: (chatId: string) => void;

  // Selected chat
  selectedChatId: string | null;
  setSelectedChatId: (chatId: string | null) => void;

  // Messages (stored per chat)
  messagesByChat: Record<string, Message[]>;
  setMessages: (chatId: string, messages: Message[]) => void;
  addMessage: (chatId: string, message: Message) => void;
  getMessages: (chatId: string) => Message[];
}

export const useChatStore = create<ChatState>()(
  persist(
    (set, get) => ({
      // Hydration state
      _hasHydrated: false,
      setHasHydrated: (hasHydrated) => set({ _hasHydrated: hasHydrated }),

      // User identity
      userId: null,
      setUserId: (userId) =>
        set((state) => {
          if (state.userId === userId) return state;
          const messagesByChat =
            userId && userId.length > 0 ? loadMessagesForUser(userId) : {};
          return { userId, messagesByChat, selectedChatId: null };
        }),

      // Chats
      chats: [],
      setChats: (chats) => set({ chats }),
      addChat: (chat) => set((state) => ({ chats: [chat, ...state.chats] })),
      bumpChat: (chatId) =>
        set((state) => {
          const chat = state.chats.find((c) => c.id === chatId);
          if (!chat) return state;
          return {
            chats: [chat, ...state.chats.filter((c) => c.id !== chatId)],
          };
        }),

      // Selected chat
      selectedChatId: null,
      setSelectedChatId: (chatId) => set({ selectedChatId: chatId }),

      // Messages
      messagesByChat: {},
      setMessages: (chatId, messages) =>
        set((state) => ({
          messagesByChat: { ...state.messagesByChat, [chatId]: messages },
        })),
      addMessage: (chatId, message) =>
        set((state) => {
          const existingMessages = state.messagesByChat[chatId] || [];
          const idx = existingMessages.findIndex(
            (m) => m.message_id === message.message_id
          );

          // Upsert: replace if exists, otherwise append
          let updatedMessages: Message[];
          if (idx >= 0) {
            const merged = { ...existingMessages[idx], ...message };
            updatedMessages = [
              ...existingMessages.slice(0, idx),
              merged,
              ...existingMessages.slice(idx + 1),
            ];
          } else {
            updatedMessages = [...existingMessages, message];
          }

          return {
            messagesByChat: {
              ...state.messagesByChat,
              [chatId]: updatedMessages,
            },
          };
        }),
      getMessages: (chatId) => get().messagesByChat[chatId] || [],
    }),
    {
      name: "chat-storage", // logical name; actual storage keys are custom below
      storage: createNamespacedStorage(),
      partialize: (state) => ({
        userId: state.userId,
        messagesByChat: state.messagesByChat,
      }),
      onRehydrateStorage: () => (state) => {
        // Called when Zustand finishes loading from storage
        state?.setHasHydrated(true);
      },
    }
  )
);

// Custom storage: userId in sessionStorage; messagesByChat in localStorage, namespaced by userId
type PersistedShape = {
  userId: string | null;
  messagesByChat: Record<string, Message[]>;
};

function createNamespacedStorage(): PersistStorage<PersistedShape> {

  return {
    getItem: () => {
      if (!isBrowser) return null;
      const userId = sessionStorage.getItem(USER_KEY);

      const rawMessages =
        userId !== null ? localStorage.getItem(messagesKey(userId)) : null;
      let messagesByChat: Record<string, Message[]> = {};
      if (rawMessages) {
        try {
          const parsed = JSON.parse(rawMessages);
          messagesByChat = parsed.messagesByChat || {};
        } catch {
          messagesByChat = {};
        }
      }
      return {
        state: {
          userId,
          messagesByChat,
        },
        version: 0,
      };
    },
    setItem: (name, value) => {
      if (!isBrowser) return;
      void name;
      try {
        const { state } = value || {};
        const userId = state?.userId;
        const messagesByChat = state?.messagesByChat;
        // store userId in sessionStorage
        if (userId !== undefined) {
          if (userId === null) {
            sessionStorage.removeItem(USER_KEY);
          } else {
            sessionStorage.setItem(USER_KEY, userId);
          }
        }
        // store messages in a user-namespaced key in localStorage
        const key = messagesKey(userId ?? null);
        localStorage.setItem(
          key,
          JSON.stringify({ messagesByChat: messagesByChat || {} })
        );
      } catch (e) {
        console.error("Failed to persist chat storage", e);
      }
    },
    removeItem: (name) => {
      if (!isBrowser) return;
      void name;
      const userId = sessionStorage.getItem(USER_KEY);
      if (userId !== null) {
        localStorage.removeItem(messagesKey(userId));
      }
      sessionStorage.removeItem(USER_KEY);
    },
  };
}

