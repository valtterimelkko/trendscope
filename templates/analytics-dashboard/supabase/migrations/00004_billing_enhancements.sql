-- Analytics Dashboard: Billing Enhancements
-- Adds trial support, dunning fields, and feature flags

-- Add trial and dunning columns to subscriptions table
ALTER TABLE public.subscriptions
ADD COLUMN IF NOT EXISTS trial_start TIMESTAMPTZ,
ADD COLUMN IF NOT EXISTS trial_end TIMESTAMPTZ,
ADD COLUMN IF NOT EXISTS is_reverse_trial BOOLEAN DEFAULT FALSE,
ADD COLUMN IF NOT EXISTS grace_period_until TIMESTAMPTZ,
ADD COLUMN IF NOT EXISTS dunning_started_at TIMESTAMPTZ,
ADD COLUMN IF NOT EXISTS dunning_emails_sent INTEGER DEFAULT 0,
ADD COLUMN IF NOT EXISTS feature_flags JSONB DEFAULT '{}',
ADD COLUMN IF NOT EXISTS plan_tier TEXT DEFAULT 'starter';

-- Index for trial end date (for batch notifications)
CREATE INDEX IF NOT EXISTS idx_subscriptions_trial_end
  ON public.subscriptions(trial_end)
  WHERE trial_end IS NOT NULL;

-- Index for dunning (for finding past_due subscriptions)
CREATE INDEX IF NOT EXISTS idx_subscriptions_dunning
  ON public.subscriptions(dunning_started_at)
  WHERE dunning_started_at IS NOT NULL;

-- Function to check if user is in trial
CREATE OR REPLACE FUNCTION public.is_in_trial(p_user_id UUID)
RETURNS BOOLEAN AS $$
  SELECT EXISTS (
    SELECT 1 FROM public.subscriptions
    WHERE user_id = p_user_id
      AND status = 'trialing'
      AND trial_end > NOW()
  );
$$ LANGUAGE SQL SECURITY DEFINER;

-- Function to get days remaining in trial
CREATE OR REPLACE FUNCTION public.get_trial_days_remaining(p_user_id UUID)
RETURNS INTEGER AS $$
  SELECT GREATEST(0, EXTRACT(DAY FROM (trial_end - NOW())))::INTEGER
  FROM public.subscriptions
  WHERE user_id = p_user_id
    AND status = 'trialing'
    AND trial_end > NOW()
  LIMIT 1;
$$ LANGUAGE SQL SECURITY DEFINER;

-- Function to check if user is in grace period
CREATE OR REPLACE FUNCTION public.is_in_grace_period(p_user_id UUID)
RETURNS BOOLEAN AS $$
  SELECT EXISTS (
    SELECT 1 FROM public.subscriptions
    WHERE user_id = p_user_id
      AND status = 'past_due'
      AND grace_period_until > NOW()
  );
$$ LANGUAGE SQL SECURITY DEFINER;

-- Function to get feature flags for user
CREATE OR REPLACE FUNCTION public.get_feature_flags(p_user_id UUID)
RETURNS JSONB AS $$
  SELECT COALESCE(feature_flags, '{}')
  FROM public.subscriptions
  WHERE user_id = p_user_id
    AND status IN ('active', 'trialing')
  ORDER BY created_at DESC
  LIMIT 1;
$$ LANGUAGE SQL SECURITY DEFINER;

-- Function to check if user has specific feature
CREATE OR REPLACE FUNCTION public.has_feature(p_user_id UUID, p_feature TEXT)
RETURNS BOOLEAN AS $$
  SELECT COALESCE(
    (feature_flags->>p_feature)::BOOLEAN,
    FALSE
  )
  FROM public.subscriptions
  WHERE user_id = p_user_id
    AND status IN ('active', 'trialing')
  ORDER BY created_at DESC
  LIMIT 1;
$$ LANGUAGE SQL SECURITY DEFINER;

-- Add upcoming invoice cache table for usage-based preview
CREATE TABLE IF NOT EXISTS public.upcoming_invoices (
  id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  user_id UUID REFERENCES public.profiles(id) ON DELETE CASCADE NOT NULL,
  stripe_customer_id TEXT NOT NULL,
  amount_due INTEGER NOT NULL, -- in cents
  currency TEXT DEFAULT 'usd',
  period_start TIMESTAMPTZ,
  period_end TIMESTAMPTZ,
  cached_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
  UNIQUE(user_id)
);

-- Enable RLS on upcoming_invoices
ALTER TABLE public.upcoming_invoices ENABLE ROW LEVEL SECURITY;

-- Policy for upcoming_invoices
CREATE POLICY "Users can view own upcoming invoice"
  ON public.upcoming_invoices FOR SELECT
  USING (auth.uid() = user_id);

-- Index for cache cleanup
CREATE INDEX IF NOT EXISTS idx_upcoming_invoices_cached_at
  ON public.upcoming_invoices(cached_at);
