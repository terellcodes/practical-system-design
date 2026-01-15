import { create } from "zustand";
import type { InviteWithUsers } from "@/types";

interface InviteState {
  // Pending invites received by the user
  pendingInvites: InviteWithUsers[];
  setPendingInvites: (invites: InviteWithUsers[]) => void;
  addPendingInvite: (invite: InviteWithUsers) => void;
  removePendingInvite: (inviteId: number) => void;

  // Sent invites (optional, for tracking)
  sentInvites: InviteWithUsers[];
  setSentInvites: (invites: InviteWithUsers[]) => void;
  addSentInvite: (invite: InviteWithUsers) => void;
  updateSentInviteStatus: (inviteId: number, status: string) => void;

  // Loading state
  isLoading: boolean;
  setIsLoading: (loading: boolean) => void;
}

export const useInviteStore = create<InviteState>((set) => ({
  // Pending invites
  pendingInvites: [],
  setPendingInvites: (invites) => set({ pendingInvites: invites }),
  addPendingInvite: (invite) =>
    set((state) => {
      // Avoid duplicates
      if (state.pendingInvites.some((i) => i.id === invite.id)) {
        return state;
      }
      return {
        pendingInvites: [invite, ...state.pendingInvites],
      };
    }),
  removePendingInvite: (inviteId) =>
    set((state) => ({
      pendingInvites: state.pendingInvites.filter((i) => i.id !== inviteId),
    })),

  // Sent invites
  sentInvites: [],
  setSentInvites: (invites) => set({ sentInvites: invites }),
  addSentInvite: (invite) =>
    set((state) => ({
      sentInvites: [invite, ...state.sentInvites],
    })),
  updateSentInviteStatus: (inviteId, status) =>
    set((state) => ({
      sentInvites: state.sentInvites.map((i) =>
        i.id === inviteId ? { ...i, status: status as InviteWithUsers["status"] } : i
      ),
    })),

  // Loading
  isLoading: false,
  setIsLoading: (loading) => set({ isLoading: loading }),
}));



