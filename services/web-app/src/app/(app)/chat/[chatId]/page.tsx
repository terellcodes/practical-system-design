"use client";

import { useEffect, useMemo, useCallback } from "react";
import { useParams } from "next/navigation";
import { MessageCircle } from "lucide-react";
import { useChatStore } from "@/store/chat-store";
import { useWebSocket } from "@/contexts/websocket-context";
import { MessageList } from "@/components/chat/message-list";
import { MessageInput } from "@/components/chat/message-input";
import { chatApi, normalizeLocalstackUrl, S3_BUCKET } from "@/lib/api";
import type { Message } from "@/types";

export default function ChatConversationPage() {
  const params = useParams();
  const chatId = params.chatId as string;

  const { userId, username, name, chats, messagesByChat, addMessage, bumpChat } = useChatStore();
  
  // Get WebSocket from context (single connection for all chats)
  const { isConnected, sendMessage } = useWebSocket();

  // Find the current chat to get its name
  const currentChat = useMemo(
    () => chats.find((c) => c.id === chatId),
    [chats, chatId]
  );

  // Get messages for this chat, sorted by timestamp
  const messages = useMemo(() => {
    const chatMessages = messagesByChat[chatId] || [];
    return [...chatMessages].sort(
      (a, b) =>
        new Date(a.created_at).getTime() - new Date(b.created_at).getTime()
    );
  }, [messagesByChat, chatId]);

  // Send text or text+attachment
  const handleSendMessage = useCallback(
    async (content: string, file?: File | null) => {
      if (!userId) return;

      // Text-only: use existing WebSocket send
      if (!file) {
        sendMessage(chatId, content);
        return;
      }

      // Attachment flow: request presigned URL, upload, and rely on consumer to deliver
      const contentType = file.type || "application/octet-stream";
      const fallbackContent = content || `[Attachment: ${file.name}]`;

      try {
        const uploadReq = await chatApi.requestUpload(chatId, {
          sender_id: userId,
          filename: file.name,
          content_type: contentType,
          content: fallbackContent,
          sender_username: username ?? undefined,
          sender_name: name ?? undefined,
        });

        // Add a local pending message placeholder
        const pendingMessage: Message = {
          message_id: uploadReq.message_id,
          chat_id: chatId,
          sender_id: userId,
          content: fallbackContent,
          created_at: new Date().toISOString(),
          type: "message",
          upload_status: "PENDING",
          s3_bucket: S3_BUCKET,
          s3_key: uploadReq.s3_key,
        };
        addMessage(chatId, pendingMessage);
        bumpChat(chatId);

        // PUT the file to the presigned URL (swap host for local dev)
        const uploadUrl = normalizeLocalstackUrl(uploadReq.upload_url);
        const resp = await fetch(uploadUrl, {
          method: "PUT",
          headers: { "Content-Type": contentType },
          body: file,
        });
        if (!resp.ok) {
          throw new Error(`Upload failed: HTTP ${resp.status}`);
        }
      } catch (err) {
        console.error("Upload failed", err);
        addMessage(chatId, {
          message_id: `pending-${file?.name ?? "attachment"}-${Date.now()}`,
          chat_id: chatId,
          sender_id: userId,
          content: `[Attachment failed: ${file?.name ?? "file"}]`,
          created_at: new Date().toISOString(),
          type: "system",
        });
      }
    },
    [chatId, userId, username, name, addMessage, bumpChat, sendMessage]
  );

  // Update document title with chat name
  useEffect(() => {
    if (currentChat) {
      document.title = `${currentChat.name} - Chat App`;
    }
    return () => {
      document.title = "Chat App";
    };
  }, [currentChat]);

  if (!userId) {
    return null;
  }

  return (
    <div className="flex-1 flex flex-col">
      {/* Header */}
      <div className="sticky top-0 z-10 h-16 px-6 flex items-center border-b border-border bg-card">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-full bg-primary/20 flex items-center justify-center">
            <MessageCircle className="w-5 h-5 text-primary" />
          </div>
          <div>
            <h2 className="font-semibold">
              {currentChat?.name || "Chat"}
            </h2>
            <p className="text-xs text-muted-foreground font-mono">{chatId}</p>
          </div>
        </div>
      </div>

      {/* Message List */}
      <MessageList messages={messages} currentUserId={userId} />

      {/* Message Input (sticky) */}
      <div className="sticky bottom-0 bg-card/90 backdrop-blur border-t border-border px-4 py-3">
        <MessageInput
          onSend={handleSendMessage}
          disabled={!isConnected}
        />
      </div>
    </div>
  );
}
