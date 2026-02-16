import { createClient } from '@/lib/supabase/server'
import { SettingsNav } from '../_components/SettingsNav'
import { createBillingPortalSession } from '@/lib/stripe/actions'

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

  // Fetch seat count
  const { count: memberCount } = await supabase
    .from('workspace_members')
    .select('*', { count: 'exact', head: true })
    .eq('workspace_id', currentWorkspace?.id)

  const plans = [
    {
      name: 'Free',
      price: '$0',
      period: 'forever',
      seats: 5,
      features: ['Up to 5 team members', '100 issues', 'Basic integrations'],
      current: !subscription || subscription.price_id === 'free',
    },
    {
      name: 'Pro',
      price: '$8',
      period: 'per seat/month',
      seats: 'unlimited',
      features: ['Unlimited team members', 'Unlimited issues', 'Priority support', 'Advanced analytics'],
      current: subscription?.price_id?.includes('pro'),
      recommended: true,
    },
    {
      name: 'Business',
      price: '$12',
      period: 'per seat/month',
      seats: 'unlimited',
      features: ['Everything in Pro', 'SSO/SAML', 'Audit logs', 'Custom workflows', 'Dedicated support'],
      current: subscription?.price_id?.includes('business'),
    },
  ]

  return (
    <div className="h-full flex">
      <SettingsNav />

      <div className="flex-1 overflow-auto">
        <div className="max-w-4xl mx-auto p-8">
          <h2 className="text-xl font-semibold text-foreground mb-6">Billing</h2>

          {/* Current plan */}
          <div className="bg-surface border border-border rounded-lg p-6 mb-8">
            <div className="flex items-center justify-between">
              <div>
                <h3 className="text-lg font-semibold text-foreground">
                  {subscription ? 'Pro Plan' : 'Free Plan'}
                </h3>
                <p className="text-sm text-muted mt-1">
                  {memberCount} seats in use
                  {subscription && ` • Next billing: ${new Date(subscription.current_period_end).toLocaleDateString()}`}
                </p>
              </div>
              {subscription && (
                <form action={createBillingPortalSession}>
                  <button
                    type="submit"
                    className="px-4 py-2 bg-surface-hover hover:bg-background border border-border text-foreground text-sm font-medium rounded-lg transition-colors"
                  >
                    Manage subscription
                  </button>
                </form>
              )}
            </div>
          </div>

          {/* Plans */}
          <h3 className="text-sm font-medium text-foreground mb-4">Available Plans</h3>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-8">
            {plans.map((plan) => (
              <div
                key={plan.name}
                className={`relative bg-surface border rounded-lg p-6 ${
                  plan.current ? 'border-primary' : 'border-border'
                } ${plan.recommended ? 'ring-2 ring-primary/20' : ''}`}
              >
                {plan.recommended && (
                  <span className="absolute -top-3 left-4 px-2 py-0.5 bg-primary text-white text-xs font-medium rounded">
                    Recommended
                  </span>
                )}
                {plan.current && (
                  <span className="absolute -top-3 right-4 px-2 py-0.5 bg-status-done text-white text-xs font-medium rounded">
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
                      <CheckIcon className="w-4 h-4 text-status-done flex-shrink-0" />
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
                  <button className="w-full py-2 px-4 bg-primary hover:bg-primary-hover text-white text-sm font-medium rounded-lg transition-colors">
                    {plan.price === '$0' ? 'Downgrade' : 'Upgrade'}
                  </button>
                )}
              </div>
            ))}
          </div>

          {/* Usage */}
          <h3 className="text-sm font-medium text-foreground mb-4">Usage This Month</h3>
          <div className="bg-surface border border-border rounded-lg p-6">
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
              <div>
                <p className="text-sm text-muted mb-1">Active seats</p>
                <p className="text-2xl font-semibold text-foreground">{memberCount}</p>
              </div>
              <div>
                <p className="text-sm text-muted mb-1">Issues created</p>
                <p className="text-2xl font-semibold text-foreground">-</p>
              </div>
              <div>
                <p className="text-sm text-muted mb-1">Storage used</p>
                <p className="text-2xl font-semibold text-foreground">-</p>
              </div>
            </div>
          </div>

          {/* Billing history */}
          <h3 className="text-sm font-medium text-foreground mt-8 mb-4">Billing History</h3>
          <div className="bg-surface border border-border rounded-lg p-8 text-center">
            <p className="text-sm text-muted">No invoices yet</p>
          </div>
        </div>
      </div>
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
