'use client'

import { useState, useEffect, useRef } from 'react'
import { Send, Bot } from 'lucide-react'
import { ScrollArea } from '@/components/ui/scroll-area'
import { Input } from '@/components/ui/input'
import { Button } from '@/components/ui/button'
import { CopilotMessage } from './copilot-message'
import { useCopilotStore } from '@/store/copilot-store'

function TypingIndicator() {
  return (
    <div className="flex gap-3 mb-4">
      <div className="flex-shrink-0 w-8 h-8 rounded-full flex items-center justify-center bg-[#222e35]">
        <Bot className="h-4 w-4 text-[#8696a0]" />
      </div>
      <div className="flex-1 rounded-lg px-3 py-2 bg-[#222e35]">
        <div className="flex gap-1 items-center">
          <div className="w-2 h-2 bg-[#8696a0] rounded-full animate-bounce" style={{ animationDelay: '0ms' }} />
          <div className="w-2 h-2 bg-[#8696a0] rounded-full animate-bounce" style={{ animationDelay: '150ms' }} />
          <div className="w-2 h-2 bg-[#8696a0] rounded-full animate-bounce" style={{ animationDelay: '300ms' }} />
        </div>
      </div>
    </div>
  )
}

export function CopilotChat() {
  const [inputValue, setInputValue] = useState('')
  const messages = useCopilotStore((state) => state.messages)
  const isLoading = useCopilotStore((state) => state.isLoading)
  const sendMessage = useCopilotStore((state) => state.sendMessage)
  const scrollAreaRef = useRef<HTMLDivElement>(null)
  const messagesEndRef = useRef<HTMLDivElement>(null)
  const inputRef = useRef<HTMLInputElement>(null)

  // Auto-focus input when component mounts
  useEffect(() => {
    inputRef.current?.focus()
  }, [])

  // Auto-scroll to bottom when messages change
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages, isLoading])

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!inputValue.trim() || isLoading) return

    const message = inputValue
    setInputValue('')
    await sendMessage(message)
  }

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSubmit(e)
    }
  }

  return (
    <div className="flex flex-col h-full">
      {/* Messages area */}
      <ScrollArea className="flex-1 px-4 py-4" ref={scrollAreaRef}>
        <div className="space-y-1">
          {messages.length === 0 ? (
            <div className="flex flex-col items-center justify-center h-full text-center py-8">
              <Bot className="h-12 w-12 text-[#8696a0] mb-4" />
              <h3 className="text-[#e9edef] font-medium text-lg mb-2">Welcome to AI Copilot</h3>
              <p className="text-[#8696a0] text-sm max-w-sm">
                Ask me anything about your app, get help with features, or just chat. I'm here to help!
              </p>
            </div>
          ) : (
            <>
              {messages.map((message) => (
                <CopilotMessage
                  key={message.id}
                  role={message.role}
                  content={message.content}
                  timestamp={message.timestamp}
                />
              ))}
              {isLoading && <TypingIndicator />}
              <div ref={messagesEndRef} />
            </>
          )}
        </div>
      </ScrollArea>

      {/* Input area */}
      <div className="border-t border-[#222e35] p-4">
        <form onSubmit={handleSubmit} className="flex gap-2">
          <Input
            ref={inputRef}
            value={inputValue}
            onChange={(e) => setInputValue(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Ask me anything..."
            disabled={isLoading}
            className="flex-1 bg-[#222e35] border-[#2a3942] text-[#e9edef] placeholder:text-[#8696a0] disabled:opacity-50"
          />
          <Button
            type="submit"
            size="icon"
            disabled={!inputValue.trim() || isLoading}
            className="bg-[#00a884] hover:bg-[#00a884]/90 disabled:opacity-50"
          >
            <Send className="h-4 w-4" />
          </Button>
        </form>
      </div>
    </div>
  )
}
