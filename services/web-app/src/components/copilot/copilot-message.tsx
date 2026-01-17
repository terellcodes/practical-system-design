'use client'

import { Bot, User } from 'lucide-react'
import { cn } from '@/lib/utils'

interface CopilotMessageProps {
  role: 'user' | 'assistant'
  content: string
  timestamp?: number
}

export function CopilotMessage({ role, content, timestamp }: CopilotMessageProps) {
  const isUser = role === 'user'

  return (
    <div className={cn("flex gap-3 mb-4", isUser && "flex-row-reverse")}>
      {/* Avatar */}
      <div
        className={cn(
          "flex-shrink-0 w-8 h-8 rounded-full flex items-center justify-center",
          isUser ? "bg-[#00a884]" : "bg-[#222e35]"
        )}
      >
        {isUser ? (
          <User className="h-4 w-4 text-white" />
        ) : (
          <Bot className="h-4 w-4 text-[#8696a0]" />
        )}
      </div>

      {/* Message bubble */}
      <div
        className={cn(
          "flex-1 rounded-lg px-3 py-2 max-w-[85%]",
          isUser
            ? "bg-[#005c4b] text-[#e9edef]"
            : "bg-[#222e35] text-[#e9edef]"
        )}
      >
        <p className="text-sm whitespace-pre-wrap break-words">{content}</p>
        {timestamp && (
          <span className="text-[10px] text-[#8696a0] mt-1 block">
            {new Date(timestamp).toLocaleTimeString([], {
              hour: '2-digit',
              minute: '2-digit'
            })}
          </span>
        )}
      </div>
    </div>
  )
}
