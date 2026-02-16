-- Analytics Dashboard: App-Specific Schema
-- Creates sites (domains being tracked), events, and public share settings

-- Sites (domains being tracked)
CREATE TABLE IF NOT EXISTS public.sites (
  id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  team_id UUID REFERENCES public.teams(id) ON DELETE CASCADE,
  user_id UUID REFERENCES public.profiles(id) ON DELETE CASCADE NOT NULL,
  domain TEXT NOT NULL,
  name TEXT,
  is_public BOOLEAN DEFAULT FALSE NOT NULL,
  public_slug TEXT UNIQUE,
  timezone TEXT DEFAULT 'UTC' NOT NULL,
  created_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
  updated_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
  UNIQUE(user_id, domain)
);

-- Enable RLS
ALTER TABLE public.sites ENABLE ROW LEVEL SECURITY;

-- Policies for sites
CREATE POLICY "Users can view own sites"
  ON public.sites FOR SELECT
  USING (auth.uid() = user_id OR is_public = TRUE);

CREATE POLICY "Users can insert own sites"
  ON public.sites FOR INSERT
  WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can update own sites"
  ON public.sites FOR UPDATE
  USING (auth.uid() = user_id);

CREATE POLICY "Users can delete own sites"
  ON public.sites FOR DELETE
  USING (auth.uid() = user_id);

-- Events (pageviews and custom events)
CREATE TABLE IF NOT EXISTS public.events (
  id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  site_id UUID REFERENCES public.sites(id) ON DELETE CASCADE NOT NULL,
  event_name TEXT DEFAULT 'pageview' NOT NULL,
  pathname TEXT NOT NULL,
  referrer TEXT,
  referrer_source TEXT,
  country_code TEXT,
  device_type TEXT CHECK (device_type IN ('desktop', 'mobile', 'tablet')),
  browser TEXT,
  os TEXT,
  utm_source TEXT,
  utm_medium TEXT,
  utm_campaign TEXT,
  session_id TEXT,
  visitor_id TEXT,
  timestamp TIMESTAMPTZ DEFAULT NOW() NOT NULL
);

-- Enable RLS (events are inserted by service role, read by site owners)
ALTER TABLE public.events ENABLE ROW LEVEL SECURITY;

-- Policy for events - site owners can read their events
CREATE POLICY "Site owners can view events"
  ON public.events FOR SELECT
  USING (
    EXISTS (
      SELECT 1 FROM public.sites
      WHERE sites.id = events.site_id
      AND (sites.user_id = auth.uid() OR sites.is_public = TRUE)
    )
  );

-- Partitioning hint: For production, consider partitioning events by timestamp
-- CREATE TABLE public.events_2024_01 PARTITION OF public.events
--   FOR VALUES FROM ('2024-01-01') TO ('2024-02-01');

-- Indexes for common analytics queries
CREATE INDEX IF NOT EXISTS idx_events_site_timestamp ON public.events(site_id, timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_events_site_pathname ON public.events(site_id, pathname);
CREATE INDEX IF NOT EXISTS idx_events_site_referrer ON public.events(site_id, referrer_source) WHERE referrer_source IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_events_site_country ON public.events(site_id, country_code);

-- Aggregated daily stats (for faster dashboard queries)
CREATE TABLE IF NOT EXISTS public.daily_stats (
  id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  site_id UUID REFERENCES public.sites(id) ON DELETE CASCADE NOT NULL,
  date DATE NOT NULL,
  visitors INTEGER DEFAULT 0 NOT NULL,
  pageviews INTEGER DEFAULT 0 NOT NULL,
  sessions INTEGER DEFAULT 0 NOT NULL,
  bounce_rate DECIMAL(5,2),
  avg_duration_seconds INTEGER,
  created_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
  UNIQUE(site_id, date)
);

-- Enable RLS
ALTER TABLE public.daily_stats ENABLE ROW LEVEL SECURITY;

-- Policy for daily_stats
CREATE POLICY "Site owners can view daily stats"
  ON public.daily_stats FOR SELECT
  USING (
    EXISTS (
      SELECT 1 FROM public.sites
      WHERE sites.id = daily_stats.site_id
      AND (sites.user_id = auth.uid() OR sites.is_public = TRUE)
    )
  );

-- Index for date range queries
CREATE INDEX IF NOT EXISTS idx_daily_stats_site_date ON public.daily_stats(site_id, date DESC);

-- Function to generate public share slug
CREATE OR REPLACE FUNCTION public.generate_share_slug()
RETURNS TEXT AS $$
  SELECT encode(gen_random_bytes(8), 'hex');
$$ LANGUAGE SQL;

-- Trigger for sites updated_at
CREATE TRIGGER update_sites_updated_at
  BEFORE UPDATE ON public.sites
  FOR EACH ROW EXECUTE FUNCTION public.update_updated_at_column();
