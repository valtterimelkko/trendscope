import { createClient } from '@/lib/supabase/server'
import Link from 'next/link'

export default async function ProjectsPage() {
  const supabase = await createClient()
  const { data: { user } } = await supabase.auth.getUser()

  // Fetch user's workspace
  const { data: workspaces } = await supabase
    .from('workspaces')
    .select('*, workspace_members!inner(*)')
    .eq('workspace_members.user_id', user?.id)
    .limit(1)

  const currentWorkspace = workspaces?.[0]

  // Fetch projects with issue counts
  const { data: projects } = await supabase
    .from('projects')
    .select(`
      *,
      lead:profiles!lead_id(id, display_name, avatar_url),
      issues(id, status)
    `)
    .eq('workspace_id', currentWorkspace?.id)
    .order('created_at', { ascending: false })

  return (
    <div className="h-full flex flex-col">
      {/* Header */}
      <div className="px-4 py-3 border-b border-border">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-lg font-semibold text-foreground">Projects</h2>
            <p className="text-sm text-muted">{projects?.length || 0} projects in this workspace</p>
          </div>
          <button className="flex items-center gap-1.5 px-3 py-1.5 bg-primary hover:bg-primary-hover text-white text-sm font-medium rounded-md transition-colors">
            <PlusIcon className="w-4 h-4" />
            <span>New Project</span>
          </button>
        </div>
      </div>

      {/* Projects grid */}
      <div className="flex-1 overflow-auto p-4">
        {projects && projects.length > 0 ? (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {projects.map((project) => {
              const totalIssues = project.issues?.length || 0
              const doneIssues = project.issues?.filter((i: any) => i.status === 'done').length || 0
              const progress = totalIssues > 0 ? (doneIssues / totalIssues) * 100 : 0

              return (
                <Link
                  key={project.id}
                  href={`/dashboard/projects/${project.slug}`}
                  className="block p-4 bg-surface border border-border rounded-lg hover:border-border-hover transition-colors group"
                >
                  <div className="flex items-start gap-3">
                    {/* Project icon */}
                    <div
                      className="w-10 h-10 rounded-lg flex items-center justify-center flex-shrink-0"
                      style={{ backgroundColor: `${project.color}20` }}
                    >
                      <span className="text-lg">{project.icon || '📁'}</span>
                    </div>

                    {/* Content */}
                    <div className="flex-1 min-w-0">
                      <h3 className="text-sm font-semibold text-foreground group-hover:text-primary transition-colors truncate">
                        {project.name}
                      </h3>
                      {project.description && (
                        <p className="text-xs text-muted mt-0.5 line-clamp-2">
                          {project.description}
                        </p>
                      )}
                    </div>
                  </div>

                  {/* Progress bar */}
                  <div className="mt-4">
                    <div className="flex items-center justify-between text-xs text-muted mb-1">
                      <span>{doneIssues} of {totalIssues} issues done</span>
                      <span>{Math.round(progress)}%</span>
                    </div>
                    <div className="h-1 bg-background rounded-full overflow-hidden">
                      <div
                        className="h-full bg-status-done rounded-full transition-all"
                        style={{ width: `${progress}%` }}
                      />
                    </div>
                  </div>

                  {/* Lead */}
                  {project.lead && (
                    <div className="flex items-center gap-2 mt-3 pt-3 border-t border-border">
                      <div className="w-5 h-5 bg-primary/20 rounded-full flex items-center justify-center">
                        <span className="text-xs font-medium text-primary">
                          {project.lead.display_name?.charAt(0) || 'U'}
                        </span>
                      </div>
                      <span className="text-xs text-muted">{project.lead.display_name}</span>
                    </div>
                  )}
                </Link>
              )
            })}
          </div>
        ) : (
          <div className="flex flex-col items-center justify-center h-full text-center px-4">
            <div className="w-12 h-12 bg-surface rounded-xl flex items-center justify-center mb-4">
              <FolderIcon className="w-6 h-6 text-muted" />
            </div>
            <h3 className="text-lg font-medium text-foreground mb-1">No projects yet</h3>
            <p className="text-sm text-muted max-w-xs mb-4">
              Create your first project to start organizing issues.
            </p>
            <button className="flex items-center gap-1.5 px-3 py-1.5 bg-primary hover:bg-primary-hover text-white text-sm font-medium rounded-md transition-colors">
              <PlusIcon className="w-4 h-4" />
              <span>Create Project</span>
            </button>
          </div>
        )}
      </div>
    </div>
  )
}

function PlusIcon({ className }: { className?: string }) {
  return (
    <svg className={className} fill="none" viewBox="0 0 24 24" stroke="currentColor">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
    </svg>
  )
}

function FolderIcon({ className }: { className?: string }) {
  return (
    <svg className={className} fill="none" viewBox="0 0 24 24" stroke="currentColor">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 7v10a2 2 0 002 2h14a2 2 0 002-2V9a2 2 0 00-2-2h-6l-2-2H5a2 2 0 00-2 2z" />
    </svg>
  )
}
