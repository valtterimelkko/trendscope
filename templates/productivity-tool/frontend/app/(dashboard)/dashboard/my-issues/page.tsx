import { createClient } from '@/lib/supabase/server'

export default async function MyIssuesPage() {
  const supabase = await createClient()
  const { data: { user } } = await supabase.auth.getUser()

  // Fetch user's workspace
  const { data: workspaces } = await supabase
    .from('workspaces')
    .select('*, workspace_members!inner(*)')
    .eq('workspace_members.user_id', user?.id)
    .limit(1)

  const currentWorkspace = workspaces?.[0]

  // Fetch issues assigned to the current user
  const { data: issues } = await supabase
    .from('issues')
    .select(`
      *,
      project:projects(id, name, slug, color),
      labels:issue_labels(label:labels(*))
    `)
    .eq('workspace_id', currentWorkspace?.id)
    .eq('assignee_id', user?.id)
    .neq('status', 'done')
    .neq('status', 'canceled')
    .order('priority', { ascending: false })
    .order('created_at', { ascending: false })

  const priorityOrder = ['urgent', 'high', 'medium', 'low', 'none']

  return (
    <div className="h-full flex flex-col">
      {/* Header */}
      <div className="px-4 py-3 border-b border-border">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-lg font-semibold text-foreground">My Issues</h2>
            <p className="text-sm text-muted">{issues?.length || 0} open issues assigned to you</p>
          </div>
        </div>
      </div>

      {/* Issue list */}
      <div className="flex-1 overflow-auto">
        {issues && issues.length > 0 ? (
          <div className="divide-y divide-border">
            {issues.map((issue) => (
              <div
                key={issue.id}
                className="px-4 py-3 hover:bg-surface-hover transition-colors cursor-pointer group"
              >
                <div className="flex items-start gap-3">
                  {/* Priority indicator */}
                  <div className={`w-1 h-10 rounded-full flex-shrink-0 ${getPriorityColor(issue.priority)}`} />

                  {/* Status icon */}
                  <div className="flex-shrink-0 mt-0.5">
                    <StatusIcon status={issue.status} />
                  </div>

                  {/* Content */}
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2">
                      <span className="text-xs text-muted font-mono">{issue.identifier}</span>
                      {issue.project && (
                        <span
                          className="text-xs px-1.5 py-0.5 rounded"
                          style={{
                            backgroundColor: `${issue.project.color}20`,
                            color: issue.project.color
                          }}
                        >
                          {issue.project.name}
                        </span>
                      )}
                    </div>
                    <h3 className="text-sm font-medium text-foreground mt-0.5 group-hover:text-primary transition-colors">
                      {issue.title}
                    </h3>
                    {issue.labels && issue.labels.length > 0 && (
                      <div className="flex items-center gap-1 mt-1">
                        {issue.labels.map((il: any) => (
                          <span
                            key={il.label.id}
                            className="text-xs px-1.5 py-0.5 rounded"
                            style={{
                              backgroundColor: `${il.label.color}20`,
                              color: il.label.color
                            }}
                          >
                            {il.label.name}
                          </span>
                        ))}
                      </div>
                    )}
                  </div>

                  {/* Due date */}
                  {issue.due_date && (
                    <div className="flex-shrink-0 text-xs text-muted">
                      {new Date(issue.due_date).toLocaleDateString()}
                    </div>
                  )}
                </div>
              </div>
            ))}
          </div>
        ) : (
          <div className="flex flex-col items-center justify-center h-full text-center px-4">
            <div className="w-12 h-12 bg-surface rounded-xl flex items-center justify-center mb-4">
              <CheckIcon className="w-6 h-6 text-status-done" />
            </div>
            <h3 className="text-lg font-medium text-foreground mb-1">All caught up!</h3>
            <p className="text-sm text-muted max-w-xs">
              You have no open issues assigned to you. Press <kbd className="kbd">C</kbd> to create a new issue.
            </p>
          </div>
        )}
      </div>
    </div>
  )
}

function getPriorityColor(priority: string) {
  switch (priority) {
    case 'urgent': return 'bg-red-500'
    case 'high': return 'bg-orange-500'
    case 'medium': return 'bg-yellow-500'
    case 'low': return 'bg-blue-500'
    default: return 'bg-gray-500'
  }
}

function StatusIcon({ status }: { status: string }) {
  const baseClasses = "w-4 h-4 rounded-full border-2"

  switch (status) {
    case 'backlog':
      return <div className={`${baseClasses} border-status-backlog border-dashed`} />
    case 'todo':
      return <div className={`${baseClasses} border-status-todo`} />
    case 'inprogress':
      return (
        <div className={`${baseClasses} border-status-inprogress relative`}>
          <div className="absolute inset-0 bg-status-inprogress rounded-full scale-50" />
        </div>
      )
    case 'done':
      return (
        <div className={`${baseClasses} border-status-done bg-status-done flex items-center justify-center`}>
          <svg className="w-2.5 h-2.5 text-background" fill="currentColor" viewBox="0 0 20 20">
            <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
          </svg>
        </div>
      )
    default:
      return <div className={`${baseClasses} border-muted`} />
  }
}

function CheckIcon({ className }: { className?: string }) {
  return (
    <svg className={className} fill="none" viewBox="0 0 24 24" stroke="currentColor">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
    </svg>
  )
}
