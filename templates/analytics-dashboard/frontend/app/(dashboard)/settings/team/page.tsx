import { createClient } from '@/lib/supabase/server'
import { Users, Copy, Mail } from 'lucide-react'

export default async function TeamSettingsPage() {
  const supabase = createClient()
  const { data: { user } } = await supabase.auth.getUser()

  // In a real app, fetch team members from the database
  const teamMembers = [
    { id: user?.id, email: user?.email, role: 'Owner', status: 'Active' },
  ]

  return (
    <div className="max-w-4xl">
      <div className="mb-8">
        <h1 className="text-2xl font-display font-bold">Team Settings</h1>
        <p className="text-foreground/70 mt-1">
          Manage your team members and their permissions.
        </p>
      </div>

      {/* Invite Section */}
      <div className="card p-6 mb-6">
        <h2 className="font-semibold mb-4">Invite Team Members</h2>
        <div className="flex gap-4">
          <div className="flex-1">
            <div className="relative">
              <Mail className="absolute left-3 top-1/2 -translate-y-1/2 h-5 w-5 text-foreground/40" />
              <input
                type="email"
                placeholder="colleague@company.com"
                className="input pl-10"
              />
            </div>
          </div>
          <button className="btn-primary">Send Invite</button>
        </div>
        <p className="text-xs text-foreground/50 mt-2">
          Invited members will receive an email with a link to join your workspace.
        </p>
      </div>

      {/* Invite Link */}
      <div className="card p-6 mb-6">
        <h2 className="font-semibold mb-4">Invite Link</h2>
        <p className="text-sm text-foreground/70 mb-4">
          Share this link with anyone you want to invite to your workspace.
        </p>
        <div className="flex gap-2">
          <input
            type="text"
            value="https://app.example.com/invite/abc123xyz"
            readOnly
            className="input flex-1 bg-surface"
          />
          <button className="btn-secondary flex items-center gap-2">
            <Copy className="h-4 w-4" />
            Copy
          </button>
        </div>
      </div>

      {/* Team Members List */}
      <div className="card">
        <div className="p-6 border-b border-border">
          <h2 className="font-semibold">Team Members</h2>
        </div>
        <div className="divide-y divide-border">
          {teamMembers.map((member) => (
            <div key={member.id} className="p-4 flex items-center justify-between">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 rounded-full bg-primary/10 text-primary flex items-center justify-center">
                  <Users className="h-5 w-5" />
                </div>
                <div>
                  <p className="font-medium">{member.email}</p>
                  <p className="text-xs text-foreground/50">{member.role}</p>
                </div>
              </div>
              <span className="badge badge-success">{member.status}</span>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}
