"use client";

import { useEffect, useState } from "react";
import { useChatStore } from "@/store/chat-store";
import { userApi } from "@/lib/api";

interface CurrentUser {
  id: number;
  username: string;
  name: string;
  email: string;
  connect_pin: string;
}

interface UseCurrentUserReturn {
  user: CurrentUser | null;
  isLoading: boolean;
  error: string | null;
}

/**
 * Hook to fetch and cache the current user's data.
 * Uses the username from chat-store to fetch full user details.
 */
export function useCurrentUser(): UseCurrentUserReturn {
  console.log("useCurrentUser");
  const username = useChatStore((state) => state.username);
  const [user, setUser] = useState<CurrentUser | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  console.log("username", username);

  useEffect(() => {
    if (!username) {
      setUser(null);
      return;
    }

    const fetchUser = async () => {
      console.log("fetchUser");
      setIsLoading(true);
      setError(null);
      try {
        const userData = await userApi.getUserByUsername(username);
        setUser(userData);
      } catch (err) {
        console.error("Failed to fetch user data:", err);
        setError(err instanceof Error ? err.message : "Failed to fetch user");
        setUser(null);
      } finally {
        setIsLoading(false);
      }
    };

    fetchUser();
  }, [username]);

  return { user, isLoading, error };
}

