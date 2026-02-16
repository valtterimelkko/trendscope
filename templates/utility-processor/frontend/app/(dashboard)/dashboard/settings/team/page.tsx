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

  // Fetch subscription for seat info
  const { data: subscription } = await supabase
    .from('subscriptions')
    .select('*')
    .eq('workspace_id', currentWorkspace?.id)
    .eq('status', 'active')
    .single()

  const seatLimit = subscription?.seat_count || 5
  const usedSeats = members.length

  return (
    <div className="h-full flex">
      <SettingsNav />

      <div className="flex-1 overflow-auto">
        <div className="max-w-2xl mx-auto p-8">
          <div className="flex items-center justify-between mb-6">
            <h2 className="text-xl font-semibold text-foreground">Team Members</h2>
            <button
              className="flex items-center gap-1.5 px-3 py-1.5 bg-primary hover:bg-primary-hover text-white text-sm font-medium rounded-md transition-colors disabled:opacity-50"
              disabled={usedSeats >= seatLimit}
            >
              <PlusIcon className="w-4 h-4" />
              Invite member
            </button>
          </div>

          {/* Seat usage */}
          <div className="bg-surface border border-border rounded-lg p-4 mb-6">
            <div className="flex items-center justify-between mb-2">
              <span className="text-sm text-muted">Seat usage</span>
              <span className="text-sm font-medium text-foreground">
                {usedSeats} / {seatLimit} seats
              </span>
            </div>
            <div className="h-2 bg-background rounded-full overflow-hidden">
              <div
                className={`h-full rounded-full transition-all ${
                  usedSeats >= seatLimit ? 'bg-red-500' : 'bg-primary'
                }`}
                style={{ width: `${Math.min((usedSeats / seatLimit) * 100, 100)}%` }}
              />
            </div>
            {usedSeats >= seatLimit && (
              <p className="text-xs text-red-400 mt-2">
                You've reached your seat limit.{' '}
                <a href="/dashboard/settings/billing" className="text-primary hover:underline">
                  Upgrade your plan
                </a>{' '}
                to add more members.
              </p>
            )}
          </div>

          {/* Members list */}
          <div className="bg-surface border border-border rounded-lg overflow-hidden">
            <table className="w-full">
              <thead>
                <tr className="border-b border-border bg-background">
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
                        <div className="w-8 h-8 bg-primary/20 rounded-full flex items-center justify-center">
                          <span className="text-sm font-medium text-primary">
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
                          ? 'bg-yellow-500/10 text-yellow-500'
                          : 'bg-surface-hover text-muted'
                      }`}>
                        {member.role}
                      </span>
                    </td>
                    <td className="px-4 py-3 text-sm text-muted">
                      {new Date(member.created_at).toLocaleDateString()}
                    </td>
                    <td className="px-4 py-3">
                      {member.role !== 'owner' && member.user_id !== user?.id && (
                        <button className="text-xs text-muted hover:text-red-400 transition-colors">
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
            <div className="bg-surface border border-border rounded-lg p-8 text-center">
              <p className="text-sm text-muted">No pending invitations</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

function PlusIcon({ className }: { className?: string }) {
  return (
    <svg className={className} fill="none" viewBox="0 0 24 24" stroke="currentColor">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
    </svg>
  )
}
