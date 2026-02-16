'use client'

import Link from 'next/link'
import { usePathname } from 'next/navigation'
import {
  BarChart3,
  LayoutDashboard,
  Globe,
  Code,
  Settings,
  Users,
  CreditCard,
  HelpCircle,
} from 'lucide-react'
import { cn } from '@/lib/utils'

const navigation = [
  { name: 'Dashboard', href: '/dashboard', icon: LayoutDashboard },
  { name: 'Public Stats', href: '/dashboard/public', icon: Globe },
  { name: 'Tracking Code', href: '/settings/snippet', icon: Code },
]

const settingsNav = [
  { name: 'General', href: '/settings', icon: Settings },
  { name: 'Team', href: '/settings/team', icon: Users },
  { name: 'Billing', href: '/settings/billing', icon: CreditCard },
]

export function Sidebar() {
  const pathname = usePathname()

  return (
    <aside className="hidden lg:fixed lg:inset-y-0 lg:flex lg:w-64 lg:flex-col">
      <div className="flex flex-col flex-1 min-h-0 bg-background border-r border-border">
        {/* Logo */}
        <div className="flex items-center h-16 px-6 border-b border-border">
          <Link href="/" className="flex items-center gap-2">
            <BarChart3 className="h-8 w-8 text-primary" />
            <span className="font-display font-bold text-xl">Analytics</span>
          </Link>
        </div>

        {/* Navigation */}
        <nav className="flex-1 px-4 py-4 space-y-1 overflow-y-auto">
          <div className="space-y-1">
            {navigation.map((item) => (
              <Link
                key={item.name}
                href={item.href}
                className={cn(
                  'flex items-center gap-3 px-3 py-2 text-sm font-medium rounded-lg transition-colors',
                  pathname === item.href
                    ? 'bg-primary/10 text-primary'
                    : 'text-foreground/70 hover:bg-surface hover:text-foreground'
                )}
              >
                <item.icon className="h-5 w-5" />
                {item.name}
              </Link>
            ))}
          </div>

          <div className="pt-6">
            <p className="px-3 text-xs font-semibold text-foreground/50 uppercase tracking-wider">
              Settings
            </p>
            <div className="mt-2 space-y-1">
              {settingsNav.map((item) => (
                <Link
                  key={item.name}
                  href={item.href}
                  className={cn(
                    'flex items-center gap-3 px-3 py-2 text-sm font-medium rounded-lg transition-colors',
                    pathname === item.href
                      ? 'bg-primary/10 text-primary'
                      : 'text-foreground/70 hover:bg-surface hover:text-foreground'
                  )}
                >
                  <item.icon className="h-5 w-5" />
                  {item.name}
                </Link>
              ))}
            </div>
          </div>
        </nav>

        {/* Footer */}
        <div className="p-4 border-t border-border">
          <Link
            href="/help"
            className="flex items-center gap-3 px-3 py-2 text-sm font-medium text-foreground/70 hover:bg-surface rounded-lg transition-colors"
          >
            <HelpCircle className="h-5 w-5" />
            Help & Support
          </Link>
        </div>
      </div>
    </aside>
  )
}
