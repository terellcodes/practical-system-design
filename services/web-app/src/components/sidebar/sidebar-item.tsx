'use client'

import { ReactNode } from 'react'
import Link from 'next/link'
import { motion, AnimatePresence } from 'framer-motion'
import { cn } from '@/lib/utils'

interface SidebarItemProps {
  icon: ReactNode
  label: string
  href?: string
  onClick?: () => void
  isActive?: boolean
  isOpen: boolean
}

export function SidebarItem({ 
  icon, 
  label, 
  href, 
  onClick, 
  isActive, 
  isOpen 
}: SidebarItemProps) {
  const content = (
    <motion.div
      className={cn(
        "flex items-center transition-colors mx-1",
        isOpen ? "gap-3 px-3 py-2 rounded-md" : "justify-center py-2 px-0 rounded-md",
        "hover:bg-[#202c33] cursor-pointer group relative",
        isActive && "bg-emerald-500/10 text-emerald-500"
      )}
      whileHover={{ scale: 1.01 }}
      whileTap={{ scale: 0.99 }}
    >
      <div className={cn(
        "w-4 h-4 flex-shrink-0 flex items-center justify-center",
        isActive ? "text-emerald-500" : "text-[#8696a0] group-hover:text-[#e9edef]"
      )}>
        {icon}
      </div>
      
      <AnimatePresence mode="wait">
        {isOpen && (
          <motion.span
            initial={{ opacity: 0, width: 0 }}
            animate={{ opacity: 1, width: "auto" }}
            exit={{ opacity: 0, width: 0 }}
            transition={{ duration: 0.2 }}
            className="text-sm font-medium text-sidebar-foreground whitespace-nowrap overflow-hidden"
          >
            {label}
          </motion.span>
        )}
      </AnimatePresence>
    </motion.div>
  )

  if (href) {
    return (
      <Link href={href} className="block">
        {content}
      </Link>
    )
  }
  
  return (
    <button onClick={onClick} className="w-full text-left">
      {content}
    </button>
  )
}