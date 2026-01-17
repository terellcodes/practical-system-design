'use client'

import { useEffect } from 'react'
import { useRouter } from 'next/navigation'
import { Sidebar } from '@/components/sidebar/sidebar'
import { Header } from '@/components/header/header'
import { CopilotPanel } from '@/components/copilot/copilot-panel'
import { useChatStore } from '@/store/chat-store'

export default function AppLayout({ children }: { children: React.ReactNode }) {
  const router = useRouter()
  const userId = useChatStore((state) => state.userId)

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
      <Header />
      <Sidebar />
      <CopilotPanel />
      <main className="flex-1 ml-10 pt-12">
        {children}
      </main>
    </div>
  )
}