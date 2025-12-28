'use client'

import { ReactNode } from 'react'
import Link from 'next/link'
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
    <div
      className={cn(
        "flex items-center transition-colors mx-1",
        isOpen ? "gap-3 px-3 py-2 rounded-md" : "justify-center py-2 px-0 rounded-md",
        "hover:bg-[#202c33] cursor-pointer group relative",
        isActive && "bg-emerald-500/10 text-emerald-500"
      )}
    >
      <div className={cn(
        "w-4 h-4 flex-shrink-0 flex items-center justify-center",
        isActive ? "text-emerald-500" : "text-[#8696a0] group-hover:text-[#e9edef]"
      )}>
        {icon}
      </div>
      
      {isOpen && (
        <span className="text-sm font-medium text-sidebar-foreground whitespace-nowrap">
          {label}
        </span>
      )}
    </div>
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