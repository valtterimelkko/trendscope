'use client'

import { useEffect, useState, useCallback } from 'react'
import { Command } from 'cmdk'
import {
  Plus,
  Search,
  Settings,
  Users,
  LogOut,
  Home,
  LayoutGrid,
  List,
  Calendar,
} from 'lucide-react'
import { useRouter } from 'next/navigation'

interface CommandPaletteProps {
  isOpen: boolean
  onClose: () => void
}

export function CommandPalette({ isOpen, onClose }: CommandPaletteProps) {
  const router = useRouter()
  const [search, setSearch] = useState('')

  // Close on escape
  useEffect(() => {
    const down = (e: KeyboardEvent) => {
      if (e.key === 'Escape') {
        onClose()
      }
    }
    document.addEventListener('keydown', down)
    return () => document.removeEventListener('keydown', down)
  }, [onClose])

  const runCommand = useCallback((command: () => void) => {
    onClose()
    command()
  }, [onClose])

  if (!isOpen) return null

  return (
    <div className="command-palette">
      <div className="command-palette-backdrop" onClick={onClose} />
      <Command className="command-palette-content" shouldFilter>
        <div className="flex items-center border-b border-border px-3">
          <Search className="h-4 w-4 text-text-muted mr-2" />
          <Command.Input
            value={search}
            onValueChange={setSearch}
            placeholder="Type a command or search..."
            className="flex-1 py-3 bg-transparent text-sm placeholder-text-muted focus:outline-none"
            autoFocus
          />
          <kbd className="text-xs">esc</kbd>
        </div>

        <Command.List className="max-h-[300px] overflow-y-auto p-2">
          <Command.Empty className="py-6 text-center text-sm text-text-muted">
            No results found.
          </Command.Empty>

          <Command.Group heading="Actions" className="mb-2">
            <Command.Item
              onSelect={() => runCommand(() => console.log('New issue'))}
              className="flex items-center gap-3 px-3 py-2 text-sm rounded-md cursor-pointer hover:bg-surface-hover aria-selected:bg-surface-hover"
            >
              <Plus className="h-4 w-4" />
              <span>Create new issue</span>
              <kbd className="ml-auto">C</kbd>
            </Command.Item>
          </Command.Group>

          <Command.Group heading="Navigation" className="mb-2">
            <Command.Item
              onSelect={() => runCommand(() => router.push('/dashboard'))}
              className="flex items-center gap-3 px-3 py-2 text-sm rounded-md cursor-pointer hover:bg-surface-hover aria-selected:bg-surface-hover"
            >
              <Home className="h-4 w-4" />
              <span>Go to Dashboard</span>
            </Command.Item>
            <Command.Item
              onSelect={() => runCommand(() => router.push('/settings'))}
              className="flex items-center gap-3 px-3 py-2 text-sm rounded-md cursor-pointer hover:bg-surface-hover aria-selected:bg-surface-hover"
            >
              <Settings className="h-4 w-4" />
              <span>Go to Settings</span>
            </Command.Item>
            <Command.Item
              onSelect={() => runCommand(() => router.push('/settings/team'))}
              className="flex items-center gap-3 px-3 py-2 text-sm rounded-md cursor-pointer hover:bg-surface-hover aria-selected:bg-surface-hover"
            >
              <Users className="h-4 w-4" />
              <span>Go to Team</span>
            </Command.Item>
          </Command.Group>

          <Command.Group heading="View" className="mb-2">
            <Command.Item
              onSelect={() => runCommand(() => console.log('Board view'))}
              className="flex items-center gap-3 px-3 py-2 text-sm rounded-md cursor-pointer hover:bg-surface-hover aria-selected:bg-surface-hover"
            >
              <LayoutGrid className="h-4 w-4" />
              <span>Switch to Board view</span>
            </Command.Item>
            <Command.Item
              onSelect={() => runCommand(() => console.log('List view'))}
              className="flex items-center gap-3 px-3 py-2 text-sm rounded-md cursor-pointer hover:bg-surface-hover aria-selected:bg-surface-hover"
            >
              <List className="h-4 w-4" />
              <span>Switch to List view</span>
            </Command.Item>
            <Command.Item
              onSelect={() => runCommand(() => console.log('Calendar view'))}
              className="flex items-center gap-3 px-3 py-2 text-sm rounded-md cursor-pointer hover:bg-surface-hover aria-selected:bg-surface-hover"
            >
              <Calendar className="h-4 w-4" />
              <span>Switch to Calendar view</span>
            </Command.Item>
          </Command.Group>

          <Command.Separator className="my-2 h-px bg-border" />

          <Command.Item
            onSelect={() => runCommand(() => console.log('Sign out'))}
            className="flex items-center gap-3 px-3 py-2 text-sm rounded-md cursor-pointer hover:bg-surface-hover aria-selected:bg-surface-hover text-error"
          >
            <LogOut className="h-4 w-4" />
            <span>Sign out</span>
          </Command.Item>
        </Command.List>
      </Command>
    </div>
  )
}
