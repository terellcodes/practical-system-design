'use client'

import { useEffect } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { X } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { useUIStore } from '@/store/ui-store'
import { useChatStore } from '@/store/chat-store'
import { useCopilotStore } from '@/store/copilot-store'
import { CopilotChat } from './copilot-chat'

export function CopilotPanel() {
  const copilotOpen = useUIStore((state) => state.copilotOpen)
  const setCopilotOpen = useUIStore((state) => state.setCopilotOpen)
  const userId = useChatStore((state) => state.userId)
  const setCurrentUser = useCopilotStore((state) => state.setCurrentUser)

  // Sync userId to copilot store - loads that user's message history
  useEffect(() => {
    setCurrentUser(userId)
  }, [userId, setCurrentUser])

  // Body scroll lock when panel is open
  useEffect(() => {
    if (copilotOpen) {
      document.body.style.overflow = 'hidden'
      return () => {
        document.body.style.overflow = 'unset'
      }
    }
  }, [copilotOpen])

  // Escape key handler
  useEffect(() => {
    if (!copilotOpen) return
    const handleEscape = (e: KeyboardEvent) => {
      if (e.key === 'Escape') setCopilotOpen(false)
    }
    document.addEventListener('keydown', handleEscape)
    return () => document.removeEventListener('keydown', handleEscape)
  }, [copilotOpen, setCopilotOpen])

  return (
    <AnimatePresence>
      {copilotOpen && (
        <>
          {/* Backdrop */}
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            transition={{ duration: 0.2 }}
            className="fixed inset-0 bg-black/80 md:bg-black/50 z-40"
            onClick={() => setCopilotOpen(false)}
          />

          {/* Panel */}
          <motion.div
            role="complementary"
            aria-label="AI Copilot Panel"
            initial={{ x: '100%' }}
            animate={{ x: 0 }}
            exit={{ x: '100%' }}
            transition={{ duration: 0.3, ease: 'easeInOut' }}
            className="fixed right-0 top-0 h-[100dvh] bg-[#111b21] border-l border-[#222e35] w-full md:w-[400px] lg:w-[480px] pt-12 z-40 flex flex-col"
          >
            {/* Header */}
            <div className="flex items-center justify-between px-4 py-3 border-b border-[#222e35]">
              <h2 className="text-[#e9edef] font-medium text-lg">AI Copilot</h2>
              <Button
                variant="ghost"
                size="icon"
                onClick={() => setCopilotOpen(false)}
                aria-label="Close copilot"
              >
                <X className="h-4 w-4" />
              </Button>
            </div>

            {/* Chat interface */}
            <div className="flex-1 flex flex-col overflow-hidden">
              <CopilotChat />
            </div>
          </motion.div>
        </>
      )}
    </AnimatePresence>
  )
}
