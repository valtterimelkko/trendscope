import { createClient } from '@/lib/supabase/server'
import { getSubscription, createPortalSession } from '@/lib/stripe/actions'
import { CreditCard, ExternalLink, AlertCircle } from 'lucide-react'
import { formatDate } from '@/lib/utils'

export default async function BillingPage() {
  const supabase = createClient()
  const { data: { user } } = await supabase.auth.getUser()
  const subscription = await getSubscription()

  // Demo usage data - replace with real data
  const usage = {
    current: 12847,
    limit: 50000,
    percentage: 26,
  }

  return (
    <div className="max-w-4xl">
      <div className="mb-8">
        <h1 className="text-2xl font-display font-bold">Billing</h1>
        <p className="text-foreground/70 mt-1">
          Manage your subscription and billing information.
        </p>
      </div>

      {/* Current Plan */}
      <div className="card p-6 mb-6">
        <div className="flex items-start justify-between">
          <div>
            <h2 className="font-semibold mb-1">Current Plan</h2>
            <div className="flex items-center gap-2">
              <span className="text-2xl font-bold">
                {subscription?.price_id ? 'Pro' : 'Free Trial'}
              </span>
              {subscription && (
                <span className="badge badge-success">Active</span>
              )}
            </div>
            {subscription?.current_period_end && (
              <p className="text-sm text-foreground/60 mt-2">
                {subscription.cancel_at_period_end
                  ? `Cancels on ${formatDate(subscription.current_period_end)}`
                  : `Renews on ${formatDate(subscription.current_period_end)}`}
              </p>
            )}
          </div>
          <form action={createPortalSession}>
            <button type="submit" className="btn-secondary flex items-center gap-2">
              Manage Subscription
              <ExternalLink className="h-4 w-4" />
            </button>
          </form>
        </div>
      </div>

      {/* Usage */}
      <div className="card p-6 mb-6">
        <h2 className="font-semibold mb-4">Usage This Month</h2>
        <div className="space-y-4">
          <div>
            <div className="flex justify-between text-sm mb-2">
              <span>Events tracked</span>
              <span className="font-medium">
                {usage.current.toLocaleString()} / {usage.limit.toLocaleString()}
              </span>
            </div>
            <div className="progress-bar">
              <div
                className="progress-fill"
                style={{ width: `${usage.percentage}%` }}
              />
            </div>
          </div>

          {usage.percentage > 80 && (
            <div className="flex items-center gap-2 p-3 bg-warning/10 text-warning rounded-lg text-sm">
              <AlertCircle className="h-4 w-4" />
              <span>You&apos;re approaching your monthly limit. Consider upgrading.</span>
            </div>
          )}
        </div>
      </div>

      {/* Payment Method */}
      <div className="card p-6 mb-6">
        <h2 className="font-semibold mb-4">Payment Method</h2>
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-lg bg-surface flex items-center justify-center">
              <CreditCard className="h-5 w-5 text-foreground/60" />
            </div>
            <div>
              <p className="font-medium">•••• •••• •••• 4242</p>
              <p className="text-xs text-foreground/50">Expires 12/2025</p>
            </div>
          </div>
          <form action={createPortalSession}>
            <button type="submit" className="btn-ghost text-sm">
              Update
            </button>
          </form>
        </div>
      </div>

      {/* Billing History */}
      <div className="card">
        <div className="p-6 border-b border-border">
          <h2 className="font-semibold">Billing History</h2>
        </div>
        <div className="divide-y divide-border">
          <div className="p-4 flex items-center justify-between text-sm">
            <div>
              <p className="font-medium">Invoice #001</p>
              <p className="text-foreground/50">Dec 1, 2024</p>
            </div>
            <div className="flex items-center gap-4">
              <span>$29.00</span>
              <span className="badge badge-success">Paid</span>
              <button className="text-primary hover:underline">Download</button>
            </div>
          </div>
          <div className="p-4 flex items-center justify-between text-sm">
            <div>
              <p className="font-medium">Invoice #000</p>
              <p className="text-foreground/50">Nov 1, 2024</p>
            </div>
            <div className="flex items-center gap-4">
              <span>$29.00</span>
              <span className="badge badge-success">Paid</span>
              <button className="text-primary hover:underline">Download</button>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
