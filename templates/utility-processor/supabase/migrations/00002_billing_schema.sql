-- Utility Processor: Billing Schema
-- Creates Stripe customer mapping and usage/credit subscriptions

-- Stripe customer mapping (per workspace)
CREATE TABLE IF NOT EXISTS public.customers (
  workspace_id UUID REFERENCES public.workspaces(id) ON DELETE CASCADE PRIMARY KEY,
  stripe_customer_id TEXT UNIQUE,
  created_at TIMESTAMPTZ DEFAULT NOW() NOT NULL
);

-- Enable RLS
ALTER TABLE public.customers ENABLE ROW LEVEL SECURITY;

-- Policies for customers
CREATE POLICY "Workspace admins can view customer record"
  ON public.customers FOR SELECT
  USING (
    EXISTS (
      SELECT 1 FROM public.workspace_members
      WHERE workspace_members.workspace_id = customers.workspace_id
      AND workspace_members.user_id = auth.uid()
      AND workspace_members.role IN ('owner', 'admin')
    )
  );

-- Subscriptions (per workspace, seat-based)
CREATE TABLE IF NOT EXISTS public.subscriptions (
  id TEXT PRIMARY KEY, -- Stripe subscription ID
  workspace_id UUID REFERENCES public.workspaces(id) ON DELETE CASCADE NOT NULL,
  status TEXT NOT NULL CHECK (status IN (
    'trialing', 'active', 'canceled', 'incomplete',
    'incomplete_expired', 'past_due', 'unpaid', 'paused'
  )),
  price_id TEXT,
  quantity INTEGER DEFAULT 1, -- Number of seats
  cancel_at_period_end BOOLEAN DEFAULT FALSE,
  current_period_start TIMESTAMPTZ,
  current_period_end TIMESTAMPTZ,
  created_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
  updated_at TIMESTAMPTZ DEFAULT NOW() NOT NULL
);

-- Enable RLS
ALTER TABLE public.subscriptions ENABLE ROW LEVEL SECURITY;

-- Policies for subscriptions
CREATE POLICY "Workspace members can view subscriptions"
  ON public.subscriptions FOR SELECT
  USING (
    EXISTS (
      SELECT 1 FROM public.workspace_members
      WHERE workspace_members.workspace_id = subscriptions.workspace_id
      AND workspace_members.user_id = auth.uid()
    )
  );

-- Indexes
CREATE INDEX IF NOT EXISTS idx_subscriptions_workspace_id ON public.subscriptions(workspace_id);
CREATE INDEX IF NOT EXISTS idx_subscriptions_status ON public.subscriptions(status);

-- Seat usage tracking (for overage alerts)
CREATE TABLE IF NOT EXISTS public.seat_usage (
  id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  workspace_id UUID REFERENCES public.workspaces(id) ON DELETE CASCADE NOT NULL,
  recorded_seats INTEGER NOT NULL,
  allowed_seats INTEGER NOT NULL,
  recorded_at TIMESTAMPTZ DEFAULT NOW() NOT NULL
);

-- Enable RLS
ALTER TABLE public.seat_usage ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Workspace admins can view seat usage"
  ON public.seat_usage FOR SELECT
  USING (
    EXISTS (
      SELECT 1 FROM public.workspace_members
      WHERE workspace_members.workspace_id = seat_usage.workspace_id
      AND workspace_members.user_id = auth.uid()
      AND workspace_members.role IN ('owner', 'admin')
    )
  );

-- Function to check if workspace can add more members
CREATE OR REPLACE FUNCTION public.can_add_workspace_member(p_workspace_id UUID)
RETURNS BOOLEAN AS $$
DECLARE
  v_current_seats INTEGER;
  v_allowed_seats INTEGER;
BEGIN
  -- Get current seat count
  SELECT COUNT(*)::INTEGER INTO v_current_seats
  FROM public.workspace_members
  WHERE workspace_id = p_workspace_id
    AND role != 'guest';

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

  RETURN v_current_seats < v_allowed_seats;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Trigger for subscriptions updated_at
CREATE TRIGGER update_subscriptions_updated_at
  BEFORE UPDATE ON public.subscriptions
  FOR EACH ROW EXECUTE FUNCTION public.update_updated_at_column();
