import { createClient } from '@/lib/supabase/server'
import Link from 'next/link'
import { formatRelativeDate, getStatusColor, truncate } from '@/lib/utils'

export default async function ContentPage() {
  const supabase = await createClient()
  const { data: { user } } = await supabase.auth.getUser()

  // Fetch user's workspace
  const { data: workspaces } = await supabase
    .from('workspaces')
    .select('*, workspace_members!inner(*)')
    .eq('workspace_members.user_id', user?.id)
    .limit(1)

  const currentWorkspace = workspaces?.[0]

  // Fetch posts
  const { data: posts } = await supabase
    .from('posts')
    .select(`
      *,
      author:profiles!author_id(id, display_name, avatar_url)
    `)
    .eq('workspace_id', currentWorkspace?.id)
    .order('updated_at', { ascending: false })

  const draftPosts = posts?.filter(p => p.status === 'draft') || []
  const publishedPosts = posts?.filter(p => p.status === 'published') || []
  const scheduledPosts = posts?.filter(p => p.status === 'scheduled') || []

  return (
    <div className="p-6">
      {/* Page header */}
      <div className="flex items-center justify-between mb-8">
        <div>
          <h1 className="text-2xl font-bold text-foreground">Content</h1>
          <p className="text-muted mt-1">Manage your posts and drafts</p>
        </div>
        <Link
          href="/dashboard/content/new"
          className="px-4 py-2 bg-primary text-white font-medium rounded-lg hover:bg-primary-hover transition-colors"
        >
          New Post
        </Link>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-8">
        <StatCard
          label="Total posts"
          value={posts?.length || 0}
          icon={DocumentIcon}
        />
        <StatCard
          label="Drafts"
          value={draftPosts.length}
          icon={PencilIcon}
          color="text-status-draft"
        />
        <StatCard
          label="Scheduled"
          value={scheduledPosts.length}
          icon={ClockIcon}
          color="text-status-scheduled"
        />
        <StatCard
          label="Published"
          value={publishedPosts.length}
          icon={CheckIcon}
          color="text-status-published"
        />
      </div>

      {/* Content tabs */}
      <div className="bg-surface border border-border rounded-xl overflow-hidden">
        {/* Tab header */}
        <div className="flex items-center border-b border-border">
          <button className="px-6 py-3 text-sm font-medium text-primary border-b-2 border-primary">
            All Posts
          </button>
          <button className="px-6 py-3 text-sm font-medium text-muted hover:text-foreground">
            Drafts ({draftPosts.length})
          </button>
          <button className="px-6 py-3 text-sm font-medium text-muted hover:text-foreground">
            Published ({publishedPosts.length})
          </button>
        </div>

        {/* Posts list */}
        {posts && posts.length > 0 ? (
          <div className="divide-y divide-border">
            {posts.map((post) => (
              <Link
                key={post.id}
                href={`/dashboard/content/${post.id}`}
                className="flex items-center gap-4 p-4 hover:bg-surface-hover transition-colors"
              >
                {/* Thumbnail */}
                <div className="w-20 h-14 bg-surface-hover rounded-lg overflow-hidden flex-shrink-0">
                  {post.featured_image ? (
                    <img
                      src={post.featured_image}
                      alt=""
                      className="w-full h-full object-cover"
                    />
                  ) : (
                    <div className="w-full h-full flex items-center justify-center">
                      <DocumentIcon className="w-6 h-6 text-muted" />
                    </div>
                  )}
                </div>

                {/* Content */}
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2 mb-1">
                    <h3 className="text-sm font-medium text-foreground truncate">
                      {post.title || 'Untitled'}
                    </h3>
                    <span className={`status-badge ${getStatusColor(post.status)}`}>
                      {post.status}
                    </span>
                  </div>
                  <p className="text-xs text-muted">
                    {truncate(post.excerpt || '', 100) || 'No excerpt'}
                  </p>
                </div>

                {/* Meta */}
                <div className="text-right text-xs text-muted flex-shrink-0">
                  <p>{formatRelativeDate(post.updated_at)}</p>
                  <p className="mt-0.5">by {post.author?.display_name || 'Unknown'}</p>
                </div>
              </Link>
            ))}
          </div>
        ) : (
          <div className="p-12 text-center">
            <DocumentIcon className="w-12 h-12 text-muted mx-auto mb-4" />
            <h3 className="text-lg font-medium text-foreground mb-2">No posts yet</h3>
            <p className="text-sm text-muted mb-6">
              Create your first post to get started
            </p>
            <Link
              href="/dashboard/content/new"
              className="inline-flex px-4 py-2 bg-primary text-white font-medium rounded-lg hover:bg-primary-hover transition-colors"
            >
              Create your first post
            </Link>
          </div>
        )}
      </div>
    </div>
  )
}

function StatCard({
  label,
  value,
  icon: Icon,
  color = 'text-foreground',
}: {
  label: string
  value: number
  icon: any
  color?: string
}) {
  return (
    <div className="bg-surface border border-border rounded-xl p-4">
      <div className="flex items-center gap-3">
        <div className={`p-2 rounded-lg bg-surface-hover ${color}`}>
          <Icon className="w-5 h-5" />
        </div>
        <div>
          <p className="text-2xl font-bold text-foreground">{value}</p>
          <p className="text-xs text-muted">{label}</p>
        </div>
      </div>
    </div>
  )
}

function DocumentIcon({ className }: { className?: string }) {
  return (
    <svg className={className} fill="none" viewBox="0 0 24 24" stroke="currentColor">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
    </svg>
  )
}

function PencilIcon({ className }: { className?: string }) {
  return (
    <svg className={className} fill="none" viewBox="0 0 24 24" stroke="currentColor">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15.232 5.232l3.536 3.536m-2.036-5.036a2.5 2.5 0 113.536 3.536L6.5 21.036H3v-3.572L16.732 3.732z" />
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

function CheckIcon({ className }: { className?: string }) {
  return (
    <svg className={className} fill="none" viewBox="0 0 24 24" stroke="currentColor">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
    </svg>
  )
}
