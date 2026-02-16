-- Content Creator: App-Specific Schema
-- Creates posts, media, and categories

-- Categories/Tags
CREATE TABLE IF NOT EXISTS public.categories (
  id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  workspace_id UUID REFERENCES public.workspaces(id) ON DELETE CASCADE NOT NULL,
  name TEXT NOT NULL,
  slug TEXT NOT NULL,
  color TEXT DEFAULT '#E07A5F',
  description TEXT,
  created_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
  UNIQUE(workspace_id, slug)
);

-- Enable RLS
ALTER TABLE public.categories ENABLE ROW LEVEL SECURITY;

-- Posts (the core entity)
CREATE TABLE IF NOT EXISTS public.posts (
  id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  workspace_id UUID REFERENCES public.workspaces(id) ON DELETE CASCADE NOT NULL,
  author_id UUID REFERENCES public.profiles(id) ON DELETE SET NULL NOT NULL,

  -- Content
  title TEXT,
  slug TEXT,
  excerpt TEXT,
  content TEXT,
  featured_image TEXT,

  -- Status
  status TEXT DEFAULT 'draft' CHECK (status IN (
    'draft', 'review', 'scheduled', 'published', 'archived'
  )) NOT NULL,

  -- Scheduling
  scheduled_for TIMESTAMPTZ,
  published_at TIMESTAMPTZ,

  -- SEO
  meta_title TEXT,
  meta_description TEXT,

  -- Timestamps
  created_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
  updated_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,

  UNIQUE(workspace_id, slug)
);

-- Enable RLS
ALTER TABLE public.posts ENABLE ROW LEVEL SECURITY;

-- Post categories (many-to-many)
CREATE TABLE IF NOT EXISTS public.post_categories (
  post_id UUID REFERENCES public.posts(id) ON DELETE CASCADE,
  category_id UUID REFERENCES public.categories(id) ON DELETE CASCADE,
  PRIMARY KEY (post_id, category_id)
);

-- Enable RLS
ALTER TABLE public.post_categories ENABLE ROW LEVEL SECURITY;

-- Media library
CREATE TABLE IF NOT EXISTS public.media (
  id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  workspace_id UUID REFERENCES public.workspaces(id) ON DELETE CASCADE NOT NULL,
  uploaded_by UUID REFERENCES public.profiles(id) ON DELETE SET NULL,

  -- File info
  name TEXT NOT NULL,
  url TEXT NOT NULL,
  type TEXT,
  size_bytes BIGINT,

  -- Metadata
  alt_text TEXT,
  caption TEXT,

  -- Timestamps
  created_at TIMESTAMPTZ DEFAULT NOW() NOT NULL
);

-- Enable RLS
ALTER TABLE public.media ENABLE ROW LEVEL SECURITY;

-- RLS Policies

-- Categories: Workspace members can CRUD
CREATE POLICY "Workspace members can manage categories"
  ON public.categories FOR ALL
  USING (
    EXISTS (
      SELECT 1 FROM public.workspace_members
      WHERE workspace_members.workspace_id = categories.workspace_id
      AND workspace_members.user_id = auth.uid()
    )
  );

-- Posts: Workspace members can view, editors+ can manage
CREATE POLICY "Workspace members can view posts"
  ON public.posts FOR SELECT
  USING (
    EXISTS (
      SELECT 1 FROM public.workspace_members
      WHERE workspace_members.workspace_id = posts.workspace_id
      AND workspace_members.user_id = auth.uid()
    )
  );

CREATE POLICY "Editors can manage posts"
  ON public.posts FOR ALL
  USING (
    EXISTS (
      SELECT 1 FROM public.workspace_members
      WHERE workspace_members.workspace_id = posts.workspace_id
      AND workspace_members.user_id = auth.uid()
      AND workspace_members.role IN ('owner', 'admin', 'editor')
    )
  );

-- Authors can always edit their own posts
CREATE POLICY "Authors can manage own posts"
  ON public.posts FOR ALL
  USING (auth.uid() = author_id);

-- Post categories: Based on post access
CREATE POLICY "Post category access follows post access"
  ON public.post_categories FOR ALL
  USING (
    EXISTS (
      SELECT 1 FROM public.posts
      JOIN public.workspace_members ON workspace_members.workspace_id = posts.workspace_id
      WHERE posts.id = post_categories.post_id
      AND workspace_members.user_id = auth.uid()
      AND workspace_members.role IN ('owner', 'admin', 'editor')
    )
  );

-- Media: Workspace members can manage
CREATE POLICY "Workspace members can manage media"
  ON public.media FOR ALL
  USING (
    EXISTS (
      SELECT 1 FROM public.workspace_members
      WHERE workspace_members.workspace_id = media.workspace_id
      AND workspace_members.user_id = auth.uid()
    )
  );

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_posts_workspace_status ON public.posts(workspace_id, status);
CREATE INDEX IF NOT EXISTS idx_posts_author_id ON public.posts(author_id);
CREATE INDEX IF NOT EXISTS idx_posts_published_at ON public.posts(published_at);
CREATE INDEX IF NOT EXISTS idx_posts_scheduled_for ON public.posts(scheduled_for);
CREATE INDEX IF NOT EXISTS idx_media_workspace_id ON public.media(workspace_id);
CREATE INDEX IF NOT EXISTS idx_categories_workspace_id ON public.categories(workspace_id);

-- Triggers for updated_at
CREATE TRIGGER update_posts_updated_at
  BEFORE UPDATE ON public.posts
  FOR EACH ROW EXECUTE FUNCTION public.update_updated_at_column();

-- Function to auto-set published_at when status changes to published
CREATE OR REPLACE FUNCTION public.handle_post_status_change()
RETURNS TRIGGER AS $$
BEGIN
  IF NEW.status = 'published' AND OLD.status != 'published' THEN
    NEW.published_at = COALESCE(NEW.published_at, NOW());
  END IF;
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER on_post_status_change
  BEFORE UPDATE ON public.posts
  FOR EACH ROW
  WHEN (OLD.status IS DISTINCT FROM NEW.status)
  EXECUTE FUNCTION public.handle_post_status_change();

-- Function to check post limit before insert
CREATE OR REPLACE FUNCTION public.check_post_limit()
RETURNS TRIGGER AS $$
BEGIN
  IF NOT public.can_use_feature(NEW.workspace_id, 'posts') THEN
    RAISE EXCEPTION 'Post limit reached. Please upgrade your plan.';
  END IF;
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER before_post_insert
  BEFORE INSERT ON public.posts
  FOR EACH ROW EXECUTE FUNCTION public.check_post_limit();

-- Function to check scheduled post limit
CREATE OR REPLACE FUNCTION public.check_scheduled_limit()
RETURNS TRIGGER AS $$
BEGIN
  IF NEW.status = 'scheduled' AND OLD.status != 'scheduled' THEN
    IF NOT public.can_use_feature(NEW.workspace_id, 'scheduled') THEN
      RAISE EXCEPTION 'Scheduled post limit reached. Please upgrade your plan.';
    END IF;
  END IF;
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER before_post_schedule
  BEFORE UPDATE ON public.posts
  FOR EACH ROW
  WHEN (NEW.status = 'scheduled' AND OLD.status IS DISTINCT FROM NEW.status)
  EXECUTE FUNCTION public.check_scheduled_limit();
