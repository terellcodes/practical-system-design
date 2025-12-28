'use client'

import { useState } from 'react'
import { usePathname } from 'next/navigation'
import { motion } from 'framer-motion'
import { Plus, MessageSquare, ChevronRight } from 'lucide-react'
import { SidebarItem } from './sidebar-item'
import { useUIStore } from '@/store/ui-store'
import { AddUserDialog } from './add-user-dialog'
import { useChatStore } from '@/store/chat-store'

export function Sidebar() {
  const pathname = usePathname()
  const { sidebarOpen, toggleSidebar } = useUIStore()
  const userId = useChatStore((state) => state.userId)
  const [showAddUserDialog, setShowAddUserDialog] = useState(false)

  return (
    <>
      <motion.aside
        initial={false}
        animate={{ width: sidebarOpen ? 180 : 40 }}
        transition={{ duration: 0.2, ease: 'easeInOut' }}
        className="fixed left-0 top-0 h-full bg-[#111b21] border-r border-[#222e35] flex flex-col z-40"
      >

        {/* Top spacing when collapsed, user info when expanded */}
        {sidebarOpen ? (
          userId && (
            <motion.div
              initial={{ opacity: 0, height: 0 }}
              animate={{ opacity: 1, height: 'auto' }}
              exit={{ opacity: 0, height: 0 }}
              className="px-2 py-2 border-b border-[#222e35]"
            >
              <p className="text-[10px] text-muted-foreground uppercase">User</p>
              <p className="text-sidebar-foreground text-xs font-medium truncate">{userId}</p>
            </motion.div>
          )
        ) : (
          <div className="h-12 border-b border-[#222e35]" />
        )}

        {/* Navigation Items */}
        <nav className="flex-1 py-2 px-0 space-y-0.5">
          <SidebarItem
            icon={<Plus />}
            label="Add User"
            onClick={() => setShowAddUserDialog(true)}
            isOpen={sidebarOpen}
          />
          <SidebarItem
            icon={<MessageSquare />}
            label="Chat"
            href="/chat"
            isActive={pathname?.startsWith('/chat')}
            isOpen={sidebarOpen}
          />
        </nav>

        {/* Toggle Button */}
        <button
          onClick={toggleSidebar}
          className="h-9 flex items-center justify-center border-t border-[#222e35] hover:bg-[#202c33] transition-colors"
        >
          <motion.div
            animate={{ rotate: sidebarOpen ? 180 : 0 }}
            transition={{ duration: 0.2 }}
          >
            <ChevronRight className="w-4 h-4 text-[#8696a0]" />
          </motion.div>
        </button>
      </motion.aside>

      {/* Add User Dialog */}
      <AddUserDialog 
        open={showAddUserDialog} 
        onOpenChange={setShowAddUserDialog} 
      />
    </>
  )
}