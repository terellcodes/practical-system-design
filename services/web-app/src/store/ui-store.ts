import { create } from 'zustand'
import { persist } from 'zustand/middleware'

interface UIState {
  sidebarOpen: boolean
  copilotOpen: boolean
  toggleSidebar: () => void
  setSidebarOpen: (open: boolean) => void
  toggleCopilot: () => void
  setCopilotOpen: (open: boolean) => void
}

export const useUIStore = create<UIState>()(
  persist(
    (set) => ({
      sidebarOpen: false, // Default to collapsed
      copilotOpen: false,
      toggleSidebar: () => set((state) => ({ sidebarOpen: !state.sidebarOpen })),
      setSidebarOpen: (open) => set({ sidebarOpen: open }),
      toggleCopilot: () => set((state) => ({ copilotOpen: !state.copilotOpen })),
      setCopilotOpen: (open) => set({ copilotOpen: open }),
    }),
    {
      name: 'ui-storage',
      partialize: (state) => ({
        sidebarOpen: state.sidebarOpen,
        copilotOpen: state.copilotOpen
      }),
    }
  )
)