-- Productivity Tool: Billing Enhancements
-- Adds trial support, dunning fields, and seat management improvements

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

-- Rename 'quantity' to be clearer about seat meaning
-- Note: We keep 'quantity' for Stripe compatibility but add alias view
COMMENT ON COLUMN public.subscriptions.quantity IS 'Number of paid seats (synced with Stripe quantity)';

-- Index for trial end date (for batch notifications)
CREATE INDEX IF NOT EXISTS idx_subscriptions_trial_end
  ON public.subscriptions(trial_end)
  WHERE trial_end IS NOT NULL;

-- Index for dunning (for finding past_due subscriptions)
CREATE INDEX IF NOT EXISTS idx_subscriptions_dunning
  ON public.subscriptions(dunning_started_at)
  WHERE dunning_started_at IS NOT NULL;

-- Update seat_usage table with more fields
ALTER TABLE public.seat_usage
ADD COLUMN IF NOT EXISTS seat_count INTEGER,
ADD COLUMN IF NOT EXISTS billable_seats INTEGER,
ADD COLUMN IF NOT EXISTS guest_seats INTEGER DEFAULT 0;

-- Backfill seat_count from recorded_seats if exists
UPDATE public.seat_usage
SET seat_count = recorded_seats
WHERE seat_count IS NULL AND recorded_seats IS NOT NULL;

-- Function to check if workspace is in trial
CREATE OR REPLACE FUNCTION public.is_workspace_in_trial(p_workspace_id UUID)
RETURNS BOOLEAN AS $$
  SELECT EXISTS (
    SELECT 1 FROM public.subscriptions
    WHERE workspace_id = p_workspace_id
      AND status = 'trialing'
      AND trial_end > NOW()
  );
$$ LANGUAGE SQL SECURITY DEFINER;

-- Function to get days remaining in trial
CREATE OR REPLACE FUNCTION public.get_workspace_trial_days_remaining(p_workspace_id UUID)
RETURNS INTEGER AS $$
  SELECT GREATEST(0, EXTRACT(DAY FROM (trial_end - NOW())))::INTEGER
  FROM public.subscriptions
  WHERE workspace_id = p_workspace_id
    AND status = 'trialing'
    AND trial_end > NOW()
  LIMIT 1;
$$ LANGUAGE SQL SECURITY DEFINER;

-- Function to check if workspace is in grace period
CREATE OR REPLACE FUNCTION public.is_workspace_in_grace_period(p_workspace_id UUID)
RETURNS BOOLEAN AS $$
  SELECT EXISTS (
    SELECT 1 FROM public.subscriptions
    WHERE workspace_id = p_workspace_id
      AND status = 'past_due'
      AND grace_period_until > NOW()
  );
$$ LANGUAGE SQL SECURITY DEFINER;

-- Function to get feature flags for workspace
CREATE OR REPLACE FUNCTION public.get_workspace_feature_flags(p_workspace_id UUID)
RETURNS JSONB AS $$
  SELECT COALESCE(feature_flags, '{}')
  FROM public.subscriptions
  WHERE workspace_id = p_workspace_id
    AND status IN ('active', 'trialing')
  ORDER BY created_at DESC
  LIMIT 1;
$$ LANGUAGE SQL SECURITY DEFINER;

-- Function to check if workspace has specific feature
CREATE OR REPLACE FUNCTION public.workspace_has_feature(p_workspace_id UUID, p_feature TEXT)
RETURNS BOOLEAN AS $$
  SELECT COALESCE(
    (feature_flags->>p_feature)::BOOLEAN,
    FALSE
  )
  FROM public.subscriptions
  WHERE workspace_id = p_workspace_id
    AND status IN ('active', 'trialing')
  ORDER BY created_at DESC
  LIMIT 1;
$$ LANGUAGE SQL SECURITY DEFINER;

-- Function to calculate proration preview for adding seats
CREATE OR REPLACE FUNCTION public.calculate_seat_proration_preview(
  p_workspace_id UUID,
  p_seats_to_add INTEGER
)
RETURNS TABLE(
  current_seats INTEGER,
  new_seats INTEGER,
  days_remaining INTEGER,
  estimated_proration_cents INTEGER
) AS $$
DECLARE
  v_subscription RECORD;
  v_days_in_period INTEGER;
  v_days_remaining INTEGER;
  v_daily_rate INTEGER;
BEGIN
  SELECT * INTO v_subscription
  FROM public.subscriptions
  WHERE workspace_id = p_workspace_id
    AND status IN ('active', 'trialing')
  LIMIT 1;

  IF v_subscription IS NULL THEN
    RETURN;
  END IF;

  -- Calculate days remaining in period
  v_days_in_period := EXTRACT(DAY FROM (v_subscription.current_period_end - v_subscription.current_period_start))::INTEGER;
  v_days_remaining := GREATEST(0, EXTRACT(DAY FROM (v_subscription.current_period_end - NOW())))::INTEGER;

  -- Estimate daily rate (assuming $12/seat/month = 1200 cents / 30 days = 40 cents/day)
  v_daily_rate := 40; -- This should be calculated from actual price

  RETURN QUERY SELECT
    v_subscription.quantity::INTEGER,
    (v_subscription.quantity + p_seats_to_add)::INTEGER,
    v_days_remaining,
    (p_seats_to_add * v_daily_rate * v_days_remaining)::INTEGER;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Updated function to check if workspace can add members (considers guests)
CREATE OR REPLACE FUNCTION public.can_add_workspace_member(p_workspace_id UUID, p_is_guest BOOLEAN DEFAULT FALSE)
RETURNS BOOLEAN AS $$
DECLARE
  v_current_billable INTEGER;
  v_allowed_seats INTEGER;
BEGIN
  -- Guests are always free
  IF p_is_guest THEN
    RETURN TRUE;
  END IF;

  -- Get current billable seat count (non-guests)
  SELECT COUNT(*)::INTEGER INTO v_current_billable
  FROM public.workspace_members
  WHERE workspace_id = p_workspace_id
    AND role NOT IN ('guest', 'viewer');

  -- Get allowed seats from active subscription
  SELECT COALESCE(quantity, 5) INTO v_allowed_seats
  FROM public.subscriptions
  WHERE workspace_id = p_workspace_id
    AND status IN ('active', 'trialing')
  ORDER BY created_at DESC
  LIMIT 1;

  -- If no subscription, default to 5 seats (trial)
  IF v_allowed_seats IS NULL THEN
    v_allowed_seats := 5;
  END IF;

  RETURN v_current_billable < v_allowed_seats;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;
