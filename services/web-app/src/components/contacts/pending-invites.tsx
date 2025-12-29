"use client";

import { useEffect, useState } from "react";
import { useInviteStore } from "@/store/invite-store";
import { inviteApi } from "@/lib/api";
import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";
import { Bell, Check, X, Loader2, UserPlus } from "lucide-react";
import type { InviteWithUsers } from "@/types";

interface PendingInvitesProps {
  userId: number;
}

export function PendingInvites({ userId }: PendingInvitesProps) {
  const [open, setOpen] = useState(false);
  const {
    pendingInvites,
    setPendingInvites,
    removePendingInvite,
    isLoading,
    setIsLoading,
  } = useInviteStore();
  const [respondingTo, setRespondingTo] = useState<number | null>(null);

  // Fetch pending invites on mount
  useEffect(() => {
    const fetchInvites = async () => {
      if (!userId) return;
      setIsLoading(true);
      try {
        const invites = await inviteApi.getPendingInvites(userId);
        setPendingInvites(invites);
      } catch (error) {
        console.error("Failed to fetch pending invites:", error);
      } finally {
        setIsLoading(false);
      }
    };

    fetchInvites();
  }, [userId, setPendingInvites, setIsLoading]);

  const handleRespond = async (
    inviteId: number,
    status: "accepted" | "rejected"
  ) => {
    setRespondingTo(inviteId);
    try {
      await inviteApi.respondToInvite(userId, inviteId, status);
      removePendingInvite(inviteId);
    } catch (error) {
      console.error(`Failed to ${status} invite:`, error);
    } finally {
      setRespondingTo(null);
    }
  };

  const pendingCount = pendingInvites.length;

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogTrigger asChild>
        <Button variant="ghost" size="sm" className="relative">
          <Bell className="h-5 w-5" />
          {pendingCount > 0 && (
            <span className="absolute -top-1 -right-1 h-5 w-5 rounded-full bg-red-500 text-white text-xs flex items-center justify-center font-medium">
              {pendingCount > 9 ? "9+" : pendingCount}
            </span>
          )}
        </Button>
      </DialogTrigger>
      <DialogContent className="sm:max-w-md">
        <DialogHeader>
          <DialogTitle>Contact Invites</DialogTitle>
          <DialogDescription>
            People who want to connect with you
          </DialogDescription>
        </DialogHeader>

        <div className="py-2">
          {isLoading ? (
            <div className="flex items-center justify-center py-8">
              <Loader2 className="h-6 w-6 animate-spin text-gray-400" />
            </div>
          ) : pendingInvites.length === 0 ? (
            <p className="text-sm text-gray-500 py-8 text-center">
              No pending invites
            </p>
          ) : (
            <div className="space-y-2 max-h-80 overflow-y-auto">
              {pendingInvites.map((invite) => (
                <InviteItem
                  key={invite.id}
                  invite={invite}
                  onAccept={() => handleRespond(invite.id, "accepted")}
                  onReject={() => handleRespond(invite.id, "rejected")}
                  isLoading={respondingTo === invite.id}
                />
              ))}
            </div>
          )}
        </div>
      </DialogContent>
    </Dialog>
  );
}

interface InviteItemProps {
  invite: InviteWithUsers;
  onAccept: () => void;
  onReject: () => void;
  isLoading: boolean;
}

function InviteItem({ invite, onAccept, onReject, isLoading }: InviteItemProps) {
  return (
    <div className="flex items-center gap-3 p-3 rounded-lg border border-gray-100 bg-gray-50">
      <div className="flex-shrink-0 w-10 h-10 bg-blue-100 rounded-full flex items-center justify-center">
        <UserPlus className="h-5 w-5 text-blue-600" />
      </div>
      <div className="flex-1 min-w-0">
        <p className="text-sm font-medium text-gray-900 truncate">
          {invite.invitor_name}
        </p>
        <p className="text-xs text-gray-500">@{invite.invitor_username}</p>
      </div>
      <div className="flex gap-1">
        <Button
          variant="outline"
          size="sm"
          className="h-8 px-3 text-green-600 border-green-200 hover:bg-green-50"
          onClick={onAccept}
          disabled={isLoading}
        >
          {isLoading ? (
            <Loader2 className="h-4 w-4 animate-spin" />
          ) : (
            <Check className="h-4 w-4" />
          )}
        </Button>
        <Button
          variant="outline"
          size="sm"
          className="h-8 px-3 text-red-600 border-red-200 hover:bg-red-50"
          onClick={onReject}
          disabled={isLoading}
        >
          <X className="h-4 w-4" />
        </Button>
      </div>
    </div>
  );
}
