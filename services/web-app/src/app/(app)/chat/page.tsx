"use client";

import { MessageCircle } from "lucide-react";

export default function ChatPage() {
  return (
    <div className="flex-1 flex items-center justify-center bg-card/30">
      <div className="text-center">
        <div className="inline-flex items-center justify-center w-20 h-20 rounded-2xl bg-muted mb-4">
          <MessageCircle className="w-10 h-10 text-muted-foreground" />
        </div>
        <h2 className="text-xl font-semibold mb-2">Select a chat</h2>
        <p className="text-muted-foreground">
          Choose a conversation from the sidebar or create a new one
        </p>
      </div>
    </div>
  );
}

