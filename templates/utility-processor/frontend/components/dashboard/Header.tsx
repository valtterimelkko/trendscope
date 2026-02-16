'use client'

import { User } from '@supabase/supabase-js'
import { usePathname } from 'next/navigation'

interface HeaderProps {
  user: User
  profile: any
  currentWorkspace: any
}

export function Header({ user, profile, currentWorkspace }: HeaderProps) {
  const pathname = usePathname()

  // Determine page title based on pathname
  const getPageTitle = () => {
    if (pathname === '/dashboard') return 'Inbox'
    if (pathname === '/dashboard/my-issues') return 'My Issues'
    if (pathname === '/dashboard/projects') return 'Projects'
    if (pathname === '/dashboard/views') return 'Views'
    if (pathname.startsWith('/dashboard/settings')) return 'Settings'
    return 'Dashboard'
  }

  return (
    <header className="h-12 border-b border-border flex items-center px-4 gap-4">
      {/* Breadcrumb / Page title */}
      <div className="flex items-center gap-2">
        <h1 className="text-sm font-medium text-foreground">{getPageTitle()}</h1>
      </div>

      {/* Spacer */}
      <div className="flex-1" />

      {/* Quick actions */}
      <div className="flex items-center gap-2">
        {/* New issue button */}
        <button className="flex items-center gap-1.5 px-3 py-1.5 bg-primary hover:bg-primary-hover text-white text-sm font-medium rounded-md transition-colors">
          <PlusIcon className="w-4 h-4" />
          <span>New Issue</span>
          <kbd className="text-xs opacity-70 ml-1">C</kbd>
        </button>

        {/* Filter */}
        <button className="p-1.5 text-muted hover:text-foreground hover:bg-surface-hover rounded-md transition-colors">
          <FilterIcon className="w-4 h-4" />
        </button>

        {/* View options */}
        <button className="p-1.5 text-muted hover:text-foreground hover:bg-surface-hover rounded-md transition-colors">
          <ViewOptionsIcon className="w-4 h-4" />
        </button>
      </div>
    </header>
  )
}

function PlusIcon({ className }: { className?: string }) {
  return (
    <svg className={className} fill="none" viewBox="0 0 24 24" stroke="currentColor">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
    </svg>
  )
}

function FilterIcon({ className }: { className?: string }) {
  return (
    <svg className={className} fill="none" viewBox="0 0 24 24" stroke="currentColor">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 4a1 1 0 011-1h16a1 1 0 011 1v2.586a1 1 0 01-.293.707l-6.414 6.414a1 1 0 00-.293.707V17l-4 4v-6.586a1 1 0 00-.293-.707L3.293 7.293A1 1 0 013 6.586V4z" />
    </svg>
  )
}

function ViewOptionsIcon({ className }: { className?: string }) {
  return (
    <svg className={className} fill="none" viewBox="0 0 24 24" stroke="currentColor">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6V4m0 2a2 2 0 100 4m0-4a2 2 0 110 4m-6 8a2 2 0 100-4m0 4a2 2 0 110-4m0 4v2m0-6V4m6 6v10m6-2a2 2 0 100-4m0 4a2 2 0 110-4m0 4v2m0-6V4" />
    </svg>
  )
}
