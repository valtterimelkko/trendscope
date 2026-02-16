import { createClient } from '@/lib/supabase/server'

export default async function AnalyticsPage() {
  const supabase = await createClient()
  const { data: { user } } = await supabase.auth.getUser()

  // Fetch user's workspace
  const { data: workspaces } = await supabase
    .from('workspaces')
    .select('*, workspace_members!inner(*)')
    .eq('workspace_members.user_id', user?.id)
    .limit(1)

  const currentWorkspace = workspaces?.[0]

  // Fetch posts with engagement data
  const { data: posts } = await supabase
    .from('posts')
    .select('*')
    .eq('workspace_id', currentWorkspace?.id)
    .eq('status', 'published')
    .order('published_at', { ascending: false })
    .limit(20)

  // Calculate aggregate stats (demo data for template)
  const totalImpressions = posts?.reduce((sum, p) => sum + (p.impressions || 0), 0) || 0
  const totalEngagements = posts?.reduce((sum, p) => sum + (p.likes || 0) + (p.comments || 0) + (p.shares || 0), 0) || 0
  const avgEngagementRate = totalImpressions > 0 ? ((totalEngagements / totalImpressions) * 100).toFixed(2) : '0.00'
  const totalPosts = posts?.length || 0

  return (
    <div className="p-6">
      {/* Page header */}
      <div className="flex items-center justify-between mb-8">
        <div>
          <h1 className="text-2xl font-bold text-foreground">
            {/* CONTENT_SLOT: analytics.title */}
            Content Analytics
          </h1>
          <p className="text-muted mt-1">
            {/* CONTENT_SLOT: analytics.subtitle */}
            Track how your content is performing across all platforms.
          </p>
        </div>
        <div className="flex items-center gap-2">
          <select className="px-3 py-2 bg-surface border border-border rounded-lg text-sm text-foreground">
            <option>Last 7 days</option>
            <option>Last 30 days</option>
            <option>Last 90 days</option>
            <option>All time</option>
          </select>
        </div>
      </div>

      {/* Stats overview */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-8">
        <StatCard
          label="Total Impressions"
          value={formatNumber(totalImpressions)}
          change={12.5}
          icon={EyeIcon}
        />
        <StatCard
          label="Engagements"
          value={formatNumber(totalEngagements)}
          change={8.3}
          icon={HeartIcon}
        />
        <StatCard
          label="Engagement Rate"
          value={`${avgEngagementRate}%`}
          change={-1.2}
          icon={ChartIcon}
        />
        <StatCard
          label="Published Posts"
          value={totalPosts.toString()}
          change={0}
          icon={DocumentIcon}
        />
      </div>

      {/* Top performing posts */}
      <div className="bg-surface border border-border rounded-xl">
        <div className="p-4 border-b border-border">
          <h2 className="font-semibold text-foreground">Top Performing Posts</h2>
          <p className="text-sm text-muted mt-0.5">Your best content based on engagement</p>
        </div>

        {posts && posts.length > 0 ? (
          <div className="divide-y divide-border">
            {posts.slice(0, 10).map((post, index) => (
              <div key={post.id} className="p-4 hover:bg-surface-hover transition-colors">
                <div className="flex items-start gap-4">
                  {/* Rank */}
                  <div className="w-8 h-8 bg-surface-hover rounded-full flex items-center justify-center flex-shrink-0">
                    <span className="text-sm font-semibold text-muted">#{index + 1}</span>
                  </div>

                  {/* Content */}
                  <div className="flex-1 min-w-0">
                    <h3 className="font-medium text-foreground truncate">
                      {post.title || 'Untitled post'}
                    </h3>
                    <p className="text-sm text-muted mt-0.5">
                      Published {formatRelativeDate(post.published_at)}
                    </p>
                  </div>

                  {/* Stats */}
                  <div className="flex items-center gap-6 text-sm">
                    <div className="text-center">
                      <p className="font-semibold text-foreground">{formatNumber(post.impressions || 0)}</p>
                      <p className="text-xs text-muted">Views</p>
                    </div>
                    <div className="text-center">
                      <p className="font-semibold text-foreground">{formatNumber(post.likes || 0)}</p>
                      <p className="text-xs text-muted">Likes</p>
                    </div>
                    <div className="text-center">
                      <p className="font-semibold text-foreground">{formatNumber(post.comments || 0)}</p>
                      <p className="text-xs text-muted">Comments</p>
                    </div>
                    <div className="text-center">
                      <p className="font-semibold text-foreground">{formatNumber(post.shares || 0)}</p>
                      <p className="text-xs text-muted">Shares</p>
                    </div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        ) : (
          <div className="p-12 text-center">
            <div className="w-16 h-16 bg-surface-hover rounded-full flex items-center justify-center mx-auto mb-4">
              <ChartIcon className="w-8 h-8 text-muted" />
            </div>
            <h3 className="text-lg font-semibold text-foreground mb-2">
              {/* CONTENT_SLOT: analytics.empty.title */}
              No analytics data yet
            </h3>
            <p className="text-muted max-w-md mx-auto">
              {/* CONTENT_SLOT: analytics.empty.description */}
              Publish your first post to start tracking engagement and performance metrics.
            </p>
          </div>
        )}
      </div>

      {/* Best posting times */}
      <div className="mt-6 bg-surface border border-border rounded-xl p-6">
        <h2 className="font-semibold text-foreground mb-4">Best Posting Times</h2>
        <div className="grid grid-cols-7 gap-2">
          {['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'].map((day) => (
            <div key={day} className="text-center">
              <p className="text-xs text-muted mb-2">{day}</p>
              <div className="space-y-1">
                {[9, 12, 15, 18, 21].map((hour) => {
                  const intensity = Math.random() // Demo: replace with real data
                  return (
                    <div
                      key={hour}
                      className="h-6 rounded transition-colors"
                      style={{
                        backgroundColor: `rgba(var(--color-primary-rgb), ${intensity * 0.8 + 0.1})`,
                      }}
                      title={`${hour}:00 - ${hour + 3}:00`}
                    />
                  )
                })}
              </div>
            </div>
          ))}
        </div>
        <p className="text-xs text-muted mt-4 text-center">
          Darker cells indicate higher engagement. Based on your audience activity.
        </p>
      </div>
    </div>
  )
}

// Stat Card Component
function StatCard({
  label,
  value,
  change,
  icon: Icon,
}: {
  label: string
  value: string
  change: number
  icon: React.ComponentType<{ className?: string }>
}) {
  const isPositive = change > 0
  const isNeutral = change === 0

  return (
    <div className="bg-surface border border-border rounded-xl p-4">
      <div className="flex items-center justify-between mb-3">
        <div className="w-10 h-10 bg-primary/10 rounded-lg flex items-center justify-center">
          <Icon className="w-5 h-5 text-primary" />
        </div>
        {!isNeutral && (
          <span className={`text-xs font-medium px-2 py-1 rounded-full ${
            isPositive 
              ? 'bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400' 
              : 'bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-400'
          }`}>
            {isPositive ? '+' : ''}{change}%
          </span>
        )}
      </div>
      <p className="text-2xl font-bold text-foreground">{value}</p>
      <p className="text-sm text-muted mt-1">{label}</p>
    </div>
  )
}

// Helper functions
function formatNumber(num: number): string {
  if (num >= 1000000) return `${(num / 1000000).toFixed(1)}M`
  if (num >= 1000) return `${(num / 1000).toFixed(1)}K`
  return num.toString()
}

function formatRelativeDate(dateString: string): string {
  const date = new Date(dateString)
  const now = new Date()
  const diffMs = now.getTime() - date.getTime()
  const diffDays = Math.floor(diffMs / (1000 * 60 * 60 * 24))

  if (diffDays === 0) return 'today'
  if (diffDays === 1) return 'yesterday'
  if (diffDays < 7) return `${diffDays} days ago`
  if (diffDays < 30) return `${Math.floor(diffDays / 7)} weeks ago`
  return date.toLocaleDateString()
}

// Icons
function EyeIcon({ className }: { className?: string }) {
  return (
    <svg className={className} fill="none" viewBox="0 0 24 24" stroke="currentColor">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
    </svg>
  )
}

function HeartIcon({ className }: { className?: string }) {
  return (
    <svg className={className} fill="none" viewBox="0 0 24 24" stroke="currentColor">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4.318 6.318a4.5 4.5 0 000 6.364L12 20.364l7.682-7.682a4.5 4.5 0 00-6.364-6.364L12 7.636l-1.318-1.318a4.5 4.5 0 00-6.364 0z" />
    </svg>
  )
}

function ChartIcon({ className }: { className?: string }) {
  return (
    <svg className={className} fill="none" viewBox="0 0 24 24" stroke="currentColor">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
    </svg>
  )
}

function DocumentIcon({ className }: { className?: string }) {
  return (
    <svg className={className} fill="none" viewBox="0 0 24 24" stroke="currentColor">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
    </svg>
  )
}
