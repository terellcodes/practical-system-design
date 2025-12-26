"use client";

import { cn } from "@/lib/utils";
import { buildS3PublicUrl } from "@/lib/api";
import type { Message } from "@/types";

interface MessageBubbleProps {
  message: Message;
  isOwn: boolean;
}

function formatTime(dateString: string): string {
  const date = new Date(dateString);
  return date.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
}

export function MessageBubble({ message, isOwn }: MessageBubbleProps) {
  // System messages (user joined/left)
  if (message.type === "system") {
    return (
      <div className="flex justify-center my-2">
        <span className="text-xs text-muted-foreground bg-muted/50 px-3 py-1 rounded-full">
          {message.content}
        </span>
      </div>
    );
  }

  return (
    <div
      className={cn("flex mb-2", isOwn ? "justify-end" : "justify-start")}
    >
      <div
        className={cn(
          "max-w-[70%] rounded-2xl px-4 py-2",
          isOwn
            ? "bg-primary text-primary-foreground rounded-br-md"
            : "bg-card text-card-foreground rounded-bl-md"
        )}
      >
        {/* Sender name for other users */}
        {!isOwn && (
          <p className="text-xs font-medium text-primary mb-1">
            {message.sender_id}
          </p>
        )}
        
        {/* Message content */}
        <p className="text-sm whitespace-pre-wrap break-words">
          {message.content}
        </p>

        {/* Attachment (link) */}
        {message.s3_bucket && message.s3_key && (
          <div className="mt-2">
            <a
              className={cn(
                "text-xs underline",
                isOwn ? "text-primary-foreground" : "text-primary"
              )}
              href={buildS3PublicUrl(message.s3_bucket, message.s3_key)}
              target="_blank"
              rel="noreferrer"
            >
              Attachment
            </a>
            {message.upload_status && (
              <span className="ml-2 text-[10px] uppercase tracking-wide">
                {message.upload_status}
              </span>
            )}
          </div>
        )}
        
        {/* Timestamp */}
        <p
          className={cn(
            "text-[10px] mt-1 text-right",
            isOwn ? "text-primary-foreground/70" : "text-muted-foreground"
          )}
        >
          {formatTime(message.created_at)}
        </p>
      </div>
    </div>
  );
}

