'use client'

import Link from 'next/link'
import { usePathname } from 'next/navigation'
import { User } from '@supabase/supabase-js'

interface SidebarProps {
  user: User
  profile: any
  workspaces: any[]
  currentWorkspace: any
  limits: {
    posts: { used: number; max: number }
    storage: { used: number; max: number }
    scheduledPosts: { used: number; max: number }
  }
}

export function Sidebar({ user, profile, workspaces, currentWorkspace, limits }: SidebarProps) {
  const pathname = usePathname()

  const navigation = [
    {
      name: 'Content',
      href: '/dashboard',
      icon: DocumentIcon,
    },
    {
      name: 'Queue',
      href: '/dashboard/queue',
      icon: QueueIcon,
    },
    {
      name: 'Calendar',
      href: '/dashboard/calendar',
      icon: CalendarIcon,
    },
    {
      name: 'Analytics',
      href: '/dashboard/analytics',
      icon: ChartIcon,
    },
    {
      name: 'Media',
      href: '/dashboard/media',
      icon: ImageIcon,
    },
    {
      name: 'Connect',
      href: '/dashboard/connect',
      icon: LinkIcon,
    },
  ]

  const bottomNav = [
    {
      name: 'Settings',
      href: '/dashboard/settings',
      icon: SettingsIcon,
    },
  ]

  const postUsagePercent = (limits.posts.used / limits.posts.max) * 100
  const isNearLimit = postUsagePercent >= 80
  const isAtLimit = postUsagePercent >= 100

  return (
    <aside className="w-64 bg-surface border-r border-border flex flex-col">
      {/* Workspace selector */}
      <div className="p-4 border-b border-border">
        <button className="w-full flex items-center gap-3 px-3 py-2 rounded-lg hover:bg-surface-hover transition-colors">
          <div className="w-8 h-8 bg-primary rounded-lg flex items-center justify-center">
            <span className="text-sm font-semibold text-white">
              {currentWorkspace?.name?.charAt(0) || 'W'}
            </span>
          </div>
          <div className="flex-1 text-left">
            <p className="text-sm font-medium text-foreground truncate">
              {currentWorkspace?.name || 'Workspace'}
            </p>
            <p className="text-xs text-muted">Starter plan</p>
          </div>
          <ChevronIcon className="w-4 h-4 text-muted" />
        </button>
      </div>

      {/* Create button */}
      <div className="p-4">
        <Link
          href="/dashboard/content/new"
          className="w-full flex items-center justify-center gap-2 px-4 py-2.5 bg-primary text-white font-medium rounded-lg hover:bg-primary-hover transition-colors"
        >
          <PlusIcon className="w-4 h-4" />
          New Post
        </Link>
      </div>

      {/* Main navigation */}
      <nav className="flex-1 px-3 space-y-1">
        {navigation.map((item) => {
          const isActive = pathname === item.href || (item.href !== '/dashboard' && pathname.startsWith(item.href))
          return (
            <Link
              key={item.name}
              href={item.href}
              className={`flex items-center gap-3 px-3 py-2 rounded-lg text-sm transition-colors ${
                isActive
                  ? 'bg-primary/10 text-primary font-medium'
                  : 'text-muted hover:text-foreground hover:bg-surface-hover'
              }`}
            >
              <item.icon className="w-5 h-5" />
              <span>{item.name}</span>
            </Link>
          )
        })}
      </nav>

      {/* Usage indicator */}
      <div className="px-4 py-3 border-t border-border">
        <div className="space-y-2">
          <div className="flex items-center justify-between text-xs">
            <span className="text-muted">Posts used</span>
            <span className={`font-medium ${isAtLimit ? 'text-red-500' : isNearLimit ? 'text-yellow-600' : 'text-foreground'}`}>
              {limits.posts.used} / {limits.posts.max}
            </span>
          </div>
          <div className="h-1.5 bg-surface-hover rounded-full overflow-hidden">
            <div
              className={`h-full rounded-full transition-all ${
                isAtLimit ? 'bg-red-500' : isNearLimit ? 'bg-yellow-500' : 'bg-primary'
              }`}
              style={{ width: `${Math.min(postUsagePercent, 100)}%` }}
            />
          </div>
          {isNearLimit && (
            <Link
              href="/dashboard/settings/billing"
              className="block text-xs text-primary hover:underline"
            >
              {isAtLimit ? 'Upgrade to create more posts' : 'Running low? Upgrade now'}
            </Link>
          )}
        </div>
      </div>

      {/* Bottom navigation */}
      <div className="px-3 py-2 border-t border-border space-y-1">
        {bottomNav.map((item) => {
          const isActive = pathname.startsWith(item.href)
          return (
            <Link
              key={item.name}
              href={item.href}
              className={`flex items-center gap-3 px-3 py-2 rounded-lg text-sm transition-colors ${
                isActive
                  ? 'bg-primary/10 text-primary font-medium'
                  : 'text-muted hover:text-foreground hover:bg-surface-hover'
              }`}
            >
              <item.icon className="w-5 h-5" />
              <span>{item.name}</span>
            </Link>
          )
        })}
      </div>

      {/* User */}
      <div className="p-4 border-t border-border">
        <div className="flex items-center gap-3">
          <div className="w-9 h-9 bg-secondary rounded-full flex items-center justify-center">
            <span className="text-sm font-medium text-foreground">
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
function DocumentIcon({ className }: { className?: string }) {
  return (
    <svg className={className} fill="none" viewBox="0 0 24 24" stroke="currentColor">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
    </svg>
  )
}

function ImageIcon({ className }: { className?: string }) {
  return (
    <svg className={className} fill="none" viewBox="0 0 24 24" stroke="currentColor">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z" />
    </svg>
  )
}

function CalendarIcon({ className }: { className?: string }) {
  return (
    <svg className={className} fill="none" viewBox="0 0 24 24" stroke="currentColor">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
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

function PlusIcon({ className }: { className?: string }) {
  return (
    <svg className={className} fill="none" viewBox="0 0 24 24" stroke="currentColor">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
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

function QueueIcon({ className }: { className?: string }) {
  return (
    <svg className={className} fill="none" viewBox="0 0 24 24" stroke="currentColor">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 10h16M4 14h16M4 18h16" />
    </svg>
  )
}

function LinkIcon({ className }: { className?: string }) {
  return (
    <svg className={className} fill="none" viewBox="0 0 24 24" stroke="currentColor">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13.828 10.172a4 4 0 00-5.656 0l-4 4a4 4 0 105.656 5.656l1.102-1.101m-.758-4.899a4 4 0 005.656 0l4-4a4 4 0 00-5.656-5.656l-1.1 1.1" />
    </svg>
  )
}

function ChartIcon({ className }: { className?: string }) {
  return (
    <svg className={className} fill="none" viewBox="0 0 24 24" stroke="currentColor">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
    </svg>
  )
}
