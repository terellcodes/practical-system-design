"use client";

import { useEffect } from "react";
import { useInviteStore } from "@/store/invite-store";
import { X, UserPlus } from "lucide-react";
import { Button } from "@/components/ui/button";

export function InviteNotification() {
  const {
    showInviteNotification,
    latestInvite,
    setShowInviteNotification,
  } = useInviteStore();

  // Auto-hide after 5 seconds
  useEffect(() => {
    if (showInviteNotification) {
      const timer = setTimeout(() => {
        setShowInviteNotification(false);
      }, 5000);
      return () => clearTimeout(timer);
    }
  }, [showInviteNotification, setShowInviteNotification]);

  if (!showInviteNotification || !latestInvite) {
    return null;
  }

  return (
    <div className="fixed top-4 right-4 z-50 animate-in slide-in-from-top-2 fade-in duration-300">
      <div className="bg-white border border-gray-200 rounded-lg shadow-lg p-4 max-w-sm flex items-start gap-3">
        <div className="flex-shrink-0 w-10 h-10 bg-blue-100 rounded-full flex items-center justify-center">
          <UserPlus className="h-5 w-5 text-blue-600" />
        </div>
        <div className="flex-1 min-w-0">
          <p className="text-sm font-medium text-gray-900">
            New Contact Invite
          </p>
          <p className="text-sm text-gray-500 truncate">
            <span className="font-medium">{latestInvite.invitor_name}</span>
            {" "}wants to connect with you
          </p>
        </div>
        <Button
          variant="ghost"
          size="sm"
          className="flex-shrink-0 -mt-1 -mr-1"
          onClick={() => setShowInviteNotification(false)}
        >
          <X className="h-4 w-4" />
        </Button>
      </div>
    </div>
  );
}

