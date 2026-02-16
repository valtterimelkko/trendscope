'use client'

import { User } from '@supabase/supabase-js'
import { usePathname } from 'next/navigation'
import Link from 'next/link'

interface HeaderProps {
  user: User
  profile: any
}

export function Header({ user, profile }: HeaderProps) {
  const pathname = usePathname()

  // Determine page title and breadcrumb
  const getBreadcrumb = () => {
    if (pathname === '/dashboard') return [{ name: 'Content', href: '/dashboard' }]
    if (pathname === '/dashboard/media') return [{ name: 'Media', href: '/dashboard/media' }]
    if (pathname === '/dashboard/calendar') return [{ name: 'Calendar', href: '/dashboard/calendar' }]
    if (pathname.startsWith('/dashboard/settings')) return [{ name: 'Settings', href: '/dashboard/settings' }]
    if (pathname.startsWith('/dashboard/content/')) return [
      { name: 'Content', href: '/dashboard' },
      { name: 'Editor', href: pathname }
    ]
    return [{ name: 'Dashboard', href: '/dashboard' }]
  }

  const breadcrumb = getBreadcrumb()

  return (
    <header className="h-14 border-b border-border bg-surface flex items-center px-6 gap-4">
      {/* Breadcrumb */}
      <nav className="flex items-center gap-2 text-sm">
        {breadcrumb.map((item, index) => (
          <div key={item.href} className="flex items-center gap-2">
            {index > 0 && <span className="text-muted">/</span>}
            {index === breadcrumb.length - 1 ? (
              <span className="font-medium text-foreground">{item.name}</span>
            ) : (
              <Link href={item.href} className="text-muted hover:text-foreground transition-colors">
                {item.name}
              </Link>
            )}
          </div>
        ))}
      </nav>

      {/* Spacer */}
      <div className="flex-1" />

      {/* Search */}
      <button className="flex items-center gap-2 px-3 py-1.5 bg-background border border-border rounded-lg text-sm text-muted hover:border-border-hover transition-colors">
        <SearchIcon className="w-4 h-4" />
        <span>Search posts...</span>
        <kbd className="px-1.5 py-0.5 bg-surface-hover rounded text-xs">⌘K</kbd>
      </button>

      {/* Notifications */}
      <button className="p-2 text-muted hover:text-foreground hover:bg-surface-hover rounded-lg transition-colors relative">
        <BellIcon className="w-5 h-5" />
        <span className="absolute top-1.5 right-1.5 w-2 h-2 bg-primary rounded-full"></span>
      </button>

      {/* Help */}
      <button className="p-2 text-muted hover:text-foreground hover:bg-surface-hover rounded-lg transition-colors">
        <HelpIcon className="w-5 h-5" />
      </button>
    </header>
  )
}

function SearchIcon({ className }: { className?: string }) {
  return (
    <svg className={className} fill="none" viewBox="0 0 24 24" stroke="currentColor">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
    </svg>
  )
}

function BellIcon({ className }: { className?: string }) {
  return (
    <svg className={className} fill="none" viewBox="0 0 24 24" stroke="currentColor">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6.002 6.002 0 00-4-5.659V5a2 2 0 10-4 0v.341C7.67 6.165 6 8.388 6 11v3.159c0 .538-.214 1.055-.595 1.436L4 17h5m6 0v1a3 3 0 11-6 0v-1m6 0H9" />
    </svg>
  )
}

function HelpIcon({ className }: { className?: string }) {
  return (
    <svg className={className} fill="none" viewBox="0 0 24 24" stroke="currentColor">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8.228 9c.549-1.165 2.03-2 3.772-2 2.21 0 4 1.343 4 3 0 1.4-1.278 2.575-3.006 2.907-.542.104-.994.54-.994 1.093m0 3h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
    </svg>
  )
}
