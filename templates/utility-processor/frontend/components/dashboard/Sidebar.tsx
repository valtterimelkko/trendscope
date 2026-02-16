'use client'

import Link from 'next/link'
import { usePathname } from 'next/navigation'
import { User } from '@supabase/supabase-js'

interface SidebarProps {
  user: User
  profile: any
  workspaces: any[]
  currentWorkspace: any
}

export function Sidebar({ user, profile, workspaces, currentWorkspace }: SidebarProps) {
  const pathname = usePathname()

  const navigation = [
    {
      name: 'Inbox',
      href: '/dashboard',
      icon: InboxIcon,
      shortcut: 'G I'
    },
    {
      name: 'My Issues',
      href: '/dashboard/my-issues',
      icon: UserIcon,
      shortcut: 'G M'
    },
    {
      name: 'Projects',
      href: '/dashboard/projects',
      icon: FolderIcon,
      shortcut: 'G P'
    },
    {
      name: 'Views',
      href: '/dashboard/views',
      icon: ViewIcon,
      shortcut: 'G V'
    },
  ]

  const bottomNav = [
    {
      name: 'Settings',
      href: '/dashboard/settings',
      icon: SettingsIcon,
      shortcut: 'G S'
    },
  ]

  return (
    <aside className="w-60 bg-surface border-r border-border flex flex-col">
      {/* Workspace selector */}
      <div className="p-3 border-b border-border">
        <button className="w-full flex items-center gap-2 px-2 py-1.5 rounded-md hover:bg-surface-hover transition-colors">
          <div className="w-6 h-6 bg-primary/20 rounded flex items-center justify-center">
            <span className="text-xs font-semibold text-primary">
              {currentWorkspace?.name?.charAt(0) || 'W'}
            </span>
          </div>
          <span className="text-sm font-medium text-foreground truncate flex-1 text-left">
            {currentWorkspace?.name || 'Workspace'}
          </span>
          <ChevronIcon className="w-4 h-4 text-muted" />
        </button>
      </div>

      {/* Search trigger */}
      <div className="p-3">
        <button
          className="w-full flex items-center gap-2 px-3 py-2 bg-background border border-border rounded-lg text-muted text-sm hover:border-border-hover transition-colors"
          onClick={() => {
            // Trigger command palette
            const event = new KeyboardEvent('keydown', { key: 'k', metaKey: true })
            window.dispatchEvent(event)
          }}
        >
          <SearchIcon className="w-4 h-4" />
          <span className="flex-1 text-left">Search...</span>
          <kbd className="kbd text-xs">⌘K</kbd>
        </button>
      </div>

      {/* Main navigation */}
      <nav className="flex-1 px-3 py-2 space-y-1">
        {navigation.map((item) => {
          const isActive = pathname === item.href
          return (
            <Link
              key={item.name}
              href={item.href}
              className={`flex items-center gap-2 px-2 py-1.5 rounded-md text-sm transition-colors group ${
                isActive
                  ? 'bg-primary/10 text-primary'
                  : 'text-muted hover:text-foreground hover:bg-surface-hover'
              }`}
            >
              <item.icon className="w-4 h-4" />
              <span className="flex-1">{item.name}</span>
              <kbd className="kbd text-xs opacity-0 group-hover:opacity-100 transition-opacity">
                {item.shortcut}
              </kbd>
            </Link>
          )
        })}
      </nav>

      {/* Bottom navigation */}
      <div className="px-3 py-2 border-t border-border space-y-1">
        {bottomNav.map((item) => {
          const isActive = pathname.startsWith(item.href)
          return (
            <Link
              key={item.name}
              href={item.href}
              className={`flex items-center gap-2 px-2 py-1.5 rounded-md text-sm transition-colors group ${
                isActive
                  ? 'bg-primary/10 text-primary'
                  : 'text-muted hover:text-foreground hover:bg-surface-hover'
              }`}
            >
              <item.icon className="w-4 h-4" />
              <span className="flex-1">{item.name}</span>
              <kbd className="kbd text-xs opacity-0 group-hover:opacity-100 transition-opacity">
                {item.shortcut}
              </kbd>
            </Link>
          )
        })}
      </div>

      {/* User */}
      <div className="p-3 border-t border-border">
        <div className="flex items-center gap-2 px-2">
          <div className="w-7 h-7 bg-primary/20 rounded-full flex items-center justify-center">
            <span className="text-xs font-medium text-primary">
              {profile?.display_name?.charAt(0) || user.email?.charAt(0) || 'U'}
            </span>
          </div>
          <div className="flex-1 min-w-0">
            <p className="text-sm font-medium text-foreground truncate">
              {profile?.display_name || 'User'}
            </p>
            <p className="text-xs text-muted truncate">{user.email}</p>
          </div>
        </div>
      </div>
    </aside>
  )
}

// Icons
function InboxIcon({ className }: { className?: string }) {
  return (
    <svg className={className} fill="none" viewBox="0 0 24 24" stroke="currentColor">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M20 13V6a2 2 0 00-2-2H6a2 2 0 00-2 2v7m16 0v5a2 2 0 01-2 2H6a2 2 0 01-2-2v-5m16 0h-2.586a1 1 0 00-.707.293l-2.414 2.414a1 1 0 01-.707.293h-3.172a1 1 0 01-.707-.293l-2.414-2.414A1 1 0 006.586 13H4" />
    </svg>
  )
}

function UserIcon({ className }: { className?: string }) {
  return (
    <svg className={className} fill="none" viewBox="0 0 24 24" stroke="currentColor">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
    </svg>
  )
}

function FolderIcon({ className }: { className?: string }) {
  return (
    <svg className={className} fill="none" viewBox="0 0 24 24" stroke="currentColor">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 7v10a2 2 0 002 2h14a2 2 0 002-2V9a2 2 0 00-2-2h-6l-2-2H5a2 2 0 00-2 2z" />
    </svg>
  )
}

function ViewIcon({ className }: { className?: string }) {
  return (
    <svg className={className} fill="none" viewBox="0 0 24 24" stroke="currentColor">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 10h16M4 14h16M4 18h16" />
    </svg>
  )
}

function SettingsIcon({ className }: { className?: string }) {
  return (
    <svg className={className} fill="none" viewBox="0 0 24 24" stroke="currentColor">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z" />
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
    </svg>
  )
}

function SearchIcon({ className }: { className?: string }) {
  return (
    <svg className={className} fill="none" viewBox="0 0 24 24" stroke="currentColor">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
    </svg>
  )
}

function ChevronIcon({ className }: { className?: string }) {
  return (
    <svg className={className} fill="none" viewBox="0 0 24 24" stroke="currentColor">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 9l4-4 4 4m0 6l-4 4-4-4" />
    </svg>
  )
}
