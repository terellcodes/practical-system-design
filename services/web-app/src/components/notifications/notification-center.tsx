"use client";

import { useEffect, useCallback } from "react";
import { useNotificationStore, type Notification } from "@/store/notification-store";
import { X, UserPlus, MessageSquarePlus, Bell } from "lucide-react";
import { Button } from "@/components/ui/button";

/**
 * Get the appropriate icon for a notification type
 */
function getNotificationIcon(type: string) {
  switch (type) {
    case "invite_received":
      return <UserPlus className="h-5 w-5 text-blue-600" />;
    case "chat_participant_added":
      return <MessageSquarePlus className="h-5 w-5 text-green-600" />;
    default:
      return <Bell className="h-5 w-5 text-gray-600" />;
  }
}

/**
 * Get the background color for a notification type
 */
function getNotificationBgColor(type: string) {
  switch (type) {
    case "invite_received":
      return "bg-blue-100";
    case "chat_participant_added":
      return "bg-green-100";
    default:
      return "bg-gray-100";
  }
}

interface NotificationItemProps {
  notification: Notification;
  onDismiss: (id: string) => void;
  onAction?: (notificationId: string, actionId: string) => void;
}

function NotificationItem({ notification, onDismiss, onAction }: NotificationItemProps) {
  // Auto-dismiss when expiresAt is reached
  useEffect(() => {
    if (notification.expiresAt) {
      const timeUntilExpiry = notification.expiresAt.getTime() - Date.now();
      if (timeUntilExpiry > 0) {
        const timer = setTimeout(() => {
          onDismiss(notification.id);
        }, timeUntilExpiry);
        return () => clearTimeout(timer);
      } else {
        // Already expired
        onDismiss(notification.id);
      }
    }
  }, [notification.id, notification.expiresAt, onDismiss]);

  return (
    <div className="bg-white border border-gray-200 rounded-lg shadow-lg p-4 max-w-sm flex items-start gap-3 animate-in slide-in-from-top-2 fade-in duration-300">
      <div
        className={`flex-shrink-0 w-10 h-10 ${getNotificationBgColor(notification.type)} rounded-full flex items-center justify-center`}
      >
        {getNotificationIcon(notification.type)}
      </div>
      <div className="flex-1 min-w-0">
        <p className="text-sm font-medium text-gray-900">{notification.title}</p>
        <p className="text-sm text-gray-500 truncate">{notification.message}</p>
        {notification.actions && notification.actions.length > 0 && (
          <div className="flex gap-2 mt-2">
            {notification.actions.map((action) => (
              <Button
                key={action.id}
                variant={action.variant || "outline"}
                size="sm"
                onClick={() => onAction?.(notification.id, action.id)}
              >
                {action.label}
              </Button>
            ))}
          </div>
        )}
      </div>
      <Button
        variant="ghost"
        size="sm"
        className="flex-shrink-0 -mt-1 -mr-1"
        onClick={() => onDismiss(notification.id)}
      >
        <X className="h-4 w-4" />
      </Button>
    </div>
  );
}

interface NotificationCenterProps {
  onAction?: (notificationId: string, actionId: string, notification: Notification) => void;
}

/**
 * NotificationCenter - Renders all notifications from the unified notification store.
 *
 * Place this component at the app/layout level to show notifications globally.
 * Notifications auto-dismiss when their expiresAt time is reached.
 */
export function NotificationCenter({ onAction }: NotificationCenterProps) {
  const { notifications, removeNotification } = useNotificationStore();

  const handleDismiss = useCallback(
    (id: string) => {
      removeNotification(id);
    },
    [removeNotification]
  );

  const handleAction = useCallback(
    (notificationId: string, actionId: string) => {
      const notification = notifications.find((n) => n.id === notificationId);
      if (notification && onAction) {
        onAction(notificationId, actionId, notification);
      }
      // Dismiss after action by default
      removeNotification(notificationId);
    },
    [notifications, onAction, removeNotification]
  );

  if (notifications.length === 0) {
    return null;
  }

  return (
    <div className="fixed top-4 right-4 z-50 space-y-2">
      {notifications.map((notification) => (
        <NotificationItem
          key={notification.id}
          notification={notification}
          onDismiss={handleDismiss}
          onAction={handleAction}
        />
      ))}
    </div>
  );
}
