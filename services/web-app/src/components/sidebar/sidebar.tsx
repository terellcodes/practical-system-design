'use client'

import { useState } from 'react'
import { usePathname } from 'next/navigation'
import { motion } from 'framer-motion'
import { Plus, MessageSquare } from 'lucide-react'
import { SidebarItem } from './sidebar-item'
import { AddUserDialog } from './add-user-dialog'
import { useChatStore } from '@/store/chat-store'

export function Sidebar() {
  const pathname = usePathname()
  const [isHovered, setIsHovered] = useState(false)
  const userId = useChatStore((state) => state.userId)
  const [showAddUserDialog, setShowAddUserDialog] = useState(false)

  return (
    <>
      <motion.aside
        initial={false}
        animate={{ width: isHovered ? 180 : 40 }}
        transition={{ duration: 0.2, ease: 'easeInOut' }}
        className="fixed left-0 top-0 h-full bg-[#111b21] border-r border-[#222e35] flex flex-col z-20"
        onMouseEnter={() => setIsHovered(true)}
        onMouseLeave={() => setIsHovered(false)}
      >

        {/* Top spacing - maintains consistent height */}
        <div className="h-12 border-b border-[#222e35] flex items-center">
          {isHovered && userId && (
            <div className="px-2 flex flex-col justify-center">
              <p className="text-[10px] text-muted-foreground uppercase">User</p>
              <p className="text-sidebar-foreground text-xs font-medium truncate">{userId}</p>
            </div>
          )}
        </div>

        {/* Navigation Items */}
        <nav className="flex-1 py-2 px-0 space-y-0.5">
          <SidebarItem
            icon={<Plus />}
            label="Add User"
            onClick={() => setShowAddUserDialog(true)}
            isOpen={isHovered}
          />
          <SidebarItem
            icon={<MessageSquare />}
            label="Chat"
            href="/chat"
            isActive={pathname?.startsWith('/chat')}
            isOpen={isHovered}
          />
        </nav>

      </motion.aside>

      {/* Add User Dialog */}
      <AddUserDialog 
        open={showAddUserDialog} 
        onOpenChange={setShowAddUserDialog} 
      />
    </>
  )
}