import { create } from "zustand";
import { persist } from "zustand/middleware";
import type { Chat, Message } from "@/types";

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
      setUserId: (userId) => set({ userId }),

      // Chats
      chats: [],
      setChats: (chats) => set({ chats }),
      addChat: (chat) => set((state) => ({ chats: [...state.chats, chat] })),

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
          // Avoid duplicates by checking message_id
          if (existingMessages.some((m) => m.message_id === message.message_id)) {
            return state;
          }
          return {
            messagesByChat: {
              ...state.messagesByChat,
              [chatId]: [...existingMessages, message],
            },
          };
        }),
      getMessages: (chatId) => get().messagesByChat[chatId] || [],
    }),
    {
      name: "chat-storage",
      partialize: (state) => ({
        userId: state.userId,
        messagesByChat: state.messagesByChat,
      }),
      onRehydrateStorage: () => (state) => {
        // Called when Zustand finishes loading from localStorage
        state?.setHasHydrated(true);
      },
    }
  )
);

