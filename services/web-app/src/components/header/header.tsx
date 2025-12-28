'use client'

import { useChatStore } from '@/store/chat-store'

export function Header() {
  const userId = useChatStore((state) => state.userId)

  return (
    <header className="fixed top-0 left-0 right-0 h-12 bg-[#111b21] border-b border-[#222e35] z-30">
      <div className="flex items-center justify-between h-full px-4">
        <div className="text-[#e9edef] font-medium text-lg tracking-wide">
          SupaApp
        </div>
        {userId && (
          <div className="text-[#8696a0] text-sm font-medium">
            {userId}
          </div>
        )}
      </div>
    </header>
  )
}