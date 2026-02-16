-- Digital Download: Billing Schema
-- Tiered download access billing model with Stripe

-- Customers table (links workspaces to Stripe)
CREATE TABLE IF NOT EXISTS public.customers (
  id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  workspace_id UUID REFERENCES public.workspaces(id) ON DELETE CASCADE UNIQUE NOT NULL,
  stripe_customer_id TEXT UNIQUE,
  created_at TIMESTAMPTZ DEFAULT NOW() NOT NULL
);

-- Enable RLS
ALTER TABLE public.customers ENABLE ROW LEVEL SECURITY;

-- Subscriptions table with feature limits
CREATE TABLE IF NOT EXISTS public.subscriptions (
  id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  workspace_id UUID REFERENCES public.workspaces(id) ON DELETE CASCADE UNIQUE NOT NULL,
  stripe_subscription_id TEXT UNIQUE,
  stripe_customer_id TEXT,
  status TEXT DEFAULT 'active' CHECK (status IN (
    'active', 'canceled', 'incomplete', 'incomplete_expired',
    'past_due', 'trialing', 'unpaid'
  )) NOT NULL,
  price_id TEXT,
  -- Feature limits
  post_limit INTEGER DEFAULT 10,
  storage_limit_mb INTEGER DEFAULT 500,
  scheduled_limit INTEGER DEFAULT 5,
  member_limit INTEGER DEFAULT 1,
  -- Billing period
  current_period_start TIMESTAMPTZ,
  current_period_end TIMESTAMPTZ,
  cancel_at_period_end BOOLEAN DEFAULT FALSE,
  canceled_at TIMESTAMPTZ,
  created_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
  updated_at TIMESTAMPTZ DEFAULT NOW() NOT NULL
);

-- Enable RLS
ALTER TABLE public.subscriptions ENABLE ROW LEVEL SECURITY;

-- Feature usage tracking
CREATE TABLE IF NOT EXISTS public.feature_usage (
  id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  workspace_id UUID REFERENCES public.workspaces(id) ON DELETE CASCADE NOT NULL,
  feature TEXT NOT NULL,
  count INTEGER DEFAULT 0,
  period_start DATE NOT NULL,
  period_end DATE NOT NULL,
  created_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
  updated_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
  UNIQUE(workspace_id, feature, period_start)
);

-- Enable RLS
ALTER TABLE public.feature_usage ENABLE ROW LEVEL SECURITY;

-- Customers policies
CREATE POLICY "Workspace members can view customer"
  ON public.customers FOR SELECT
  USING (
    EXISTS (
      SELECT 1 FROM public.workspace_members
      WHERE workspace_members.workspace_id = customers.workspace_id
      AND workspace_members.user_id = auth.uid()
    )
  );

-- Subscriptions policies
CREATE POLICY "Workspace members can view subscription"
  ON public.subscriptions FOR SELECT
  USING (
    EXISTS (
      SELECT 1 FROM public.workspace_members
      WHERE workspace_members.workspace_id = subscriptions.workspace_id
      AND workspace_members.user_id = auth.uid()
    )
  );

-- Feature usage policies
CREATE POLICY "Workspace members can view usage"
  ON public.feature_usage FOR SELECT
  USING (
    EXISTS (
      SELECT 1 FROM public.workspace_members
      WHERE workspace_members.workspace_id = feature_usage.workspace_id
      AND workspace_members.user_id = auth.uid()
    )
  );

-- Function to check if workspace can use feature
CREATE OR REPLACE FUNCTION public.can_use_feature(
  p_workspace_id UUID,
  p_feature TEXT
)
RETURNS BOOLEAN AS $$
DECLARE
  v_limit INTEGER;
  v_current_count INTEGER;
BEGIN
  -- Get limit from subscription
  SELECT
    CASE p_feature
      WHEN 'posts' THEN COALESCE(post_limit, 10)
      WHEN 'scheduled' THEN COALESCE(scheduled_limit, 5)
      WHEN 'members' THEN COALESCE(member_limit, 1)
      ELSE 999999
    END INTO v_limit
  FROM public.subscriptions
  WHERE workspace_id = p_workspace_id AND status = 'active';

  -- Default limits if no subscription
  IF v_limit IS NULL THEN
    v_limit := CASE p_feature
      WHEN 'posts' THEN 10
      WHEN 'scheduled' THEN 5
      WHEN 'members' THEN 1
      ELSE 999999
    END;
  END IF;

  -- Get current count
  CASE p_feature
    WHEN 'posts' THEN
      SELECT COUNT(*) INTO v_current_count FROM public.posts WHERE workspace_id = p_workspace_id;
    WHEN 'scheduled' THEN
      SELECT COUNT(*) INTO v_current_count FROM public.posts WHERE workspace_id = p_workspace_id AND status = 'scheduled';
    WHEN 'members' THEN
      SELECT COUNT(*) INTO v_current_count FROM public.workspace_members WHERE workspace_id = p_workspace_id;
    ELSE
      v_current_count := 0;
  END CASE;

  RETURN v_current_count < v_limit;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Function to increment feature usage
CREATE OR REPLACE FUNCTION public.increment_feature_usage(
  p_workspace_id UUID,
  p_feature TEXT
)
RETURNS VOID AS $$
BEGIN
  INSERT INTO public.feature_usage (workspace_id, feature, count, period_start, period_end)
  VALUES (
    p_workspace_id,
    p_feature,
    1,
    DATE_TRUNC('month', CURRENT_DATE)::DATE,
    (DATE_TRUNC('month', CURRENT_DATE) + INTERVAL '1 month' - INTERVAL '1 day')::DATE
  )
  ON CONFLICT (workspace_id, feature, period_start)
  DO UPDATE SET
    count = feature_usage.count + 1,
    updated_at = NOW();
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Triggers
CREATE TRIGGER update_subscriptions_updated_at
  BEFORE UPDATE ON public.subscriptions
  FOR EACH ROW EXECUTE FUNCTION public.update_updated_at_column();

CREATE TRIGGER update_feature_usage_updated_at
  BEFORE UPDATE ON public.feature_usage
  FOR EACH ROW EXECUTE FUNCTION public.update_updated_at_column();

-- Indexes
CREATE INDEX IF NOT EXISTS idx_subscriptions_workspace_id ON public.subscriptions(workspace_id);
CREATE INDEX IF NOT EXISTS idx_subscriptions_status ON public.subscriptions(status);
CREATE INDEX IF NOT EXISTS idx_feature_usage_workspace_period ON public.feature_usage(workspace_id, period_start);
