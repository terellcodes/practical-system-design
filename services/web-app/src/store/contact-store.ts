import { create } from "zustand";
import type { ContactWithUser } from "@/types";

interface ContactState {
  contacts: ContactWithUser[];
  isLoading: boolean;
  error: string | null;
  setContacts: (contacts: ContactWithUser[]) => void;
  setLoading: (loading: boolean) => void;
  setError: (error: string | null) => void;
  clearContacts: () => void;
}

export const useContactStore = create<ContactState>((set) => ({
  contacts: [],
  isLoading: false,
  error: null,
  setContacts: (contacts) => set({ contacts, error: null }),
  setLoading: (isLoading) => set({ isLoading }),
  setError: (error) => set({ error }),
  clearContacts: () => set({ contacts: [], error: null }),
}));
