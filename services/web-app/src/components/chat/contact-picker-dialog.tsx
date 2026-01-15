"use client";

import { useState } from "react";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Loader2, UserPlus, Search } from "lucide-react";
import { useContactStore } from "@/store/contact-store";

interface ContactPickerDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onSelectContacts: (contactIds: number[]) => Promise<void>;
  excludeUserIds?: number[]; // Don't show users already in chat
}

export function ContactPickerDialog({
  open,
  onOpenChange,
  onSelectContacts,
  excludeUserIds = [],
}: ContactPickerDialogProps) {
  const { contacts, isLoading: contactsLoading } = useContactStore();
  const [selectedIds, setSelectedIds] = useState<Set<number>>(new Set());
  const [searchQuery, setSearchQuery] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Filter contacts
  const availableContacts = contacts.filter(
    (c) => !excludeUserIds.includes(c.contact_id)
  );

  const filteredContacts = availableContacts.filter((contact) =>
    contact.contact_name.toLowerCase().includes(searchQuery.toLowerCase()) ||
    contact.contact_username.toLowerCase().includes(searchQuery.toLowerCase())
  );

  const toggleContact = (contactId: number) => {
    const newSelected = new Set(selectedIds);
    if (newSelected.has(contactId)) {
      newSelected.delete(contactId);
    } else {
      newSelected.add(contactId);
    }
    setSelectedIds(newSelected);
  };

  const handleSubmit = async () => {
    if (selectedIds.size === 0) {
      // Skip if no contacts selected
      onOpenChange(false);
      return;
    }

    setIsSubmitting(true);
    setError(null);

    try {
      await onSelectContacts(Array.from(selectedIds));
      setSelectedIds(new Set());
      setSearchQuery("");
      onOpenChange(false);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to add contacts");
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleOpenChange = (open: boolean) => {
    if (!open && !isSubmitting) {
      setSelectedIds(new Set());
      setSearchQuery("");
      setError(null);
    }
    onOpenChange(open);
  };

  return (
    <Dialog open={open} onOpenChange={handleOpenChange}>
      <DialogContent className="sm:max-w-md">
        <DialogHeader>
          <DialogTitle>Add Contacts to Chat</DialogTitle>
          <DialogDescription>
            Select contacts to add to this chat. Skip to continue without adding anyone.
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-4 py-4">
          {/* Search */}
          <div className="relative">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
            <Input
              placeholder="Search contacts..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="pl-9"
              disabled={isSubmitting}
            />
          </div>

          {/* Contact List */}
          {contactsLoading ? (
            <div className="flex items-center justify-center py-8">
              <Loader2 className="w-6 h-6 animate-spin text-muted-foreground" />
            </div>
          ) : filteredContacts.length === 0 ? (
            <div className="text-center py-8 text-muted-foreground">
              <UserPlus className="w-12 h-12 mx-auto mb-3 opacity-50" />
              <p className="text-sm">
                {availableContacts.length === 0
                  ? "No contacts available"
                  : "No contacts match your search"}
              </p>
            </div>
          ) : (
            <ScrollArea className="h-[300px] pr-4">
              <div className="space-y-2">
                {filteredContacts.map((contact) => (
                  <div
                    key={contact.contact_id}
                    className="flex items-center gap-3 p-3 rounded-lg border border-border hover:bg-accent/50 cursor-pointer transition-colors"
                    onClick={() => toggleContact(contact.contact_id)}
                  >
                    <input
                      type="checkbox"
                      checked={selectedIds.has(contact.contact_id)}
                      onChange={() => toggleContact(contact.contact_id)}
                      disabled={isSubmitting}
                      className="w-4 h-4 rounded border-gray-300"
                    />
                    <div className="flex-1 min-w-0">
                      <p className="font-medium text-sm truncate">
                        {contact.contact_name}
                      </p>
                      <p className="text-xs text-muted-foreground">
                        @{contact.contact_username}
                      </p>
                    </div>
                  </div>
                ))}
              </div>
            </ScrollArea>
          )}

          {/* Selection Count */}
          {selectedIds.size > 0 && (
            <p className="text-sm text-muted-foreground">
              {selectedIds.size} contact{selectedIds.size > 1 ? "s" : ""} selected
            </p>
          )}

          {/* Error */}
          {error && (
            <p className="text-sm text-destructive bg-destructive/10 p-2 rounded">
              {error}
            </p>
          )}
        </div>

        <DialogFooter>
          <Button
            type="button"
            variant="outline"
            onClick={() => handleOpenChange(false)}
            disabled={isSubmitting}
          >
            Skip
          </Button>
          <Button
            type="button"
            onClick={handleSubmit}
            disabled={isSubmitting}
          >
            {isSubmitting ? (
              <>
                <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                Adding...
              </>
            ) : selectedIds.size > 0 ? (
              `Add ${selectedIds.size} Contact${selectedIds.size > 1 ? "s" : ""}`
            ) : (
              "Skip"
            )}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
