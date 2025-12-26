"use client";

import { useState } from "react";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Loader2 } from "lucide-react";

interface CreateChatDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onCreateChat: (name: string) => Promise<void>;
}

export function CreateChatDialog({
  open,
  onOpenChange,
  onCreateChat,
}: CreateChatDialogProps) {
  const [chatName, setChatName] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!chatName.trim()) return;

    setIsLoading(true);
    setError(null);

    try {
      await onCreateChat(chatName.trim());
      setChatName("");
      onOpenChange(false);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to create chat");
    } finally {
      setIsLoading(false);
    }
  };

  const handleOpenChange = (open: boolean) => {
    if (!open) {
      setChatName("");
      setError(null);
    }
    onOpenChange(open);
  };

  return (
    <Dialog open={open} onOpenChange={handleOpenChange}>
      <DialogContent className="sm:max-w-md">
        <DialogHeader>
          <DialogTitle>Create New Chat</DialogTitle>
          <DialogDescription>
            Enter a name for your new chat group.
          </DialogDescription>
        </DialogHeader>

        <form onSubmit={handleSubmit}>
          <div className="space-y-4 py-4">
            <Input
              placeholder="Chat name (e.g., Team Chat)"
              value={chatName}
              onChange={(e) => setChatName(e.target.value)}
              disabled={isLoading}
              autoFocus
            />
            {error && (
              <p className="text-sm text-destructive">{error}</p>
            )}
          </div>

          <DialogFooter>
            <Button
              type="button"
              variant="outline"
              onClick={() => handleOpenChange(false)}
              disabled={isLoading}
            >
              Cancel
            </Button>
            <Button type="submit" disabled={!chatName.trim() || isLoading}>
              {isLoading ? (
                <>
                  <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                  Creating...
                </>
              ) : (
                "Create Chat"
              )}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
}

