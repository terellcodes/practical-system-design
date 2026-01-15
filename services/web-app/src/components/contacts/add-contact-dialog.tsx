"use client";

import { useState } from "react";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { inviteApi, userApi } from "@/lib/api";
import { useInviteStore } from "@/store/invite-store";
import { UserPlus, Loader2 } from "lucide-react";

interface AddContactDialogProps {
  userId: number;
  trigger?: React.ReactNode;
}

export function AddContactDialog({ userId, trigger }: AddContactDialogProps) {
  const [open, setOpen] = useState(false);
  const [connectPin, setConnectPin] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  const { addSentInvite } = useInviteStore();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setSuccess(null);

    if (!connectPin.trim()) {
      setError("Please enter a connect PIN");
      return;
    }

    setIsLoading(true);

    try {
      const invite = await inviteApi.sendInvite(userId, connectPin.trim());
      addSentInvite(invite);
      setSuccess(`Invite sent to ${invite.invitee_name}!`);
      setConnectPin("");
      
      // Close dialog after short delay
      setTimeout(() => {
        setOpen(false);
        setSuccess(null);
      }, 1500);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to send invite");
    } finally {
      setIsLoading(false);
    }
  };

  const handleOpenChange = (newOpen: boolean) => {
    setOpen(newOpen);
    if (!newOpen) {
      setConnectPin("");
      setError(null);
      setSuccess(null);
    }
  };

  return (
    <Dialog open={open} onOpenChange={handleOpenChange}>
      <DialogTrigger asChild>
        {trigger || (
          <Button variant="outline" size="sm" className="gap-2">
            <UserPlus className="h-4 w-4" />
            Add Contact
          </Button>
        )}
      </DialogTrigger>
      <DialogContent className="sm:max-w-md">
        <DialogHeader>
          <DialogTitle>Add a Contact</DialogTitle>
          <DialogDescription>
            Enter your friend&apos;s connect PIN to send them an invite.
          </DialogDescription>
        </DialogHeader>
        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="space-y-2">
            <Label htmlFor="connect-pin">Connect PIN</Label>
            <Input
              id="connect-pin"
              placeholder="e.g., ABC123"
              value={connectPin}
              onChange={(e) => setConnectPin(e.target.value.toUpperCase())}
              disabled={isLoading}
              className="font-mono tracking-wider"
            />
          </div>

          {error && (
            <p className="text-sm text-red-500 bg-red-50 p-2 rounded">
              {error}
            </p>
          )}

          {success && (
            <p className="text-sm text-green-600 bg-green-50 p-2 rounded">
              {success}
            </p>
          )}

          <div className="flex justify-end gap-2">
            <Button
              type="button"
              variant="outline"
              onClick={() => setOpen(false)}
              disabled={isLoading}
            >
              Cancel
            </Button>
            <Button type="submit" disabled={isLoading || !connectPin.trim()}>
              {isLoading ? (
                <>
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  Sending...
                </>
              ) : (
                "Send Invite"
              )}
            </Button>
          </div>
        </form>
      </DialogContent>
    </Dialog>
  );
}



