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
  username: string | null;
  name: string | null;
  setUser: (userId: string, username: string, name: string) => void;

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
      username: null,
      name: null,
      setUser: (userId, username, name) =>
        set((state) => {
          if (state.userId === userId) return state;
          const messagesByChat =
            userId && userId.length > 0 ? loadMessagesForUser(userId) : {};
          return { userId, username, name, messagesByChat, selectedChatId: null };
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
        username: state.username,
        name: state.name,
        messagesByChat: state.messagesByChat,
      }),
      onRehydrateStorage: () => (state) => {
        // Called when Zustand finishes loading from storage
        state?.setHasHydrated(true);
      },
    }
  )
);

// Custom storage: userId, username, name in sessionStorage; messagesByChat in localStorage, namespaced by userId
type PersistedShape = {
  userId: string | null;
  username: string | null;
  name: string | null;
  messagesByChat: Record<string, Message[]>;
};

function createNamespacedStorage(): PersistStorage<PersistedShape> {

  return {
    getItem: () => {
      if (!isBrowser) return null;

      // Read user identity from sessionStorage (tab-specific)
      const userId = sessionStorage.getItem(USER_KEY);
      const username = sessionStorage.getItem('chat-username');
      const name = sessionStorage.getItem('chat-name');

      // Read messages from localStorage (shared but namespaced by userId)
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
          username,
          name,
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
        const username = state?.username;
        const userName = state?.name;
        const messagesByChat = state?.messagesByChat;

        // Store user identity in sessionStorage (tab-specific)
        if (userId !== undefined) {
          if (userId === null) {
            sessionStorage.removeItem(USER_KEY);
          } else {
            sessionStorage.setItem(USER_KEY, userId);
          }
        }

        if (username !== undefined) {
          if (username === null) {
            sessionStorage.removeItem('chat-username');
          } else {
            sessionStorage.setItem('chat-username', username);
          }
        }

        if (userName !== undefined) {
          if (userName === null) {
            sessionStorage.removeItem('chat-name');
          } else {
            sessionStorage.setItem('chat-name', userName);
          }
        }

        // Store messages in localStorage (shared but namespaced by userId)
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
      sessionStorage.removeItem('chat-username');
      sessionStorage.removeItem('chat-name');
    },
  };
}

