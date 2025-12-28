'use client'

import { useEffect } from 'react'
import { useRouter } from 'next/navigation'
import { Sidebar } from '@/components/sidebar/sidebar'
import { useChatStore } from '@/store/chat-store'
import { useUIStore } from '@/store/ui-store'
import { cn } from '@/lib/utils'

export default function AppLayout({ children }: { children: React.ReactNode }) {
  const router = useRouter()
  const userId = useChatStore((state) => state.userId)
  const sidebarOpen = useUIStore((state) => state.sidebarOpen)

  useEffect(() => {
    if (!userId) {
      router.push('/')
    }
  }, [userId, router])

  if (!userId) {
    return null // or loading spinner
  }

  return (
    <div className="flex h-screen bg-[#0c1317]">
      <Sidebar />
      <main 
        className={cn(
          "flex-1 transition-all duration-200",
          sidebarOpen ? "ml-[180px]" : "ml-10"
        )}
      >
        {children}
      </main>
    </div>
  )
}