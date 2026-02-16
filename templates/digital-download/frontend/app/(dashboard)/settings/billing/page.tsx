import { createClient } from '@/lib/supabase/server'
import { SettingsNav } from '../_components/SettingsNav'
import { createBillingPortalSession } from '@/lib/stripe/actions'
import { formatFileSize } from '@/lib/utils'

export default async function BillingSettingsPage() {
  const supabase = await createClient()
  const { data: { user } } = await supabase.auth.getUser()

  // Fetch current workspace
  const { data: workspaces } = await supabase
    .from('workspaces')
    .select('*, workspace_members!inner(*)')
    .eq('workspace_members.user_id', user?.id)
    .limit(1)

  const currentWorkspace = workspaces?.[0]

  // Fetch subscription
  const { data: subscription } = await supabase
    .from('subscriptions')
    .select('*')
    .eq('workspace_id', currentWorkspace?.id)
    .eq('status', 'active')
    .single()

  // Calculate usage
  const { count: postCount } = await supabase
    .from('posts')
    .select('*', { count: 'exact', head: true })
    .eq('workspace_id', currentWorkspace?.id)

  const { count: memberCount } = await supabase
    .from('workspace_members')
    .select('*', { count: 'exact', head: true })
    .eq('workspace_id', currentWorkspace?.id)

  const plans = [
    {
      name: 'Starter',
      price: '$0',
      period: 'forever',
      features: ['10 posts', '500MB storage', '5 scheduled posts', '1 team member'],
      limits: { posts: 10, storage: 500, scheduled: 5, members: 1 },
      current: !subscription,
    },
    {
      name: 'Creator',
      price: '$15',
      period: 'per month',
      features: ['100 posts', '10GB storage', '50 scheduled posts', '3 team members', 'Priority support'],
      limits: { posts: 100, storage: 10240, scheduled: 50, members: 3 },
      current: subscription?.price_id?.includes('creator'),
      recommended: true,
    },
    {
      name: 'Studio',
      price: '$39',
      period: 'per month',
      features: ['Unlimited posts', '100GB storage', 'Unlimited scheduling', '10 team members', 'Custom domain', 'API access'],
      limits: { posts: -1, storage: 102400, scheduled: -1, members: 10 },
      current: subscription?.price_id?.includes('studio'),
    },
  ]

  const currentPlan = plans.find(p => p.current) || plans[0]

  return (
    <div className="p-6 flex gap-8">
      <SettingsNav />

      <div className="flex-1 max-w-3xl">
        <h2 className="text-xl font-semibold text-foreground mb-6">Billing</h2>

        {/* Current plan */}
        <div className="bg-surface border border-border rounded-xl p-6 mb-8">
          <div className="flex items-center justify-between">
            <div>
              <h3 className="text-lg font-semibold text-foreground">{currentPlan.name} Plan</h3>
              <p className="text-sm text-muted mt-1">
                {subscription
                  ? `Next billing: ${new Date(subscription.current_period_end).toLocaleDateString()}`
                  : 'Free forever'}
              </p>
            </div>
            {subscription && (
              <form action={createBillingPortalSession}>
                <button
                  type="submit"
                  className="px-4 py-2 border border-border rounded-lg text-sm font-medium text-foreground hover:bg-surface-hover transition-colors"
                >
                  Manage subscription
                </button>
              </form>
            )}
          </div>
        </div>

        {/* Usage */}
        <h3 className="text-sm font-medium text-foreground mb-4">Current Usage</h3>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-8">
          <UsageCard
            label="Posts"
            used={postCount || 0}
            limit={currentPlan.limits.posts}
          />
          <UsageCard
            label="Team members"
            used={memberCount || 0}
            limit={currentPlan.limits.members}
          />
        </div>

        {/* Plans */}
        <h3 className="text-sm font-medium text-foreground mb-4">Available Plans</h3>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-8">
          {plans.map((plan) => (
            <div
              key={plan.name}
              className={`relative bg-surface border rounded-xl p-5 ${
                plan.current ? 'border-primary ring-2 ring-primary/20' : 'border-border'
              }`}
            >
              {plan.recommended && !plan.current && (
                <span className="absolute -top-3 left-1/2 -translate-x-1/2 px-3 py-1 bg-primary text-white text-xs font-medium rounded-full">
                  Popular
                </span>
              )}
              {plan.current && (
                <span className="absolute -top-3 right-4 px-3 py-1 bg-accent text-white text-xs font-medium rounded-full">
                  Current
                </span>
              )}

              <h4 className="text-lg font-semibold text-foreground">{plan.name}</h4>
              <div className="mt-2 mb-4">
                <span className="text-3xl font-bold text-foreground">{plan.price}</span>
                <span className="text-sm text-muted ml-1">/{plan.period}</span>
              </div>

              <ul className="space-y-2 mb-6">
                {plan.features.map((feature) => (
                  <li key={feature} className="flex items-center gap-2 text-sm text-muted">
                    <CheckIcon className="w-4 h-4 text-accent flex-shrink-0" />
                    {feature}
                  </li>
                ))}
              </ul>

              {plan.current ? (
                <button
                  disabled
                  className="w-full py-2 px-4 bg-surface-hover text-muted text-sm font-medium rounded-lg"
                >
                  Current plan
                </button>
              ) : (
                <button className="w-full py-2 px-4 bg-primary text-white text-sm font-medium rounded-lg hover:bg-primary-hover transition-colors">
                  {plan.price === '$0' ? 'Downgrade' : 'Upgrade'}
                </button>
              )}
            </div>
          ))}
        </div>

        {/* Billing history */}
        <h3 className="text-sm font-medium text-foreground mb-4">Billing History</h3>
        <div className="bg-surface border border-border rounded-xl p-8 text-center">
          <p className="text-sm text-muted">No invoices yet</p>
        </div>
      </div>
    </div>
  )
}

function UsageCard({ label, used, limit }: { label: string; used: number; limit: number }) {
  const isUnlimited = limit === -1
  const percent = isUnlimited ? 0 : (used / limit) * 100
  const isNearLimit = percent >= 80
  const isAtLimit = percent >= 100

  return (
    <div className="bg-surface border border-border rounded-xl p-4">
      <div className="flex items-center justify-between mb-2">
        <span className="text-sm text-muted">{label}</span>
        <span className={`text-sm font-medium ${isAtLimit ? 'text-red-500' : 'text-foreground'}`}>
          {used} / {isUnlimited ? '∞' : limit}
        </span>
      </div>
      {!isUnlimited && (
        <div className="h-2 bg-surface-hover rounded-full overflow-hidden">
          <div
            className={`h-full rounded-full transition-all ${
              isAtLimit ? 'bg-red-500' : isNearLimit ? 'bg-yellow-500' : 'bg-primary'
            }`}
            style={{ width: `${Math.min(percent, 100)}%` }}
          />
        </div>
      )}
    </div>
  )
}

function CheckIcon({ className }: { className?: string }) {
  return (
    <svg className={className} fill="none" viewBox="0 0 24 24" stroke="currentColor">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
    </svg>
  )
}
