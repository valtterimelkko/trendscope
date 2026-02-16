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
    <div className="h-full flex">
      <SettingsNav />

      <div className="flex-1 overflow-auto">
        <div className="max-w-2xl mx-auto p-8">
          <h2 className="text-xl font-semibold text-foreground mb-6">General Settings</h2>

          {/* Profile section */}
          <section className="mb-8">
            <h3 className="text-sm font-medium text-foreground mb-4">Profile</h3>
            <div className="bg-surface border border-border rounded-lg p-4 space-y-4">
              <div>
                <label className="block text-sm text-muted mb-1">Display name</label>
                <input
                  type="text"
                  defaultValue={profile?.display_name || ''}
                  className="w-full px-3 py-2 bg-background border border-border rounded-lg text-foreground placeholder:text-muted focus:outline-none focus:ring-2 focus:ring-primary/50 focus:border-primary transition-colors"
                  placeholder="Your name"
                />
              </div>
              <div>
                <label className="block text-sm text-muted mb-1">Email</label>
                <input
                  type="email"
                  value={user?.email || ''}
                  disabled
                  className="w-full px-3 py-2 bg-background border border-border rounded-lg text-muted"
                />
                <p className="text-xs text-muted mt-1">Email cannot be changed</p>
              </div>
            </div>
          </section>

          {/* Workspace section */}
          <section className="mb-8">
            <h3 className="text-sm font-medium text-foreground mb-4">Workspace</h3>
            <div className="bg-surface border border-border rounded-lg p-4 space-y-4">
              <div>
                <label className="block text-sm text-muted mb-1">Workspace name</label>
                <input
                  type="text"
                  defaultValue={currentWorkspace?.name || ''}
                  className="w-full px-3 py-2 bg-background border border-border rounded-lg text-foreground placeholder:text-muted focus:outline-none focus:ring-2 focus:ring-primary/50 focus:border-primary transition-colors"
                  placeholder="My Workspace"
                />
              </div>
              <div>
                <label className="block text-sm text-muted mb-1">Workspace slug</label>
                <div className="flex items-center gap-2">
                  <span className="text-sm text-muted">app.example.com/</span>
                  <input
                    type="text"
                    defaultValue={currentWorkspace?.slug || ''}
                    className="flex-1 px-3 py-2 bg-background border border-border rounded-lg text-foreground placeholder:text-muted focus:outline-none focus:ring-2 focus:ring-primary/50 focus:border-primary transition-colors"
                    placeholder="my-workspace"
                  />
                </div>
              </div>
            </div>
          </section>

          {/* Preferences section */}
          <section className="mb-8">
            <h3 className="text-sm font-medium text-foreground mb-4">Preferences</h3>
            <div className="bg-surface border border-border rounded-lg divide-y divide-border">
              <div className="p-4 flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-foreground">Dark mode</p>
                  <p className="text-xs text-muted">Always use dark theme</p>
                </div>
                <button className="relative inline-flex h-6 w-11 items-center rounded-full bg-primary">
                  <span className="inline-block h-4 w-4 transform rounded-full bg-white transition translate-x-6" />
                </button>
              </div>
              <div className="p-4 flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-foreground">Keyboard shortcuts</p>
                  <p className="text-xs text-muted">Enable keyboard navigation</p>
                </div>
                <button className="relative inline-flex h-6 w-11 items-center rounded-full bg-primary">
                  <span className="inline-block h-4 w-4 transform rounded-full bg-white transition translate-x-6" />
                </button>
              </div>
              <div className="p-4 flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-foreground">Sound effects</p>
                  <p className="text-xs text-muted">Play sounds for actions</p>
                </div>
                <button className="relative inline-flex h-6 w-11 items-center rounded-full bg-surface-hover">
                  <span className="inline-block h-4 w-4 transform rounded-full bg-muted transition translate-x-1" />
                </button>
              </div>
            </div>
          </section>

          {/* Save button */}
          <div className="flex justify-end">
            <button className="px-4 py-2 bg-primary hover:bg-primary-hover text-white text-sm font-medium rounded-lg transition-colors">
              Save changes
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}
