"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { useChatStore } from "@/store/chat-store";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Sparkles } from "lucide-react";

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
    <div className="min-h-screen flex items-center justify-center bg-gray-950">
      <div className="w-full max-w-md p-8">
        <div className="text-center mb-8">
          <div className="inline-flex items-center justify-center w-16 h-16 rounded-2xl bg-green-600/20 mb-4">
            <Sparkles className="w-8 h-8 text-green-500" />
          </div>
          <h1 className="text-3xl font-bold tracking-tight mb-2 text-white">
            Welcome to Super App
          </h1>
          <p className="text-gray-400">
            Enter your user ID to continue
          </p>
        </div>

        <form onSubmit={handleSubmit} className="space-y-4">
          <Input
            type="text"
            placeholder="Enter your user ID (e.g., alice)"
            value={inputUserId}
            onChange={(e) => setInputUserId(e.target.value)}
            className="h-12 text-lg bg-gray-900 border-gray-800 text-white"
            autoFocus
          />
          <Button
            type="submit"
            className="w-full h-12 text-lg font-medium bg-green-600 hover:bg-green-700 text-white"
            disabled={!inputUserId.trim()}
          >
            Continue
          </Button>
        </form>

        <p className="text-center text-sm text-gray-500 mt-6">
          For testing, try: <code className="text-green-500">alice</code>,{" "}
          <code className="text-green-500">bob</code>, or{" "}
          <code className="text-green-500">charlie</code>
        </p>
      </div>
    </div>
  );
}
