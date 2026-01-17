import { create } from 'zustand'

export interface Message {
  id: string
  role: 'user' | 'assistant'
  content: string
  timestamp: number
}

interface CopilotState {
  currentUserId: string | null
  messages: Message[]
  isLoading: boolean
  setCurrentUser: (userId: string | null) => void
  sendMessage: (content: string) => Promise<void>
  clearHistory: () => void
}

// Helper to get storage key for a user
const getStorageKey = (userId: string) => `copilot-messages-${userId}`

// Helper to load messages from localStorage
const loadMessages = (userId: string): Message[] => {
  if (typeof window === 'undefined') return []
  try {
    const stored = localStorage.getItem(getStorageKey(userId))
    return stored ? JSON.parse(stored) : []
  } catch {
    return []
  }
}

// Helper to save messages to localStorage
const saveMessages = (userId: string, messages: Message[]) => {
  if (typeof window === 'undefined') return
  try {
    localStorage.setItem(getStorageKey(userId), JSON.stringify(messages))
  } catch {
    // Handle storage quota errors silently
  }
}

export const useCopilotStore = create<CopilotState>()((set, get) => ({
  currentUserId: null,
  messages: [],
  isLoading: false,

  setCurrentUser: (userId: string | null) => {
    const { currentUserId, messages } = get()

    // Don't do anything if same user
    if (currentUserId === userId) return

    // Save current user's messages before switching
    if (currentUserId) {
      saveMessages(currentUserId, messages)
    }

    // Load new user's messages (or empty if logging out)
    const newMessages = userId ? loadMessages(userId) : []

    set({ currentUserId: userId, messages: newMessages, isLoading: false })
  },

  sendMessage: async (content: string) => {
    const { currentUserId } = get()
    if (!currentUserId) return

    // Add user message
    const userMessage: Message = {
      id: crypto.randomUUID(),
      role: 'user',
      content,
      timestamp: Date.now()
    }

    set((state) => ({
      messages: [...state.messages, userMessage],
      isLoading: true
    }))

    // Save after adding user message
    saveMessages(currentUserId, get().messages)

    // Simulate AI response with 1 second delay
    await new Promise((resolve) => setTimeout(resolve, 1000))

    // Add AI response
    const aiMessage: Message = {
      id: crypto.randomUUID(),
      role: 'assistant',
      content: `I received your message: "${content}". This is a mock response. The actual AI integration will be added in the future.`,
      timestamp: Date.now()
    }

    set((state) => ({
      messages: [...state.messages, aiMessage],
      isLoading: false
    }))

    // Save after adding AI response
    saveMessages(currentUserId, get().messages)
  },

  clearHistory: () => {
    const { currentUserId } = get()
    set({ messages: [], isLoading: false })

    // Clear from localStorage too
    if (currentUserId) {
      saveMessages(currentUserId, [])
    }
  }
}))
