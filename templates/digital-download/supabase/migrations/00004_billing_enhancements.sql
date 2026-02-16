-- Content Creator: Billing Enhancements
-- Adds trial support, dunning fields, feature flags, and credit ledger

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

-- Credit ledger for one-time credit pack purchases
CREATE TABLE IF NOT EXISTS public.credit_ledger (
  id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  workspace_id UUID REFERENCES public.workspaces(id) ON DELETE CASCADE NOT NULL,
  amount INTEGER NOT NULL, -- positive = credit, negative = debit
  source TEXT NOT NULL CHECK (source IN (
    'subscription_included', 'top_up', 'usage', 'refund', 'bonus', 'expiry'
  )),
  description TEXT,
  stripe_invoice_id TEXT,
  stripe_payment_intent_id TEXT,
  expires_at TIMESTAMPTZ, -- for time-limited credits
  created_at TIMESTAMPTZ DEFAULT NOW() NOT NULL
);

-- Enable RLS on credit_ledger
ALTER TABLE public.credit_ledger ENABLE ROW LEVEL SECURITY;

-- Policy for credit_ledger
CREATE POLICY "Workspace members can view credit ledger"
  ON public.credit_ledger FOR SELECT
  USING (
    EXISTS (
      SELECT 1 FROM public.workspace_members
      WHERE workspace_members.workspace_id = credit_ledger.workspace_id
      AND workspace_members.user_id = auth.uid()
    )
  );

-- Index for credit balance calculations
CREATE INDEX IF NOT EXISTS idx_credit_ledger_workspace
  ON public.credit_ledger(workspace_id, created_at);

-- Function to get current credit balance for workspace
CREATE OR REPLACE FUNCTION public.get_credit_balance(p_workspace_id UUID)
RETURNS INTEGER AS $$
  SELECT COALESCE(SUM(amount), 0)::INTEGER
  FROM public.credit_ledger
  WHERE workspace_id = p_workspace_id
    AND (expires_at IS NULL OR expires_at > NOW());
$$ LANGUAGE SQL SECURITY DEFINER;

-- Function to deduct credits (returns success/failure)
CREATE OR REPLACE FUNCTION public.deduct_credits(
  p_workspace_id UUID,
  p_amount INTEGER,
  p_description TEXT DEFAULT 'Usage'
)
RETURNS BOOLEAN AS $$
DECLARE
  v_current_balance INTEGER;
BEGIN
  -- Get current balance
  SELECT public.get_credit_balance(p_workspace_id) INTO v_current_balance;

  -- Check if sufficient credits
  IF v_current_balance < p_amount THEN
    RETURN FALSE;
  END IF;

  -- Insert debit record
  INSERT INTO public.credit_ledger (workspace_id, amount, source, description)
  VALUES (p_workspace_id, -p_amount, 'usage', p_description);

  RETURN TRUE;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Function to add credits from top-up purchase
CREATE OR REPLACE FUNCTION public.add_credits_from_purchase(
  p_workspace_id UUID,
  p_amount INTEGER,
  p_stripe_payment_intent_id TEXT,
  p_description TEXT DEFAULT 'Credit pack purchase'
)
RETURNS UUID AS $$
DECLARE
  v_ledger_id UUID;
BEGIN
  INSERT INTO public.credit_ledger (
    workspace_id,
    amount,
    source,
    description,
    stripe_payment_intent_id
  )
  VALUES (
    p_workspace_id,
    p_amount,
    'top_up',
    p_description,
    p_stripe_payment_intent_id
  )
  RETURNING id INTO v_ledger_id;

  RETURN v_ledger_id;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Function to add monthly subscription credits
CREATE OR REPLACE FUNCTION public.add_subscription_credits(
  p_workspace_id UUID,
  p_amount INTEGER,
  p_description TEXT DEFAULT 'Monthly subscription credits'
)
RETURNS UUID AS $$
DECLARE
  v_ledger_id UUID;
BEGIN
  INSERT INTO public.credit_ledger (
    workspace_id,
    amount,
    source,
    description,
    expires_at
  )
  VALUES (
    p_workspace_id,
    p_amount,
    'subscription_included',
    p_description,
    NOW() + INTERVAL '35 days' -- Expires slightly after month end
  )
  RETURNING id INTO v_ledger_id;

  RETURN v_ledger_id;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

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

-- View for credit balance summary
CREATE OR REPLACE VIEW public.credit_balance_summary AS
SELECT
  workspace_id,
  SUM(CASE WHEN amount > 0 THEN amount ELSE 0 END) AS total_credits_earned,
  SUM(CASE WHEN amount < 0 THEN ABS(amount) ELSE 0 END) AS total_credits_used,
  SUM(amount) AS current_balance,
  SUM(CASE
    WHEN amount > 0 AND source = 'subscription_included' THEN amount
    ELSE 0
  END) AS subscription_credits,
  SUM(CASE
    WHEN amount > 0 AND source = 'top_up' THEN amount
    ELSE 0
  END) AS purchased_credits
FROM public.credit_ledger
WHERE expires_at IS NULL OR expires_at > NOW()
GROUP BY workspace_id;
