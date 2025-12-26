"use client";

import { useParams } from "next/navigation";
import { MessageCircle } from "lucide-react";

export default function ChatConversationPage() {
  const params = useParams();
  const chatId = params.chatId as string;

  return (
    <div className="flex-1 flex flex-col">
      {/* Header */}
      <div className="h-16 px-6 flex items-center border-b border-border bg-card">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-full bg-primary/20 flex items-center justify-center">
            <MessageCircle className="w-5 h-5 text-primary" />
          </div>
          <div>
            <h2 className="font-semibold">Chat</h2>
            <p className="text-xs text-muted-foreground font-mono">{chatId}</p>
          </div>
        </div>
      </div>

      {/* Messages placeholder */}
      <div className="flex-1 flex items-center justify-center text-muted-foreground">
        <p>Messages will appear here (Phase 3)</p>
      </div>

      {/* Input placeholder */}
      <div className="h-20 px-6 flex items-center border-t border-border bg-card">
        <p className="text-muted-foreground">Message input will go here (Phase 3)</p>
      </div>
    </div>
  );
}

