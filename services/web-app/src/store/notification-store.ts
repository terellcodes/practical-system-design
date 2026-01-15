import { create } from "zustand";

/**
 * Notification action that can be attached to a notification
 */
export interface NotificationAction {
  id: string;
  label: string;
  variant?: "default" | "outline" | "ghost";
}

/**
 * Unified notification type for the super app.
 * Supports multiple sources (chat, contacts, games, social, system)
 * and priority levels for future enhancements.
 */
export interface Notification {
  id: string;
  type: string; // "invite_received" | "chat_participant_added" | etc.
  source: "chat" | "contacts" | "games" | "social" | "system";
  priority: "low" | "medium" | "high" | "critical";
  category: string;
  title: string;
  message: string;
  data: Record<string, unknown>;
  actions?: NotificationAction[];
  createdAt: Date;
  expiresAt?: Date;
}

interface NotificationState {
  notifications: Notification[];
  addNotification: (notification: Omit<Notification, "id" | "createdAt">) => void;
  removeNotification: (id: string) => void;
  clearAll: () => void;
}

/**
 * Generates a unique notification ID
 */
function generateNotificationId(): string {
  return `notif-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
}

/**
 * Generate a deduplication key from notification data.
 * Used to prevent duplicate notifications for the same event.
 */
function getDeduplicationKey(notification: Omit<Notification, "id" | "createdAt">): string {
  // Use type + unique identifier from data if available
  const uniqueId = notification.data?.invite_id
    || notification.data?.chat_id
    || notification.data?.id
    || "";
  return `${notification.type}-${uniqueId}`;
}

export const useNotificationStore = create<NotificationState>((set, get) => ({
  notifications: [],

  addNotification: (notification) => {
    const state = get();
    const dedupeKey = getDeduplicationKey(notification);

    // Check for duplicate within last 5 seconds (prevents rapid duplicate notifications)
    const fiveSecondsAgo = Date.now() - 5000;
    const isDuplicate = state.notifications.some((n) => {
      const existingKey = getDeduplicationKey(n);
      return existingKey === dedupeKey && n.createdAt.getTime() > fiveSecondsAgo;
    });

    if (isDuplicate) {
      console.log(`Duplicate notification suppressed: ${dedupeKey}`);
      return;
    }

    const newNotification: Notification = {
      ...notification,
      id: generateNotificationId(),
      createdAt: new Date(),
    };

    set({
      notifications: [newNotification, ...state.notifications],
    });
  },

  removeNotification: (id) =>
    set((state) => ({
      notifications: state.notifications.filter((n) => n.id !== id),
    })),

  clearAll: () => set({ notifications: [] }),
}));
