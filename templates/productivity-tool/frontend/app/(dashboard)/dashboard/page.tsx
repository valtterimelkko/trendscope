import { createClient } from '@/lib/supabase/server'
import { KanbanBoard } from '@/components/dashboard/KanbanBoard'
import { SidePeek } from '@/components/dashboard/SidePeek'

export default async function DashboardPage() {
  const supabase = await createClient()
  const { data: { user } } = await supabase.auth.getUser()

  // Fetch user's workspace
  const { data: workspaces } = await supabase
    .from('workspaces')
    .select('*, workspace_members!inner(*)')
    .eq('workspace_members.user_id', user?.id)
    .limit(1)

  const currentWorkspace = workspaces?.[0]

  // Fetch issues assigned to user or in their inbox
  const { data: issues } = await supabase
    .from('issues')
    .select(`
      *,
      project:projects(id, name, slug, color),
      assignee:profiles!assignee_id(id, display_name, avatar_url),
      creator:profiles!creator_id(id, display_name, avatar_url),
      labels:issue_labels(label:labels(*))
    `)
    .eq('workspace_id', currentWorkspace?.id)
    .or(`assignee_id.eq.${user?.id},assignee_id.is.null`)
    .order('sort_order', { ascending: true })

  // Group issues by status for Kanban
  const columns = {
    backlog: issues?.filter(i => i.status === 'backlog') || [],
    todo: issues?.filter(i => i.status === 'todo') || [],
    inprogress: issues?.filter(i => i.status === 'inprogress') || [],
    done: issues?.filter(i => i.status === 'done') || [],
  }

  return (
    <div className="h-full flex flex-col">
      {/* Keyboard hints banner */}
      <div className="px-4 py-2 bg-surface border-b border-border">
        <div className="flex items-center gap-4 text-xs text-muted">
          <span><kbd className="kbd">C</kbd> Create issue</span>
          <span><kbd className="kbd">⌘K</kbd> Command palette</span>
          <span><kbd className="kbd">J/K</kbd> Navigate</span>
          <span><kbd className="kbd">↵</kbd> Open issue</span>
          <span><kbd className="kbd">E</kbd> Edit</span>
        </div>
      </div>

      {/* Kanban board */}
      <div className="flex-1 overflow-hidden">
        <KanbanBoard columns={columns} />
      </div>

      {/* Side peek (rendered conditionally via URL params in real implementation) */}
      {/* <SidePeek issue={selectedIssue} onClose={() => {}} /> */}
    </div>
  )
}
