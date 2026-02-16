'use client'

import Link from 'next/link'
import { usePathname } from 'next/navigation'

const navigation = [
  { name: 'General', href: '/dashboard/settings/general' },
  { name: 'Team', href: '/dashboard/settings/team' },
  { name: 'Billing', href: '/dashboard/settings/billing' },
]

export function SettingsNav() {
  const pathname = usePathname()

  return (
    <nav className="w-48 flex-shrink-0">
      <h3 className="text-xs font-semibold text-muted uppercase tracking-wider mb-3">Settings</h3>
      <ul className="space-y-1">
        {navigation.map((item) => {
          const isActive = pathname === item.href
          return (
            <li key={item.name}>
              <Link
                href={item.href}
                className={`block px-3 py-2 text-sm rounded-lg transition-colors ${
                  isActive
                    ? 'bg-primary/10 text-primary font-medium'
                    : 'text-muted hover:text-foreground hover:bg-surface-hover'
                }`}
              >
                {item.name}
              </Link>
            </li>
          )
        })}
      </ul>
    </nav>
  )
}
