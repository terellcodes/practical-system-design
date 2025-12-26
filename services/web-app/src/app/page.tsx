"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { useChatStore } from "@/store/chat-store";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { MessageCircle } from "lucide-react";

export default function Home() {
  const router = useRouter();
  const { userId, setUserId, _hasHydrated } = useChatStore();
  const [inputUserId, setInputUserId] = useState("");

  useEffect(() => {
    if (_hasHydrated && userId) {
      router.push("/chat");
    }
  }, [_hasHydrated, userId, router]);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (inputUserId.trim()) {
      setUserId(inputUserId.trim());
      router.push("/chat");
    }
  };

  if (!_hasHydrated) {
    return null;
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-background">
      <div className="w-full max-w-md p-8">
        <div className="text-center mb-8">
          <div className="inline-flex items-center justify-center w-16 h-16 rounded-2xl bg-primary/10 mb-4">
            <MessageCircle className="w-8 h-8 text-primary" />
          </div>
          <h1 className="text-3xl font-bold tracking-tight mb-2">
            Welcome to Chat
          </h1>
          <p className="text-muted-foreground">
            Enter your user ID to continue
          </p>
        </div>

        <form onSubmit={handleSubmit} className="space-y-4">
          <Input
            type="text"
            placeholder="Enter your user ID (e.g., alice)"
            value={inputUserId}
            onChange={(e) => setInputUserId(e.target.value)}
            className="h-12 text-lg bg-card border-border"
            autoFocus
          />
          <Button
            type="submit"
            className="w-full h-12 text-lg font-medium"
            disabled={!inputUserId.trim()}
          >
            Continue
          </Button>
        </form>

        <p className="text-center text-sm text-muted-foreground mt-6">
          For testing, try: <code className="text-primary">alice</code>,{" "}
          <code className="text-primary">bob</code>, or{" "}
          <code className="text-primary">charlie</code>
        </p>
      </div>
    </div>
  );
}
