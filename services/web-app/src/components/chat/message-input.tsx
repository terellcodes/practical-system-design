"use client";

import { useState, useCallback } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Send } from "lucide-react";

interface MessageInputProps {
  onSend: (content: string, file?: File | null) => void;
  disabled?: boolean;
}

export function MessageInput({ onSend, disabled }: MessageInputProps) {
  const [message, setMessage] = useState("");
  const [file, setFile] = useState<File | null>(null);

  const handleSubmit = useCallback(
    (e: React.FormEvent) => {
      e.preventDefault();
      const trimmed = message.trim();
      if (!disabled && (trimmed || file)) {
        onSend(trimmed, file);
        setMessage("");
        setFile(null);
      }
    },
    [message, file, onSend, disabled]
  );

  const handleKeyDown = useCallback(
    (e: React.KeyboardEvent) => {
      if (e.key === "Enter" && !e.shiftKey) {
        e.preventDefault();
        handleSubmit(e);
      }
    },
    [handleSubmit]
  );

  return (
    <form
      onSubmit={handleSubmit}
      className="p-4 border-t border-border bg-card"
    >
      <div className="flex items-center gap-2">
        <Input
          type="file"
          accept="image/*,video/*"
          disabled={disabled}
          onChange={(e) => {
            const selected = e.target.files?.[0] ?? null;
            setFile(selected);
          }}
          className="max-w-xs text-xs"
        />
        {file && (
          <div className="flex items-center gap-2 text-xs bg-muted px-2 py-1 rounded">
            <span className="truncate max-w-[140px]">{file.name}</span>
            <Button
              type="button"
              variant="ghost"
              size="sm"
              onClick={() => setFile(null)}
              disabled={disabled}
              className="h-6 px-2"
            >
              Clear
            </Button>
          </div>
        )}
        <Input
          type="text"
          placeholder="Type a message..."
          value={message}
          onChange={(e) => setMessage(e.target.value)}
          onKeyDown={handleKeyDown}
          disabled={disabled}
          className="flex-1 bg-muted border-0"
          autoComplete="off"
        />
        <Button
          type="submit"
          size="icon"
          disabled={(!message.trim() && !file) || disabled}
          className="shrink-0"
        >
          <Send className="w-4 h-4" />
        </Button>
      </div>
    </form>
  );
}

