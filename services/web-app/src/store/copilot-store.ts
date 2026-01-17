import { create } from 'zustand'
import { copilotApi } from '@/lib/api'

export interface Message {
  id: string
  role: 'user' | 'assistant'
  content: string
  timestamp: number
}

interface UserInfo {
  id: number
  username: string
  name: string
}

interface CopilotState {
  currentUserId: string | null
  currentUserInfo: UserInfo | null
  conversationVersion: number
  messages: Message[]
  isLoading: boolean
  error: string | null
  setCurrentUser: (userId: string | null, userInfo?: UserInfo) => void
  sendMessage: (content: string) => Promise<void>
  loadHistory: () => Promise<void>
  clearHistory: () => Promise<void>
}

// Helper to get storage key for a user (for localStorage fallback)
const getStorageKey = (userId: string) => `copilot-messages-${userId}`
const getVersionKey = (userId: string) => `copilot-version-${userId}`

// Helper to load conversation version from localStorage
const loadConversationVersion = (userId: string): number => {
  if (typeof window === 'undefined') return 0
  try {
    const stored = localStorage.getItem(getVersionKey(userId))
    return stored ? parseInt(stored, 10) : 0
  } catch {
    return 0
  }
}

// Helper to save conversation version to localStorage
const saveConversationVersion = (userId: string, version: number) => {
  if (typeof window === 'undefined') return
  try {
    localStorage.setItem(getVersionKey(userId), version.toString())
  } catch {
    // Handle storage quota errors silently
  }
}

// Helper to load messages from localStorage (fallback for history)
const loadMessagesFromStorage = (userId: string): Message[] => {
  if (typeof window === 'undefined') return []
  try {
    const stored = localStorage.getItem(getStorageKey(userId))
    return stored ? JSON.parse(stored) : []
  } catch {
    return []
  }
}

// Helper to save messages to localStorage (for local persistence)
const saveMessagesToStorage = (userId: string, messages: Message[]) => {
  if (typeof window === 'undefined') return
  try {
    localStorage.setItem(getStorageKey(userId), JSON.stringify(messages))
  } catch {
    // Handle storage quota errors silently
  }
}

export const useCopilotStore = create<CopilotState>()((set, get) => ({
  currentUserId: null,
  currentUserInfo: null,
  conversationVersion: 0,
  messages: [],
  isLoading: false,
  error: null,

  setCurrentUser: (userId: string | null, userInfo?: UserInfo) => {
    const { currentUserId, messages } = get()

    // Don't do anything if same user
    if (currentUserId === userId) {
      // But update userInfo if provided
      if (userInfo) {
        set({ currentUserInfo: userInfo })
      }
      return
    }

    // Save current user's messages before switching
    if (currentUserId) {
      saveMessagesToStorage(currentUserId, messages)
    }

    // Load new user's messages and version from localStorage
    const newMessages = userId ? loadMessagesFromStorage(userId) : []
    const newVersion = userId ? loadConversationVersion(userId) : 0

    set({
      currentUserId: userId,
      currentUserInfo: userInfo || null,
      conversationVersion: newVersion,
      messages: newMessages,
      isLoading: false,
      error: null,
    })

    // Load history from backend if user is set
    if (userId && userInfo) {
      get().loadHistory()
    }
  },

  loadHistory: async () => {
    const { currentUserInfo } = get()
    if (!currentUserInfo) return

    try {
      const response = await copilotApi.getHistory(currentUserInfo.id)

      // Convert backend messages to our format
      const messages: Message[] = response.messages.map((msg, index) => ({
        id: `history-${index}-${Date.now()}`,
        role: msg.role,
        content: msg.content,
        timestamp: Date.now() - (response.messages.length - index) * 1000,
      }))

      set({ messages })

      // Save to localStorage as backup
      if (get().currentUserId) {
        saveMessagesToStorage(get().currentUserId!, messages)
      }
    } catch (err) {
      console.error('Failed to load copilot history:', err)
      // Fall back to localStorage messages (already loaded)
    }
  },

  sendMessage: async (content: string) => {
    const { currentUserId, currentUserInfo, conversationVersion } = get()
    if (!currentUserId || !currentUserInfo) return

    // Add user message
    const userMessage: Message = {
      id: crypto.randomUUID(),
      role: 'user',
      content,
      timestamp: Date.now(),
    }

    set((state) => ({
      messages: [...state.messages, userMessage],
      isLoading: true,
      error: null,
    }))

    // Save after adding user message
    saveMessagesToStorage(currentUserId, get().messages)

    try {
      // Call the copilot API with conversation version
      const response = await copilotApi.chat(
        currentUserInfo.id,
        content,
        currentUserInfo.username,
        currentUserInfo.name,
        conversationVersion
      )

      // Add AI response
      const aiMessage: Message = {
        id: crypto.randomUUID(),
        role: 'assistant',
        content: response.response,
        timestamp: Date.now(),
      }

      set((state) => ({
        messages: [...state.messages, aiMessage],
        isLoading: false,
      }))

      // Save after adding AI response
      saveMessagesToStorage(currentUserId, get().messages)
    } catch (err) {
      console.error('Failed to send copilot message:', err)

      // Add error message as AI response
      const errorMessage: Message = {
        id: crypto.randomUUID(),
        role: 'assistant',
        content:
          'Sorry, I encountered an error processing your request. Please try again.',
        timestamp: Date.now(),
      }

      set((state) => ({
        messages: [...state.messages, errorMessage],
        isLoading: false,
        error: err instanceof Error ? err.message : 'Unknown error',
      }))

      saveMessagesToStorage(currentUserId, get().messages)
    }
  },

  clearHistory: async () => {
    const { currentUserId, currentUserInfo, conversationVersion } = get()

    // Increment version to start fresh conversation
    const newVersion = conversationVersion + 1

    // Clear local state and increment version
    set({ messages: [], isLoading: false, error: null, conversationVersion: newVersion })

    // Clear messages and save new version to localStorage
    if (currentUserId) {
      saveMessagesToStorage(currentUserId, [])
      saveConversationVersion(currentUserId, newVersion)
    }

    // Call backend to clear history (optional, mainly for logging)
    if (currentUserInfo) {
      try {
        await copilotApi.clearHistory(currentUserInfo.id)
      } catch (err) {
        console.error('Failed to clear copilot history on backend:', err)
        // Local clear already happened, so this is non-critical
      }
    }
  },
}))
