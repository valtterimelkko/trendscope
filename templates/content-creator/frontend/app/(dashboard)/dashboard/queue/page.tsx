import { createClient } from '@/lib/supabase/server'
import Link from 'next/link'
import { formatRelativeDate } from '@/lib/utils'

export default async function QueuePage() {
  const supabase = await createClient()
  const { data: { user } } = await supabase.auth.getUser()

  // Fetch user's workspace
  const { data: workspaces } = await supabase
    .from('workspaces')
    .select('*, workspace_members!inner(*)')
    .eq('workspace_members.user_id', user?.id)
    .limit(1)

  const currentWorkspace = workspaces?.[0]

  // Fetch subscription for limits
  const { data: subscription } = await supabase
    .from('subscriptions')
    .select('*')
    .eq('workspace_id', currentWorkspace?.id)
    .eq('status', 'active')
    .single()

  // Fetch scheduled posts
  const { data: scheduledPosts } = await supabase
    .from('posts')
    .select(`
      *,
      author:profiles!author_id(id, display_name, avatar_url)
    `)
    .eq('workspace_id', currentWorkspace?.id)
    .eq('status', 'scheduled')
    .not('scheduled_for', 'is', null)
    .order('scheduled_for', { ascending: true })

  // Fetch connected accounts for channel display
  const { data: connections } = await supabase
    .from('social_connections')
    .select('*')
    .eq('workspace_id', currentWorkspace?.id)

  // Group posts by date
  const postsByDate = scheduledPosts?.reduce((acc: Record<string, typeof scheduledPosts>, post) => {
    const date = new Date(post.scheduled_for).toDateString()
    if (!acc[date]) acc[date] = []
    acc[date].push(post)
    return acc
  }, {}) || {}

  const scheduledLimit = subscription?.scheduled_limit || 5
  const scheduledCount = scheduledPosts?.length || 0
  const usagePercent = (scheduledCount / scheduledLimit) * 100

  return (
    <div className="p-6">
      {/* Page header */}
      <div className="flex items-center justify-between mb-8">
        <div>
          <h1 className="text-2xl font-bold text-foreground">
            {/* CONTENT_SLOT: queue.title */}
            Post Queue
          </h1>
          <p className="text-muted mt-1">
            {/* CONTENT_SLOT: queue.subtitle */}
            Manage your scheduled posts and upcoming content.
          </p>
        </div>
        <Link
          href="/dashboard/content/new"
          className="px-4 py-2 bg-primary text-white font-medium rounded-lg hover:bg-primary-hover transition-colors"
        >
          Schedule Post
        </Link>
      </div>

      {/* Queue stats */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-8">
        <div className="bg-surface border border-border rounded-xl p-4">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 bg-primary/10 rounded-lg flex items-center justify-center">
              <CalendarIcon className="w-5 h-5 text-primary" />
            </div>
            <div>
              <p className="text-2xl font-bold text-foreground">{scheduledCount}</p>
              <p className="text-sm text-muted">Scheduled posts</p>
            </div>
          </div>
        </div>

        <div className="bg-surface border border-border rounded-xl p-4">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 bg-green-500/10 rounded-lg flex items-center justify-center">
              <ClockIcon className="w-5 h-5 text-green-500" />
            </div>
            <div>
              <p className="text-2xl font-bold text-foreground">
                {scheduledPosts?.[0] ? formatNextPost(scheduledPosts[0].scheduled_for) : '--'}
              </p>
              <p className="text-sm text-muted">Next post</p>
            </div>
          </div>
        </div>

        <div className="bg-surface border border-border rounded-xl p-4">
          <div className="flex items-center justify-between mb-2">
            <p className="text-sm text-muted">Queue capacity</p>
            <p className="text-sm font-medium text-foreground">{scheduledCount} / {scheduledLimit}</p>
          </div>
          <div className="h-2 bg-surface-hover rounded-full overflow-hidden">
            <div
              className={`h-full rounded-full transition-all ${
                usagePercent >= 90 ? 'bg-red-500' : usagePercent >= 70 ? 'bg-yellow-500' : 'bg-primary'
              }`}
              style={{ width: `${Math.min(usagePercent, 100)}%` }}
            />
          </div>
          {usagePercent >= 80 && (
            <p className="text-xs text-yellow-600 mt-2">
              <a href="/dashboard/settings/billing" className="text-primary hover:underline">
                Upgrade
              </a>{' '}
              for unlimited scheduled posts.
            </p>
          )}
        </div>
      </div>

      {/* Empty state */}
      {(!scheduledPosts || scheduledPosts.length === 0) && (
        <div className="bg-surface border border-border border-dashed rounded-xl p-12 text-center">
          <div className="w-16 h-16 bg-surface-hover rounded-full flex items-center justify-center mx-auto mb-4">
            <QueueIcon className="w-8 h-8 text-muted" />
          </div>
          <h3 className="text-lg font-semibold text-foreground mb-2">
            {/* CONTENT_SLOT: queue.empty.title */}
            Your queue is empty
          </h3>
          <p className="text-muted mb-6 max-w-md mx-auto">
            {/* CONTENT_SLOT: queue.empty.description */}
            Schedule your first post to build a consistent content calendar. Your audience will thank you!
          </p>
          <Link
            href="/dashboard/content/new"
            className="inline-flex items-center gap-2 px-4 py-2 bg-primary text-white font-medium rounded-lg hover:bg-primary-hover transition-colors"
          >
            <PlusIcon className="w-4 h-4" />
            Create Your First Post
          </Link>
        </div>
      )}

      {/* Queue timeline */}
      {Object.keys(postsByDate).length > 0 && (
        <div className="space-y-8">
          {Object.entries(postsByDate).map(([dateString, posts]) => (
            <div key={dateString}>
              {/* Date header */}
              <div className="flex items-center gap-4 mb-4">
                <div className="flex items-center gap-2 text-sm font-medium text-foreground bg-surface border border-border px-3 py-1.5 rounded-lg">
                  <CalendarIcon className="w-4 h-4 text-muted" />
                  {formatDateHeader(dateString)}
                </div>
                <div className="flex-1 h-px bg-border" />
                <span className="text-xs text-muted">{posts.length} post{posts.length !== 1 ? 's' : ''}</span>
              </div>

              {/* Posts for this date */}
              <div className="space-y-3 pl-4 border-l-2 border-border ml-2">
                {posts.map((post) => (
                  <Link
                    key={post.id}
                    href={`/dashboard/content/${post.id}`}
                    className="block bg-surface border border-border rounded-xl p-4 hover:border-primary hover:shadow-sm transition-all group"
                  >
                    <div className="flex items-start gap-4">
                      {/* Time */}
                      <div className="flex-shrink-0 text-center">
                        <p className="text-lg font-semibold text-foreground">
                          {new Date(post.scheduled_for).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                        </p>
                        <p className="text-xs text-muted">
                          {formatRelativeDate(post.scheduled_for)}
                        </p>
                      </div>

                      {/* Divider */}
                      <div className="w-px h-12 bg-border flex-shrink-0" />

                      {/* Content preview */}
                      <div className="flex-1 min-w-0">
                        <h3 className="font-medium text-foreground group-hover:text-primary transition-colors truncate">
                          {post.title || 'Untitled post'}
                        </h3>
                        <p className="text-sm text-muted mt-1 line-clamp-2">
                          {post.excerpt || post.content?.substring(0, 120) || 'No content preview available'}
                        </p>

                        {/* Channels */}
                        {post.channels && post.channels.length > 0 && (
                          <div className="flex items-center gap-2 mt-3">
                            {post.channels.map((channelId: string) => {
                              const connection = connections?.find((c) => c.id === channelId)
                              return connection ? (
                                <span
                                  key={channelId}
                                  className="inline-flex items-center gap-1 text-xs px-2 py-1 bg-surface-hover rounded-md"
                                >
                                  {getPlatformIcon(connection.platform)}
                                  @{connection.username || connection.account_name}
                                </span>
                              ) : null
                            })}
                          </div>
                        )}
                      </div>

                      {/* Actions */}
                      <div className="flex-shrink-0 flex items-center gap-2 opacity-0 group-hover:opacity-100 transition-opacity">
                        <button
                          className="p-2 hover:bg-surface-hover rounded-lg transition-colors"
                          onClick={(e) => {
                            e.preventDefault()
                            // Edit action
                          }}
                        >
                          <EditIcon className="w-4 h-4 text-muted" />
                        </button>
                        <button
                          className="p-2 hover:bg-red-50 dark:hover:bg-red-900/20 rounded-lg transition-colors"
                          onClick={(e) => {
                            e.preventDefault()
                            // Delete action
                          }}
                        >
                          <TrashIcon className="w-4 h-4 text-red-500" />
                        </button>
                      </div>
                    </div>
                  </Link>
                ))}
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Queue settings tip */}
      <div className="mt-8 p-4 bg-surface-hover rounded-xl">
        <div className="flex items-start gap-3">
          <LightbulbIcon className="w-5 h-5 text-primary flex-shrink-0 mt-0.5" />
          <div>
            <p className="text-sm font-medium text-foreground">Pro tip</p>
            <p className="text-sm text-muted mt-0.5">
              {/* CONTENT_SLOT: queue.tip */}
              Set up your posting schedule in Settings to automatically fill your queue with optimal post times based on your audience.
            </p>
          </div>
        </div>
      </div>
    </div>
  )
}

// Helper functions
function formatNextPost(dateString: string): string {
  const date = new Date(dateString)
  const now = new Date()
  const diffMs = date.getTime() - now.getTime()
  const diffHours = Math.floor(diffMs / (1000 * 60 * 60))
  const diffDays = Math.floor(diffHours / 24)

  if (diffHours < 1) return 'Soon'
  if (diffHours < 24) return `${diffHours}h`
  return `${diffDays}d`
}

function formatDateHeader(dateString: string): string {
  const date = new Date(dateString)
  const today = new Date()
  const tomorrow = new Date(today)
  tomorrow.setDate(tomorrow.getDate() + 1)

  if (date.toDateString() === today.toDateString()) {
    return 'Today'
  }
  if (date.toDateString() === tomorrow.toDateString()) {
    return 'Tomorrow'
  }
  return date.toLocaleDateString('en-US', { weekday: 'long', month: 'short', day: 'numeric' })
}

function getPlatformIcon(platform: string) {
  const icons: Record<string, string> = {
    twitter: '𝕏',
    linkedin: 'in',
    facebook: 'f',
    instagram: '📷',
    threads: '🧵',
    bluesky: '🦋',
  }
  return icons[platform] || '📱'
}

// Icons
function CalendarIcon({ className }: { className?: string }) {
  return (
    <svg className={className} fill="none" viewBox="0 0 24 24" stroke="currentColor">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
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

function QueueIcon({ className }: { className?: string }) {
  return (
    <svg className={className} fill="none" viewBox="0 0 24 24" stroke="currentColor">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 10h16M4 14h16M4 18h16" />
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

function EditIcon({ className }: { className?: string }) {
  return (
    <svg className={className} fill="none" viewBox="0 0 24 24" stroke="currentColor">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
    </svg>
  )
}

function TrashIcon({ className }: { className?: string }) {
  return (
    <svg className={className} fill="none" viewBox="0 0 24 24" stroke="currentColor">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
    </svg>
  )
}

function LightbulbIcon({ className }: { className?: string }) {
  return (
    <svg className={className} fill="none" viewBox="0 0 24 24" stroke="currentColor">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
    </svg>
  )
}
