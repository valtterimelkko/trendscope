import { createClient } from '@/lib/supabase/server'
import { SettingsNav } from '../_components/SettingsNav'

export default async function GeneralSettingsPage() {
  const supabase = await createClient()
  const { data: { user } } = await supabase.auth.getUser()

  // Fetch user profile
  const { data: profile } = await supabase
    .from('profiles')
    .select('*')
    .eq('id', user?.id)
    .single()

  // Fetch current workspace
  const { data: workspaces } = await supabase
    .from('workspaces')
    .select('*, workspace_members!inner(*)')
    .eq('workspace_members.user_id', user?.id)
    .limit(1)

  const currentWorkspace = workspaces?.[0]

  return (
    <div className="p-6 flex gap-8">
      <SettingsNav />

      <div className="flex-1 max-w-2xl">
        <h2 className="text-xl font-semibold text-foreground mb-6">General Settings</h2>

        {/* Profile section */}
        <section className="mb-8">
          <h3 className="text-sm font-medium text-foreground mb-4">Your Profile</h3>
          <div className="bg-surface border border-border rounded-xl p-6 space-y-4">
            <div className="flex items-center gap-4">
              <div className="w-16 h-16 bg-secondary rounded-full flex items-center justify-center">
                <span className="text-2xl font-semibold text-foreground">
                  {profile?.display_name?.charAt(0) || user?.email?.charAt(0) || 'U'}
                </span>
              </div>
              <div>
                <button className="text-sm text-primary hover:underline">
                  Upload photo
                </button>
                <p className="text-xs text-muted mt-0.5">JPG or PNG, max 2MB</p>
              </div>
            </div>

            <div>
              <label className="block text-sm font-medium text-foreground mb-1.5">
                Display name
              </label>
              <input
                type="text"
                defaultValue={profile?.display_name || ''}
                className="input"
                placeholder="Your name"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-foreground mb-1.5">
                Email
              </label>
              <input
                type="email"
                value={user?.email || ''}
                disabled
                className="input bg-surface-hover text-muted"
              />
              <p className="text-xs text-muted mt-1">Contact support to change your email</p>
            </div>

            <div>
              <label className="block text-sm font-medium text-foreground mb-1.5">
                Bio
              </label>
              <textarea
                defaultValue={profile?.bio || ''}
                className="input min-h-[100px] resize-none"
                placeholder="A short bio about yourself..."
              />
            </div>
          </div>
        </section>

        {/* Workspace section */}
        <section className="mb-8">
          <h3 className="text-sm font-medium text-foreground mb-4">Workspace</h3>
          <div className="bg-surface border border-border rounded-xl p-6 space-y-4">
            <div>
              <label className="block text-sm font-medium text-foreground mb-1.5">
                Workspace name
              </label>
              <input
                type="text"
                defaultValue={currentWorkspace?.name || ''}
                className="input"
                placeholder="My Workspace"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-foreground mb-1.5">
                Workspace URL
              </label>
              <div className="flex">
                <span className="inline-flex items-center px-3 bg-surface-hover border border-r-0 border-border rounded-l-lg text-sm text-muted">
                  app.example.com/
                </span>
                <input
                  type="text"
                  defaultValue={currentWorkspace?.slug || ''}
                  className="input rounded-l-none"
                  placeholder="my-workspace"
                />
              </div>
            </div>
          </div>
        </section>

        {/* Preferences section */}
        <section className="mb-8">
          <h3 className="text-sm font-medium text-foreground mb-4">Preferences</h3>
          <div className="bg-surface border border-border rounded-xl divide-y divide-border">
            <div className="p-4 flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-foreground">Email notifications</p>
                <p className="text-xs text-muted">Receive updates about your content</p>
              </div>
              <button className="relative inline-flex h-6 w-11 items-center rounded-full bg-primary transition-colors">
                <span className="inline-block h-4 w-4 transform rounded-full bg-white transition translate-x-6" />
              </button>
            </div>
            <div className="p-4 flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-foreground">Weekly digest</p>
                <p className="text-xs text-muted">Summary of your content performance</p>
              </div>
              <button className="relative inline-flex h-6 w-11 items-center rounded-full bg-primary transition-colors">
                <span className="inline-block h-4 w-4 transform rounded-full bg-white transition translate-x-6" />
              </button>
            </div>
          </div>
        </section>

        {/* Save button */}
        <div className="flex justify-end">
          <button className="px-6 py-2 bg-primary text-white font-medium rounded-lg hover:bg-primary-hover transition-colors">
            Save changes
          </button>
        </div>
      </div>
    </div>
  )
}
