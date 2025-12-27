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
  const isImageKey = (key: string) => {
    const lower = key.toLowerCase();
    return (
      lower.endsWith(".jpg") ||
      lower.endsWith(".jpeg") ||
      lower.endsWith(".png") ||
      lower.endsWith(".gif") ||
      lower.endsWith(".webp") ||
      lower.endsWith(".heic") ||
      lower.endsWith(".heif") ||
      lower.endsWith(".avif")
    );
  };

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
        
        {/* Attachment preview (images) */}
        {message.s3_bucket && message.s3_key && isImageKey(message.s3_key) && (
          <div className="mt-1 -mx-3 overflow-hidden rounded-lg border border-border/20 bg-black/5">
            <a
              href={buildS3PublicUrl(message.s3_bucket, message.s3_key)}
              target="_blank"
              rel="noreferrer"
            >
              <img
                src={buildS3PublicUrl(message.s3_bucket, message.s3_key)}
                alt="Attachment"
                className="w-full h-auto object-cover max-h-[360px] bg-muted"
              />
            </a>
          </div>
        )}

        {/* Message content */}
        {message.content && (
          <p className="text-sm whitespace-pre-wrap break-words mt-2">
            {message.content}
          </p>
        )}

        {/* Attachment link + status (for non-image or status badge) */}
        {message.s3_bucket && message.s3_key && (
          <div className="mt-2 flex items-center gap-2 text-xs">
            <a
              className={cn(
                "underline",
                isOwn ? "text-primary-foreground" : "text-primary"
              )}
              href={buildS3PublicUrl(message.s3_bucket, message.s3_key)}
              target="_blank"
              rel="noreferrer"
            >
              {isImageKey(message.s3_key) ? "View image" : "Attachment"}
            </a>
            {message.upload_status && (
              <span className="text-[10px] uppercase tracking-wide">
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

