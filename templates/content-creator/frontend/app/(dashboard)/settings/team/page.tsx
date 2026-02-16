import { createClient } from '@/lib/supabase/server'
import { SettingsNav } from '../_components/SettingsNav'

export default async function TeamSettingsPage() {
  const supabase = await createClient()
  const { data: { user } } = await supabase.auth.getUser()

  // Fetch current workspace with members
  const { data: workspaces } = await supabase
    .from('workspaces')
    .select(`
      *,
      workspace_members(
        *,
        user:profiles(id, display_name, avatar_url, email)
      )
    `)
    .eq('workspace_members.user_id', user?.id)
    .limit(1)

  const currentWorkspace = workspaces?.[0]
  const members = currentWorkspace?.workspace_members || []

  // Fetch subscription for team member limits
  const { data: subscription } = await supabase
    .from('subscriptions')
    .select('*')
    .eq('workspace_id', currentWorkspace?.id)
    .eq('status', 'active')
    .single()

  const memberLimit = subscription?.member_limit || 1
  const isAtLimit = members.length >= memberLimit

  return (
    <div className="p-6 flex gap-8">
      <SettingsNav />

      <div className="flex-1 max-w-2xl">
        <div className="flex items-center justify-between mb-6">
          <h2 className="text-xl font-semibold text-foreground">Team Members</h2>
          <button
            className="px-4 py-2 bg-primary text-white font-medium rounded-lg hover:bg-primary-hover transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
            disabled={isAtLimit}
          >
            Invite member
          </button>
        </div>

        {/* Team limit */}
        <div className="bg-surface border border-border rounded-xl p-4 mb-6">
          <div className="flex items-center justify-between mb-2">
            <span className="text-sm text-muted">Team members</span>
            <span className={`text-sm font-medium ${isAtLimit ? 'text-red-500' : 'text-foreground'}`}>
              {members.length} / {memberLimit}
            </span>
          </div>
          <div className="h-2 bg-surface-hover rounded-full overflow-hidden">
            <div
              className={`h-full rounded-full transition-all ${isAtLimit ? 'bg-red-500' : 'bg-primary'}`}
              style={{ width: `${(members.length / memberLimit) * 100}%` }}
            />
          </div>
          {isAtLimit && (
            <p className="text-xs text-red-500 mt-2">
              You've reached your team member limit.{' '}
              <a href="/dashboard/settings/billing" className="text-primary hover:underline">
                Upgrade to add more
              </a>
            </p>
          )}
        </div>

        {/* Members list */}
        <div className="bg-surface border border-border rounded-xl overflow-hidden">
          <table className="w-full">
            <thead>
              <tr className="border-b border-border bg-surface-hover">
                <th className="text-left text-xs font-medium text-muted uppercase tracking-wider px-4 py-3">
                  Member
                </th>
                <th className="text-left text-xs font-medium text-muted uppercase tracking-wider px-4 py-3">
                  Role
                </th>
                <th className="text-left text-xs font-medium text-muted uppercase tracking-wider px-4 py-3">
                  Joined
                </th>
                <th className="w-20"></th>
              </tr>
            </thead>
            <tbody className="divide-y divide-border">
              {members.map((member: any) => (
                <tr key={member.id} className="hover:bg-surface-hover transition-colors">
                  <td className="px-4 py-3">
                    <div className="flex items-center gap-3">
                      <div className="w-9 h-9 bg-secondary rounded-full flex items-center justify-center">
                        <span className="text-sm font-medium text-foreground">
                          {member.user?.display_name?.charAt(0) || 'U'}
                        </span>
                      </div>
                      <div>
                        <p className="text-sm font-medium text-foreground">
                          {member.user?.display_name || 'Unknown'}
                        </p>
                        <p className="text-xs text-muted">{member.user?.email}</p>
                      </div>
                    </div>
                  </td>
                  <td className="px-4 py-3">
                    <span className={`inline-flex px-2 py-0.5 text-xs font-medium rounded ${
                      member.role === 'owner'
                        ? 'bg-primary/10 text-primary'
                        : member.role === 'admin'
                        ? 'bg-yellow-100 text-yellow-800'
                        : 'bg-gray-100 text-gray-700'
                    }`}>
                      {member.role}
                    </span>
                  </td>
                  <td className="px-4 py-3 text-sm text-muted">
                    {new Date(member.created_at).toLocaleDateString()}
                  </td>
                  <td className="px-4 py-3">
                    {member.role !== 'owner' && member.user_id !== user?.id && (
                      <button className="text-xs text-muted hover:text-red-500 transition-colors">
                        Remove
                      </button>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        {/* Pending invitations */}
        <div className="mt-8">
          <h3 className="text-sm font-medium text-foreground mb-4">Pending Invitations</h3>
          <div className="bg-surface border border-border rounded-xl p-8 text-center">
            <p className="text-sm text-muted">No pending invitations</p>
          </div>
        </div>
      </div>
    </div>
  )
}
