"use client";

import { useCallback, useRef, useState } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Dialog, DialogContent, DialogTitle, DialogTrigger } from "@/components/ui/dialog";
import { Image, Paperclip, Plus, Send, X } from "lucide-react";

interface MessageInputProps {
  onSend: (content: string, file?: File | null) => void;
  disabled?: boolean;
}

export function MessageInput({ onSend, disabled }: MessageInputProps) {
  const [message, setMessage] = useState("");
  const [file, setFile] = useState<File | null>(null);
  const [pickerOpen, setPickerOpen] = useState(false);
  const fileInputRef = useRef<HTMLInputElement | null>(null);

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
      {/* Hidden file input */}
      <input
        ref={fileInputRef}
        type="file"
        accept="image/*,video/*"
        className="hidden"
        onChange={(e) => {
          const selected = e.target.files?.[0] ?? null;
          if (selected) {
            setFile(selected);
          }
          setPickerOpen(false);
        }}
      />

      <div className="flex items-center gap-2">
        <Dialog open={pickerOpen} onOpenChange={setPickerOpen}>
          <DialogTrigger asChild>
            <Button
              type="button"
              size="icon"
              variant="ghost"
              disabled={disabled}
              className="shrink-0"
            >
              <Plus className="w-5 h-5" />
            </Button>
          </DialogTrigger>
          <DialogContent className="max-w-xs p-4" showCloseButton>
            <div className="space-y-3">
              <DialogTitle className="text-sm font-semibold">Add</DialogTitle>
              <div className="flex flex-col gap-2">
                <Button
                  type="button"
                  variant="outline"
                  className="justify-start gap-2"
                  onClick={() => fileInputRef.current?.click()}
                  disabled={disabled}
                >
                  <Image className="w-4 h-4" />
                  Photos & videos
                </Button>
                <Button
                  type="button"
                  variant="outline"
                  className="justify-start gap-2"
                  onClick={() => fileInputRef.current?.click()}
                  disabled={disabled}
                >
                  <Paperclip className="w-4 h-4" />
                  File
                </Button>
              </div>
            </div>
          </DialogContent>
        </Dialog>

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
              <X className="w-3 h-3" />
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

