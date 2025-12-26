"use client";

import { useState, useCallback } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Send } from "lucide-react";

interface MessageInputProps {
  onSend: (content: string) => void;
  onUploadFile?: (file: File) => void;
  disabled?: boolean;
}

export function MessageInput({ onSend, onUploadFile, disabled }: MessageInputProps) {
  const [message, setMessage] = useState("");

  const handleSubmit = useCallback(
    (e: React.FormEvent) => {
      e.preventDefault();
      const trimmed = message.trim();
      if (trimmed && !disabled) {
        onSend(trimmed);
        setMessage("");
      }
    },
    [message, onSend, disabled]
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
            const file = e.target.files?.[0];
            if (file && onUploadFile && !disabled) {
              onUploadFile(file);
              e.target.value = "";
            }
          }}
          className="max-w-xs text-xs"
        />
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
          disabled={!message.trim() || disabled}
          className="shrink-0"
        >
          <Send className="w-4 h-4" />
        </Button>
      </div>
    </form>
  );
}

