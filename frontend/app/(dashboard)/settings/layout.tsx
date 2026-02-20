'use client';

import { Button } from '@/components/ui/button';
import { usePathname } from 'next/navigation';
import Link from 'next/link';
import { User, Bell, Zap, CreditCard, Trash2 } from 'lucide-react';

const settingsNav = [
  { name: 'Profile', href: '/app/settings', icon: User },
  { name: 'Notifications', href: '/app/settings/notifications', icon: Bell },
  { name: 'Integrations', href: '/app/settings/integrations', icon: Zap },
  { name: 'Billing', href: '/app/settings/billing', icon: CreditCard },
  { name: 'Danger Zone', href: '/app/settings/danger', icon: Trash2 },
];

export default function SettingsLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const pathname = usePathname();

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-heading-2 mb-2">Settings</h1>
        <p className="text-body text-muted-foreground">
          Manage your account and preferences
        </p>
      </div>

      <div className="grid gap-6 lg:grid-cols-4">
        {/* Sidebar Navigation */}
        <div className="lg:col-span-1">
          <nav className="space-y-2 border rounded-lg p-4 bg-white h-fit sticky top-20">
            {settingsNav.map((item) => {
              const isActive = pathname === item.href || (pathname === '/app/settings' && item.href === '/app/settings');
              const Icon = item.icon;
              
              return (
                <Link key={item.href} href={item.href}>
                  <Button
                    variant={isActive ? 'default' : 'ghost'}
                    className="w-full justify-start"
                  >
                    <Icon className="h-4 w-4 mr-2" />
                    {item.name}
                  </Button>
                </Link>
              );
            })}
          </nav>
        </div>

        {/* Main Content */}
        <div className="lg:col-span-3">
          {children}
        </div>
      </div>
    </div>
  );
}
