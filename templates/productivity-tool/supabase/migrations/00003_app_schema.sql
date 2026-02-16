-- Productivity Tool: App-Specific Schema
-- Creates projects, issues, labels, and comments

-- Projects (containers for issues)
CREATE TABLE IF NOT EXISTS public.projects (
  id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  workspace_id UUID REFERENCES public.workspaces(id) ON DELETE CASCADE NOT NULL,
  name TEXT NOT NULL,
  slug TEXT NOT NULL,
  description TEXT,
  color TEXT DEFAULT '#5E6AD2',
  icon TEXT DEFAULT 'folder',
  lead_id UUID REFERENCES public.profiles(id) ON DELETE SET NULL,
  created_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
  updated_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
  UNIQUE(workspace_id, slug)
);

-- Enable RLS
ALTER TABLE public.projects ENABLE ROW LEVEL SECURITY;

-- Labels
CREATE TABLE IF NOT EXISTS public.labels (
  id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  workspace_id UUID REFERENCES public.workspaces(id) ON DELETE CASCADE NOT NULL,
  name TEXT NOT NULL,
  color TEXT NOT NULL,
  description TEXT,
  created_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
  UNIQUE(workspace_id, name)
);

-- Enable RLS
ALTER TABLE public.labels ENABLE ROW LEVEL SECURITY;

-- Issues (the core entity)
CREATE TABLE IF NOT EXISTS public.issues (
  id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  workspace_id UUID REFERENCES public.workspaces(id) ON DELETE CASCADE NOT NULL,
  project_id UUID REFERENCES public.projects(id) ON DELETE CASCADE,

  -- Issue identifier (e.g., PROD-123)
  number SERIAL,
  identifier TEXT GENERATED ALWAYS AS (
    COALESCE(
      (SELECT UPPER(LEFT(slug, 4)) FROM public.projects WHERE id = project_id),
      'TASK'
    ) || '-' || number
  ) STORED,

  -- Content
  title TEXT NOT NULL,
  description TEXT,

  -- Status & Priority
  status TEXT DEFAULT 'backlog' CHECK (status IN (
    'backlog', 'todo', 'inprogress', 'done', 'canceled'
  )) NOT NULL,
  priority TEXT DEFAULT 'medium' CHECK (priority IN (
    'urgent', 'high', 'medium', 'low', 'none'
  )) NOT NULL,

  -- Assignments
  assignee_id UUID REFERENCES public.profiles(id) ON DELETE SET NULL,
  creator_id UUID REFERENCES public.profiles(id) ON DELETE SET NULL NOT NULL,

  -- Dates
  due_date DATE,
  started_at TIMESTAMPTZ,
  completed_at TIMESTAMPTZ,

  -- Ordering
  sort_order REAL DEFAULT 0,

  -- Timestamps
  created_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
  updated_at TIMESTAMPTZ DEFAULT NOW() NOT NULL
);

-- Enable RLS
ALTER TABLE public.issues ENABLE ROW LEVEL SECURITY;

-- Issue labels (many-to-many)
CREATE TABLE IF NOT EXISTS public.issue_labels (
  issue_id UUID REFERENCES public.issues(id) ON DELETE CASCADE,
  label_id UUID REFERENCES public.labels(id) ON DELETE CASCADE,
  PRIMARY KEY (issue_id, label_id)
);

-- Enable RLS
ALTER TABLE public.issue_labels ENABLE ROW LEVEL SECURITY;

-- Comments
CREATE TABLE IF NOT EXISTS public.comments (
  id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  issue_id UUID REFERENCES public.issues(id) ON DELETE CASCADE NOT NULL,
  author_id UUID REFERENCES public.profiles(id) ON DELETE SET NULL NOT NULL,
  body TEXT NOT NULL,
  created_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
  updated_at TIMESTAMPTZ DEFAULT NOW() NOT NULL
);

-- Enable RLS
ALTER TABLE public.comments ENABLE ROW LEVEL SECURITY;

-- RLS Policies

