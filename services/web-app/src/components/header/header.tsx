'use client'

import { useChatStore } from '@/store/chat-store'
import { useCurrentUser } from '@/hooks/use-current-user'
import { AddContactDialog } from '@/components/contacts/add-contact-dialog'
import { PendingInvites } from '@/components/contacts/pending-invites'
import { NotificationCenter } from '@/components/notifications/notification-center'

export function Header() {
  const userId = useChatStore((state) => state.userId)
  const { user } = useCurrentUser()

  return (
    <>
      <NotificationCenter />
      <header className="fixed top-0 left-0 right-0 h-12 bg-[#111b21] border-b border-[#222e35] z-30">
        <div className="flex items-center justify-between h-full px-4">
          <div className="text-[#e9edef] font-medium text-lg tracking-wide">
            SupaApp
          </div>
          {userId && user && (
            <div className="flex items-center gap-3">
              {/* Pending invites bell */}
              <PendingInvites userId={user.id} />
              
              {/* Add contact button */}
              <AddContactDialog userId={user.id} />
              
              {/* User info */}
              <div className="text-[#8696a0] text-sm font-medium">
                {user.name || userId}
              </div>
            </div>
          )}
        </div>
      </header>
    </>
  )
}
