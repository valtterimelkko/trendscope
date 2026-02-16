'use client'

import Link from 'next/link'
import { usePathname } from 'next/navigation'
import { User } from '@supabase/supabase-js'

interface SidebarProps {
  user: User
  profile: any
  subscription: any
  limits: {
    downloads: { used: number; max: number }
    storage: { used: number; max: number }
  }
}

export function Sidebar({ user, profile, subscription, limits }: SidebarProps) {
  const pathname = usePathname()

  const navigation = [
    {
      name: 'Downloads',
      href: '/dashboard',
      icon: DownloadIcon,
    },
  ]

  const bottomNav = [
    {
      name: 'Settings',
      href: '/dashboard/settings',
      icon: SettingsIcon,
    },
  ]

  const downloadUsagePercent = (limits.downloads.used / limits.downloads.max) * 100
  const isNearLimit = downloadUsagePercent >= 80
  const isAtLimit = downloadUsagePercent >= 100

  return (
    <aside className="w-64 bg-surface border-r border-border flex flex-col">
      {/* Account info */}
      <div className="p-4 border-b border-border">
        <div className="px-3 py-2">
          <p className="text-sm font-medium text-foreground">Digital Downloads</p>
          <p className="text-xs text-muted">{subscription?.tier || 'Starter'} plan</p>
        </div>
      </div>

      {/* Main navigation */}
      <nav className="flex-1 px-3 py-4 space-y-1">
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
            <span className="text-muted">Downloads used</span>
            <span className={`font-medium ${isAtLimit ? 'text-red-500' : isNearLimit ? 'text-yellow-600' : 'text-foreground'}`}>
              {limits.downloads.used} / {limits.downloads.max}
            </span>
          </div>
          <div className="h-1.5 bg-surface-hover rounded-full overflow-hidden">
            <div
              className={`h-full rounded-full transition-all ${
                isAtLimit ? 'bg-red-500' : isNearLimit ? 'bg-yellow-500' : 'bg-primary'
              }`}
              style={{ width: `${Math.min(downloadUsagePercent, 100)}%` }}
            />
          </div>
          {isNearLimit && (
            <Link
              href="/settings/billing"
              className="block text-xs text-primary hover:underline"
            >
              {isAtLimit ? 'Upgrade for more downloads' : 'Running low? Upgrade now'}
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
function DownloadIcon({ className }: { className?: string }) {
  return (
    <svg className={className} fill="none" viewBox="0 0 24 24" stroke="currentColor">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M9 19l3 3m0 0l3-3m-3 3V10" />
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
