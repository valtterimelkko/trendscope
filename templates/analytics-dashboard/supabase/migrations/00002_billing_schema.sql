-- Analytics Dashboard: Billing Schema
-- Creates Stripe customer mapping, subscriptions, and usage tracking

-- Stripe customer mapping
CREATE TABLE IF NOT EXISTS public.customers (
  id UUID REFERENCES public.profiles(id) ON DELETE CASCADE PRIMARY KEY,
  stripe_customer_id TEXT UNIQUE,
  created_at TIMESTAMPTZ DEFAULT NOW() NOT NULL
);

-- Enable RLS
ALTER TABLE public.customers ENABLE ROW LEVEL SECURITY;

-- Policies for customers
CREATE POLICY "Users can view own customer record"
  ON public.customers FOR SELECT
  USING (auth.uid() = id);

CREATE POLICY "Users can insert own customer record"
  ON public.customers FOR INSERT
  WITH CHECK (auth.uid() = id);

-- Subscriptions
CREATE TABLE IF NOT EXISTS public.subscriptions (
  id TEXT PRIMARY KEY, -- Stripe subscription ID
  user_id UUID REFERENCES public.profiles(id) ON DELETE CASCADE NOT NULL,
  status TEXT NOT NULL CHECK (status IN (
    'trialing', 'active', 'canceled', 'incomplete',
    'incomplete_expired', 'past_due', 'unpaid', 'paused'
  )),
  price_id TEXT,
  quantity INTEGER DEFAULT 1,
  cancel_at_period_end BOOLEAN DEFAULT FALSE,
  current_period_start TIMESTAMPTZ,
  current_period_end TIMESTAMPTZ,
  created_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
  updated_at TIMESTAMPTZ DEFAULT NOW() NOT NULL
);

-- Enable RLS
ALTER TABLE public.subscriptions ENABLE ROW LEVEL SECURITY;

-- Policies for subscriptions
CREATE POLICY "Users can view own subscriptions"
  ON public.subscriptions FOR SELECT
  USING (auth.uid() = user_id);

-- Index for faster subscription lookups
CREATE INDEX IF NOT EXISTS idx_subscriptions_user_id ON public.subscriptions(user_id);
CREATE INDEX IF NOT EXISTS idx_subscriptions_status ON public.subscriptions(status);

-- Usage tracking (for metered/usage-based billing)
CREATE TABLE IF NOT EXISTS public.usage (
  id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  user_id UUID REFERENCES public.profiles(id) ON DELETE CASCADE NOT NULL,
  team_id UUID REFERENCES public.teams(id) ON DELETE CASCADE,
  metric TEXT NOT NULL, -- e.g., 'events', 'pageviews', 'api_calls'
  quantity INTEGER DEFAULT 1 NOT NULL,
  recorded_at TIMESTAMPTZ DEFAULT NOW() NOT NULL
);

-- Enable RLS
ALTER TABLE public.usage ENABLE ROW LEVEL SECURITY;

-- Policies for usage
CREATE POLICY "Users can view own usage"
  ON public.usage FOR SELECT
  USING (auth.uid() = user_id);

CREATE POLICY "Users can insert own usage"
  ON public.usage FOR INSERT
  WITH CHECK (auth.uid() = user_id);

-- Index for faster usage aggregation
CREATE INDEX IF NOT EXISTS idx_usage_user_metric ON public.usage(user_id, metric, recorded_at);

-- Monthly usage aggregation view
CREATE OR REPLACE VIEW public.monthly_usage AS
SELECT
  user_id,
  metric,
  date_trunc('month', recorded_at) AS month,
  SUM(quantity) AS total_quantity
FROM public.usage
GROUP BY user_id, metric, date_trunc('month', recorded_at);

-- Function to get current month usage for a user
CREATE OR REPLACE FUNCTION public.get_current_month_usage(p_user_id UUID, p_metric TEXT)
RETURNS INTEGER AS $$
  SELECT COALESCE(SUM(quantity), 0)::INTEGER
  FROM public.usage
  WHERE user_id = p_user_id
    AND metric = p_metric
    AND recorded_at >= date_trunc('month', NOW())
    AND recorded_at < date_trunc('month', NOW()) + INTERVAL '1 month';
$$ LANGUAGE SQL SECURITY DEFINER;

-- Trigger for subscriptions updated_at
CREATE TRIGGER update_subscriptions_updated_at
  BEFORE UPDATE ON public.subscriptions
  FOR EACH ROW EXECUTE FUNCTION public.update_updated_at_column();
