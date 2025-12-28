'use client'

import { useState } from 'react'
import { UserPlus, Check, X } from 'lucide-react'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { motion, AnimatePresence } from 'framer-motion'

interface AddUserDialogProps {
  open: boolean
  onOpenChange: (open: boolean) => void
}

export function AddUserDialog({ open, onOpenChange }: AddUserDialogProps) {
  const [connectPin, setConnectPin] = useState('')
  const [isValidating, setIsValidating] = useState(false)
  const [error, setError] = useState('')
  const [foundUser, setFoundUser] = useState<{ name: string; username: string } | null>(null)

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError('')
    setFoundUser(null)

    // Validate format: 8-character hexadecimal
    const hexRegex = /^[0-9A-F]{8}$/i
    if (!hexRegex.test(connectPin)) {
      setError('PIN must be 8 characters using 0-9 and A-F')
      return
    }

    setIsValidating(true)

    // Simulate finding user (frontend only for now)
    setTimeout(() => {
      // Mock response - in production this would call the backend
      if (connectPin === '1234ABCD') {
        setFoundUser({ name: 'Alice Johnson', username: 'alice' })
      } else if (connectPin === 'DEADBEEF') {
        setFoundUser({ name: 'Bob Smith', username: 'bob' })
      } else {
        setError('No user found with this PIN')
      }
      setIsValidating(false)
    }, 1000)
  }

  const handleAddUser = () => {
    // In production, this would add the user to contacts/connections
    console.log('Adding user:', foundUser)
    handleClose()
  }

  const handleClose = () => {
    setConnectPin('')
    setError('')
    setFoundUser(null)
    onOpenChange(false)
  }

  return (
    <Dialog open={open} onOpenChange={handleClose}>
      <DialogContent className="sm:max-w-md">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <UserPlus className="w-5 h-5" />
            Add User by Connect PIN
          </DialogTitle>
          <DialogDescription>
            Enter an 8-character hexadecimal PIN to connect with another user
          </DialogDescription>
        </DialogHeader>

        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="space-y-2">
            <Label htmlFor="connect-pin">Connect PIN</Label>
            <Input
              id="connect-pin"
              value={connectPin}
              onChange={(e) => setConnectPin(e.target.value.toUpperCase())}
              placeholder="e.g., 1234ABCD"
              maxLength={8}
              disabled={isValidating}
              className="font-mono text-lg tracking-wider"
            />
            {error && (
              <motion.p
                initial={{ opacity: 0, y: -10 }}
                animate={{ opacity: 1, y: 0 }}
                className="text-sm text-red-500"
              >
                {error}
              </motion.p>
            )}
          </div>

          <AnimatePresence mode="wait">
            {foundUser ? (
              <motion.div
                key="found"
                initial={{ opacity: 0, scale: 0.95 }}
                animate={{ opacity: 1, scale: 1 }}
                exit={{ opacity: 0, scale: 0.95 }}
                className="p-4 bg-green-500/10 border border-green-500/30 rounded-lg"
              >
                <div className="flex items-center justify-between">
                  <div>
                    <p className="font-medium text-green-400">User Found!</p>
                    <p className="text-sm text-gray-300">{foundUser.name}</p>
                    <p className="text-xs text-gray-400">@{foundUser.username}</p>
                  </div>
                  <Check className="w-5 h-5 text-green-500" />
                </div>
              </motion.div>
            ) : null}
          </AnimatePresence>

          <div className="flex gap-2 justify-end">
            <Button
              type="button"
              variant="outline"
              onClick={handleClose}
              disabled={isValidating}
            >
              Cancel
            </Button>
            {foundUser ? (
              <Button
                type="button"
                onClick={handleAddUser}
                className="bg-green-600 hover:bg-green-700"
              >
                Add User
              </Button>
            ) : (
              <Button
                type="submit"
                disabled={!connectPin || isValidating}
              >
                {isValidating ? 'Searching...' : 'Search'}
              </Button>
            )}
          </div>
        </form>
      </DialogContent>
    </Dialog>
  )
}