-- Projects: Workspace members can CRUD
CREATE POLICY "Workspace members can manage projects"
  ON public.projects FOR ALL
  USING (
    EXISTS (
      SELECT 1 FROM public.workspace_members
      WHERE workspace_members.workspace_id = projects.workspace_id
      AND workspace_members.user_id = auth.uid()
    )
  );

-- Labels: Workspace members can CRUD
CREATE POLICY "Workspace members can manage labels"
  ON public.labels FOR ALL
  USING (
    EXISTS (
      SELECT 1 FROM public.workspace_members
      WHERE workspace_members.workspace_id = labels.workspace_id
      AND workspace_members.user_id = auth.uid()
    )
  );

-- Issues: Workspace members can CRUD
CREATE POLICY "Workspace members can manage issues"
  ON public.issues FOR ALL
  USING (
    EXISTS (
      SELECT 1 FROM public.workspace_members
      WHERE workspace_members.workspace_id = issues.workspace_id
      AND workspace_members.user_id = auth.uid()
    )
  );

-- Issue labels: Based on issue access
CREATE POLICY "Issue label access follows issue access"
  ON public.issue_labels FOR ALL
  USING (
    EXISTS (
      SELECT 1 FROM public.issues
      JOIN public.workspace_members ON workspace_members.workspace_id = issues.workspace_id
      WHERE issues.id = issue_labels.issue_id
      AND workspace_members.user_id = auth.uid()
    )
  );

-- Comments: Workspace members can view, authors can edit/delete
CREATE POLICY "Workspace members can view comments"
  ON public.comments FOR SELECT
  USING (
    EXISTS (
      SELECT 1 FROM public.issues
      JOIN public.workspace_members ON workspace_members.workspace_id = issues.workspace_id
      WHERE issues.id = comments.issue_id
      AND workspace_members.user_id = auth.uid()
    )
  );

CREATE POLICY "Authors can manage their comments"
  ON public.comments FOR ALL
  USING (auth.uid() = author_id);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_issues_workspace_status ON public.issues(workspace_id, status);
CREATE INDEX IF NOT EXISTS idx_issues_project_id ON public.issues(project_id);
CREATE INDEX IF NOT EXISTS idx_issues_assignee_id ON public.issues(assignee_id);
CREATE INDEX IF NOT EXISTS idx_issues_creator_id ON public.issues(creator_id);
CREATE INDEX IF NOT EXISTS idx_issues_sort_order ON public.issues(workspace_id, sort_order);
CREATE INDEX IF NOT EXISTS idx_comments_issue_id ON public.comments(issue_id);

-- Triggers for updated_at
CREATE TRIGGER update_projects_updated_at
  BEFORE UPDATE ON public.projects
  FOR EACH ROW EXECUTE FUNCTION public.update_updated_at_column();

CREATE TRIGGER update_issues_updated_at
  BEFORE UPDATE ON public.issues
  FOR EACH ROW EXECUTE FUNCTION public.update_updated_at_column();

CREATE TRIGGER update_comments_updated_at
  BEFORE UPDATE ON public.comments
  FOR EACH ROW EXECUTE FUNCTION public.update_updated_at_column();

-- Function to auto-set completed_at when status changes to done
CREATE OR REPLACE FUNCTION public.handle_issue_status_change()
RETURNS TRIGGER AS $$
BEGIN
  IF NEW.status = 'done' AND OLD.status != 'done' THEN
    NEW.completed_at = NOW();
  ELSIF NEW.status = 'inprogress' AND OLD.status NOT IN ('inprogress', 'done') THEN
    NEW.started_at = COALESCE(NEW.started_at, NOW());
  ELSIF NEW.status NOT IN ('done', 'canceled') AND OLD.status = 'done' THEN
    NEW.completed_at = NULL;
  END IF;
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER on_issue_status_change
  BEFORE UPDATE ON public.issues
  FOR EACH ROW
  WHEN (OLD.status IS DISTINCT FROM NEW.status)
  EXECUTE FUNCTION public.handle_issue_status_change();
