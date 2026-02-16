import { createClient } from '@/lib/supabase/server'
import Link from 'next/link'

export default async function SitesPage() {
  const supabase = await createClient()
  const { data: { user } } = await supabase.auth.getUser()

  // Fetch user's workspace
  const { data: workspaces } = await supabase
    .from('workspaces')
    .select('*, workspace_members!inner(*)')
    .eq('workspace_members.user_id', user?.id)
    .limit(1)

  const currentWorkspace = workspaces?.[0]

  // Fetch sites/properties
  const { data: sites } = await supabase
    .from('sites')
    .select('*')
    .eq('workspace_id', currentWorkspace?.id)
    .order('created_at', { ascending: false })

  // Get subscription for site limits
  const { data: subscription } = await supabase
    .from('subscriptions')
    .select('*')
    .eq('workspace_id', currentWorkspace?.id)
    .eq('status', 'active')
    .single()

  const siteLimit = subscription?.site_limit || 1
  const siteCount = sites?.length || 0
  const canAddSite = siteCount < siteLimit

  return (
    <div className="max-w-4xl">
      <div className="mb-8">
        <h1 className="text-2xl font-display font-bold">
          {/* CONTENT_SLOT: sites.title */}
          Your Sites
        </h1>
        <p className="text-foreground/70 mt-1">
          {/* CONTENT_SLOT: sites.subtitle */}
          Manage the websites you&apos;re tracking with analytics.
        </p>
      </div>

      {/* Site limit indicator */}
      <div className="card p-4 mb-6 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-lg bg-primary/10 flex items-center justify-center">
            <GlobeIcon className="w-5 h-5 text-primary" />
          </div>
          <div>
            <p className="font-medium">Sites used</p>
            <p className="text-sm text-foreground/60">{siteCount} of {siteLimit} sites</p>
          </div>
        </div>
        <div className="flex items-center gap-4">
          <div className="w-32 h-2 bg-gray-200 dark:bg-slate-700 rounded-full overflow-hidden">
            <div
              className={`h-full rounded-full transition-all ${
                siteCount >= siteLimit ? 'bg-warning' : 'bg-primary'
              }`}
              style={{ width: `${Math.min((siteCount / siteLimit) * 100, 100)}%` }}
            />
          </div>
          {!canAddSite && (
            <Link href="/settings/billing" className="btn-secondary text-sm">
              Upgrade
            </Link>
          )}
        </div>
      </div>

      {/* Add Site Button */}
      {canAddSite && (
        <button className="card p-6 w-full mb-6 border-2 border-dashed hover:border-primary hover:bg-primary/5 transition-colors group">
          <div className="flex items-center gap-4">
            <div className="w-12 h-12 rounded-xl bg-surface flex items-center justify-center group-hover:bg-primary/10 transition-colors">
              <PlusIcon className="w-6 h-6 text-muted group-hover:text-primary transition-colors" />
            </div>
            <div className="text-left">
              <p className="font-semibold text-foreground">Add a new site</p>
              <p className="text-sm text-foreground/60">
                {/* CONTENT_SLOT: sites.add.description */}
                Start tracking another website
              </p>
            </div>
          </div>
        </button>
      )}

      {/* Sites list */}
      {sites && sites.length > 0 ? (
        <div className="space-y-4">
          {sites.map((site) => (
            <Link
              key={site.id}
              href={`/dashboard?site=${site.id}`}
              className="card p-4 block hover:border-primary transition-colors group"
            >
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-4">
                  {/* Favicon */}
                  <div className="w-10 h-10 rounded-lg bg-surface flex items-center justify-center overflow-hidden">
                    {site.favicon_url ? (
                      <img
                        src={site.favicon_url}
                        alt=""
                        className="w-6 h-6"
                      />
                    ) : (
                      <GlobeIcon className="w-5 h-5 text-muted" />
                    )}
                  </div>
                  <div>
                    <p className="font-medium text-foreground group-hover:text-primary transition-colors">
                      {site.domain}
                    </p>
                    <p className="text-sm text-foreground/60">
                      Added {formatDate(site.created_at)}
                    </p>
                  </div>
                </div>

                <div className="flex items-center gap-6">
                  {/* Quick stats */}
                  <div className="text-right hidden sm:block">
                    <p className="text-lg font-semibold text-foreground">{formatNumber(site.total_visitors || 0)}</p>
                    <p className="text-xs text-foreground/60">visitors (30d)</p>
                  </div>

                  {/* Status indicator */}
                  <div className="flex items-center gap-2">
                    {site.verified ? (
                      <span className="flex items-center gap-1.5 text-sm text-success">
                        <CheckCircleIcon className="w-4 h-4" />
                        Active
                      </span>
                    ) : (
                      <span className="flex items-center gap-1.5 text-sm text-warning">
                        <ClockIcon className="w-4 h-4" />
                        Pending
                      </span>
                    )}
                  </div>

                  {/* Arrow */}
                  <ChevronRightIcon className="w-5 h-5 text-muted group-hover:text-primary transition-colors" />
                </div>
              </div>
            </Link>
          ))}
        </div>
      ) : (
        <div className="card p-12 text-center">
          <div className="w-16 h-16 rounded-full bg-surface flex items-center justify-center mx-auto mb-4">
            <GlobeIcon className="w-8 h-8 text-muted" />
          </div>
          <h3 className="text-lg font-semibold mb-2">
            {/* CONTENT_SLOT: sites.empty.title */}
            No sites yet
          </h3>
          <p className="text-foreground/60 mb-6 max-w-md mx-auto">
            {/* CONTENT_SLOT: sites.empty.description */}
            Add your first website to start tracking analytics. It only takes a minute.
          </p>
          <button className="btn-primary inline-flex items-center gap-2">
            <PlusIcon className="w-4 h-4" />
            Add Your First Site
          </button>
        </div>
      )}

      {/* Quick setup guide */}
      {sites && sites.length > 0 && sites.some((s) => !s.verified) && (
        <div className="card p-6 mt-6 bg-warning/5 border-warning/20">
          <div className="flex items-start gap-4">
            <div className="w-10 h-10 rounded-lg bg-warning/10 flex items-center justify-center flex-shrink-0">
              <AlertIcon className="w-5 h-5 text-warning" />
            </div>
            <div>
              <h3 className="font-semibold text-foreground">Complete your setup</h3>
              <p className="text-sm text-foreground/70 mt-1">
                Some sites are still pending verification. Add the tracking snippet to start collecting data.
              </p>
              <Link href="/snippet" className="text-sm text-primary hover:underline mt-2 inline-block">
                View installation instructions →
              </Link>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

// Helper functions
function formatDate(dateString: string): string {
  const date = new Date(dateString)
  return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' })
}

function formatNumber(num: number): string {
  if (num >= 1000000) return `${(num / 1000000).toFixed(1)}M`
  if (num >= 1000) return `${(num / 1000).toFixed(1)}K`
  return num.toString()
}

// Icons
function GlobeIcon({ className }: { className?: string }) {
  return (
    <svg className={className} fill="none" viewBox="0 0 24 24" stroke="currentColor">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 12a9 9 0 01-9 9m9-9a9 9 0 00-9-9m9 9H3m9 9a9 9 0 01-9-9m9 9c1.657 0 3-4.03 3-9s-1.343-9-3-9m0 18c-1.657 0-3-4.03-3-9s1.343-9 3-9m-9 9a9 9 0 019-9" />
    </svg>
  )
}

function PlusIcon({ className }: { className?: string }) {
  return (
    <svg className={className} fill="none" viewBox="0 0 24 24" stroke="currentColor">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
    </svg>
  )
}

function CheckCircleIcon({ className }: { className?: string }) {
  return (
    <svg className={className} fill="none" viewBox="0 0 24 24" stroke="currentColor">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
    </svg>
  )
}

function ClockIcon({ className }: { className?: string }) {
  return (
    <svg className={className} fill="none" viewBox="0 0 24 24" stroke="currentColor">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
    </svg>
  )
}

function ChevronRightIcon({ className }: { className?: string }) {
  return (
    <svg className={className} fill="none" viewBox="0 0 24 24" stroke="currentColor">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
    </svg>
  )
}

function AlertIcon({ className }: { className?: string }) {
  return (
    <svg className={className} fill="none" viewBox="0 0 24 24" stroke="currentColor">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
    </svg>
  )
}
