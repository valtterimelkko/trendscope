import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';

export default function SettingsLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-heading-2 mb-2">Settings</h1>
        <p className="text-body text-muted-foreground">
          Manage your account settings and preferences
        </p>
      </div>

      <Tabs defaultValue="profile" className="space-y-6">
        <TabsList className="grid w-full max-w-md grid-cols-4">
          <TabsTrigger value="profile" asChild>
            <a href="/app/settings/profile">Profile</a>
          </TabsTrigger>
          <TabsTrigger value="niches" asChild>
            <a href="/app/settings/niches">Niches</a>
          </TabsTrigger>
          <TabsTrigger value="integrations" asChild>
            <a href="/app/settings/integrations">Integrations</a>
          </TabsTrigger>
          <TabsTrigger value="billing" asChild>
            <a href="/app/settings/billing">Billing</a>
          </TabsTrigger>
        </TabsList>
        {children}
      </Tabs>
    </div>
  );
}
