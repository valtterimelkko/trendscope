import { createClient } from '@/lib/supabase/server'
import { ContentCalendar } from '@/components/dashboard/ContentCalendar'

export default async function CalendarPage() {
  const supabase = await createClient()
  const { data: { user } } = await supabase.auth.getUser()

  // Fetch user's workspace
  const { data: workspaces } = await supabase
    .from('workspaces')
    .select('*, workspace_members!inner(*)')
    .eq('workspace_members.user_id', user?.id)
    .limit(1)

  const currentWorkspace = workspaces?.[0]

  // Fetch posts with scheduled or published dates
  const { data: posts } = await supabase
    .from('posts')
    .select('id, title, status, scheduled_for, published_at')
    .eq('workspace_id', currentWorkspace?.id)
    .or('scheduled_for.not.is.null,published_at.not.is.null')
    .order('scheduled_for', { ascending: true })

  return (
    <div className="p-6">
      {/* Page header */}
      <div className="flex items-center justify-between mb-8">
        <div>
          <h1 className="text-2xl font-bold text-foreground">Content Calendar</h1>
          <p className="text-muted mt-1">Plan and schedule your content</p>
        </div>
        <div className="flex items-center gap-3">
          <div className="flex items-center gap-4 text-sm">
            <div className="flex items-center gap-2">
              <div className="w-3 h-3 rounded-full bg-gray-400"></div>
              <span className="text-muted">Draft</span>
            </div>
            <div className="flex items-center gap-2">
              <div className="w-3 h-3 rounded-full bg-yellow-400"></div>
              <span className="text-muted">Review</span>
            </div>
            <div className="flex items-center gap-2">
              <div className="w-3 h-3 rounded-full bg-green-400"></div>
              <span className="text-muted">Scheduled</span>
            </div>
            <div className="flex items-center gap-2">
              <div className="w-3 h-3 rounded-full bg-primary"></div>
              <span className="text-muted">Published</span>
            </div>
          </div>
        </div>
      </div>

      {/* Calendar */}
      <ContentCalendar posts={posts || []} />

      {/* Tips */}
      <div className="mt-6 p-4 bg-primary-light rounded-xl">
        <div className="flex items-start gap-3">
          <LightbulbIcon className="w-5 h-5 text-primary flex-shrink-0 mt-0.5" />
          <div>
            <p className="text-sm font-medium text-foreground">Pro tip</p>
            <p className="text-sm text-muted mt-0.5">
              Click on any date to create a new post scheduled for that day. Drag posts between dates to reschedule them.
            </p>
          </div>
        </div>
      </div>
    </div>
  )
}

function LightbulbIcon({ className }: { className?: string }) {
  return (
    <svg className={className} fill="none" viewBox="0 0 24 24" stroke="currentColor">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
    </svg>
  )
}
