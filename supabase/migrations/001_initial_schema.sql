-- Trendscope Database Schema
-- Version: 1.0.0
-- Description: Initial schema for TikTok Trend Intelligence Platform

BEGIN;

-- ============================================
-- EXTENSIONS
-- ============================================
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ============================================
-- CORE TABLES
-- ============================================

-- Users and Profiles (extends Supabase Auth)
CREATE TABLE IF NOT EXISTS public.profiles (
    id UUID PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
    email TEXT NOT NULL,
    full_name TEXT,
    avatar_url TEXT,
    tier TEXT NOT NULL DEFAULT 'free' CHECK (tier IN ('free', 'solo', 'agency', 'enterprise')),
    status TEXT NOT NULL DEFAULT 'active' CHECK (status IN ('active', 'paused', 'cancelled')),
    stripe_customer_id TEXT,
    stripe_subscription_id TEXT,
    email_notifications BOOLEAN DEFAULT true,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Available Niches
CREATE TABLE IF NOT EXISTS public.niches (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name TEXT NOT NULL UNIQUE,
    display_name TEXT NOT NULL,
    description TEXT,
    hashtag_count INTEGER DEFAULT 0,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- User Niche Preferences
CREATE TABLE IF NOT EXISTS public.user_niches (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES public.profiles(id) ON DELETE CASCADE,
    niche_id UUID NOT NULL REFERENCES public.niches(id) ON DELETE CASCADE,
    alert_enabled BOOLEAN DEFAULT true,
    velocity_threshold INTEGER DEFAULT 50 CHECK (velocity_threshold >= 0 AND velocity_threshold <= 100),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(user_id, niche_id)
);

-- Alert Integrations (Slack, Webhook)
CREATE TABLE IF NOT EXISTS public.alert_integrations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES public.profiles(id) ON DELETE CASCADE,
    type TEXT NOT NULL CHECK (type IN ('slack', 'webhook', 'discord')),
    name TEXT NOT NULL,
    config JSONB NOT NULL DEFAULT '{}',
    is_active BOOLEAN DEFAULT true,
    last_tested_at TIMESTAMPTZ,
    last_test_status TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Detected Trends
CREATE TABLE IF NOT EXISTS public.trends (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    type TEXT NOT NULL CHECK (type IN ('sound', 'hashtag', 'format')),
    name TEXT NOT NULL,
    platform_id TEXT NOT NULL,
    niche_id UUID REFERENCES public.niches(id),
    first_detected_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    peak_detected_at TIMESTAMPTZ,
    status TEXT NOT NULL DEFAULT 'emerging' CHECK (status IN ('emerging', 'peaking', 'saturated', 'expired')),
    velocity_score INTEGER CHECK (velocity_score >= 0 AND velocity_score <= 100),
    saturation_percent INTEGER CHECK (saturation_percent >= 0 AND saturation_percent <= 100),
    video_count_start INTEGER,
    video_count_current INTEGER,
    growth_rate DECIMAL(5,2),
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(type, platform_id)
);

-- Trend Velocity History (time-series data)
CREATE TABLE IF NOT EXISTS public.trend_velocity_history (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    trend_id UUID NOT NULL REFERENCES public.trends(id) ON DELETE CASCADE,
    timestamp TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    video_count INTEGER NOT NULL,
    velocity_score INTEGER,
    growth_rate DECIMAL(5,2),
    saturation_percent INTEGER
);

-- User Alerts
CREATE TABLE IF NOT EXISTS public.alerts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES public.profiles(id) ON DELETE CASCADE,
    trend_id UUID NOT NULL REFERENCES public.trends(id) ON DELETE CASCADE,
    channel TEXT NOT NULL CHECK (channel IN ('email', 'slack', 'webhook')),
    status TEXT NOT NULL DEFAULT 'pending' CHECK (status IN ('pending', 'sent', 'delivered', 'failed')),
    sent_at TIMESTAMPTZ,
    opened_at TIMESTAMPTZ,
    clicked_at TIMESTAMPTZ,
    dismissed BOOLEAN DEFAULT false,
    confidence_score DECIMAL(3,2),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- User Bookmarks
CREATE TABLE IF NOT EXISTS public.bookmarks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES public.profiles(id) ON DELETE CASCADE,
    trend_id UUID NOT NULL REFERENCES public.trends(id) ON DELETE CASCADE,
    notes TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(user_id, trend_id)
);

-- Agency Client Workspaces
CREATE TABLE IF NOT EXISTS public.clients (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    agency_id UUID NOT NULL REFERENCES public.profiles(id) ON DELETE CASCADE,
    name TEXT NOT NULL,
    logo_url TEXT,
    config JSONB DEFAULT '{}',
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Client Alert Configurations
CREATE TABLE IF NOT EXISTS public.client_alerts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    client_id UUID NOT NULL REFERENCES public.clients(id) ON DELETE CASCADE,
    integration_id UUID NOT NULL REFERENCES public.alert_integrations(id) ON DELETE CASCADE,
    niche_filter JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- System Configuration
CREATE TABLE IF NOT EXISTS public.system_config (
    key TEXT PRIMARY KEY,
    value JSONB NOT NULL,
    description TEXT,
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- ============================================
-- INDEXES
-- ============================================

-- Performance indexes
CREATE INDEX IF NOT EXISTS idx_profiles_tier ON public.profiles(tier);
CREATE INDEX IF NOT EXISTS idx_profiles_stripe_customer ON public.profiles(stripe_customer_id);

CREATE INDEX IF NOT EXISTS idx_user_niches_user_id ON public.user_niches(user_id);
CREATE INDEX IF NOT EXISTS idx_user_niches_niche_id ON public.user_niches(niche_id);

CREATE INDEX IF NOT EXISTS idx_trends_type ON public.trends(type);
CREATE INDEX IF NOT EXISTS idx_trends_status ON public.trends(status);
CREATE INDEX IF NOT EXISTS idx_trends_niche ON public.trends(niche_id);
CREATE INDEX IF NOT EXISTS idx_trends_velocity ON public.trends(velocity_score DESC);
CREATE INDEX IF NOT EXISTS idx_trends_detected ON public.trends(first_detected_at DESC);

CREATE INDEX IF NOT EXISTS idx_trend_velocity_history_trend ON public.trend_velocity_history(trend_id);
CREATE INDEX IF NOT EXISTS idx_trend_velocity_history_timestamp ON public.trend_velocity_history(timestamp DESC);

CREATE INDEX IF NOT EXISTS idx_alerts_user_id ON public.alerts(user_id);
CREATE INDEX IF NOT EXISTS idx_alerts_trend_id ON public.alerts(trend_id);
CREATE INDEX IF NOT EXISTS idx_alerts_status ON public.alerts(status);
CREATE INDEX IF NOT EXISTS idx_alerts_created ON public.alerts(created_at DESC);

CREATE INDEX IF NOT EXISTS idx_alert_integrations_user ON public.alert_integrations(user_id);

CREATE INDEX IF NOT EXISTS idx_clients_agency ON public.clients(agency_id);

-- ============================================
-- ROW LEVEL SECURITY
-- ============================================

-- Enable RLS on all tables
ALTER TABLE public.profiles ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.user_niches ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.alert_integrations ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.alerts ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.bookmarks ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.clients ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.client_alerts ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.trends ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.niches ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.trend_velocity_history ENABLE ROW LEVEL SECURITY;

-- Profiles: Users can only see/edit own profile
CREATE POLICY "Users can view own profile"
    ON public.profiles FOR SELECT
    USING (auth.uid() = id);

CREATE POLICY "Users can update own profile"
    ON public.profiles FOR UPDATE
    USING (auth.uid() = id);

-- User Niches: Users can only see/edit own niche preferences
CREATE POLICY "Users can view own niches"
    ON public.user_niches FOR SELECT
    USING (auth.uid() = user_id);

CREATE POLICY "Users can manage own niches"
    ON public.user_niches FOR ALL
    USING (auth.uid() = user_id);

-- Alert Integrations: Users can only see/edit own integrations
CREATE POLICY "Users can view own integrations"
    ON public.alert_integrations FOR SELECT
    USING (auth.uid() = user_id);

CREATE POLICY "Users can manage own integrations"
    ON public.alert_integrations FOR ALL
    USING (auth.uid() = user_id);

-- Alerts: Users can only see own alerts
CREATE POLICY "Users can view own alerts"
    ON public.alerts FOR SELECT
    USING (auth.uid() = user_id);

-- Bookmarks: Users can only see/manage own bookmarks
CREATE POLICY "Users can view own bookmarks"
    ON public.bookmarks FOR SELECT
    USING (auth.uid() = user_id);

CREATE POLICY "Users can manage own bookmarks"
    ON public.bookmarks FOR ALL
    USING (auth.uid() = user_id);

-- Clients: Agency users can only see own clients
CREATE POLICY "Agencies can view own clients"
    ON public.clients FOR SELECT
    USING (auth.uid() = agency_id);

CREATE POLICY "Agencies can manage own clients"
    ON public.clients FOR ALL
    USING (auth.uid() = agency_id);

-- Client Alerts: Agencies can only see own client alerts
CREATE POLICY "Agencies can view own client alerts"
    ON public.client_alerts FOR SELECT
    USING (
        EXISTS (
            SELECT 1 FROM public.clients c
            WHERE c.id = client_alerts.client_id
            AND c.agency_id = auth.uid()
        )
    );

-- Trends: All authenticated users can read
CREATE POLICY "Authenticated users can view trends"
    ON public.trends FOR SELECT
    TO authenticated
    USING (true);

-- Niches: All authenticated users can read
CREATE POLICY "Authenticated users can view niches"
    ON public.niches FOR SELECT
    TO authenticated
    USING (true);

-- Trend Velocity History: All authenticated users can read
CREATE POLICY "Authenticated users can view velocity history"
    ON public.trend_velocity_history FOR SELECT
    TO authenticated
    USING (true);

-- ============================================
-- TRIGGERS
-- ============================================

-- Auto-update updated_at timestamp
CREATE OR REPLACE FUNCTION public.handle_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER profiles_updated_at
    BEFORE UPDATE ON public.profiles
    FOR EACH ROW EXECUTE FUNCTION public.handle_updated_at();

CREATE TRIGGER alert_integrations_updated_at
    BEFORE UPDATE ON public.alert_integrations
    FOR EACH ROW EXECUTE FUNCTION public.handle_updated_at();

CREATE TRIGGER trends_updated_at
    BEFORE UPDATE ON public.trends
    FOR EACH ROW EXECUTE FUNCTION public.handle_updated_at();

CREATE TRIGGER clients_updated_at
    BEFORE UPDATE ON public.clients
    FOR EACH ROW EXECUTE FUNCTION public.handle_updated_at();

-- Profile creation on auth signup
CREATE OR REPLACE FUNCTION public.handle_new_user()
RETURNS TRIGGER AS $$
BEGIN
    INSERT INTO public.profiles (id, email, full_name, avatar_url)
    VALUES (
        NEW.id,
        NEW.email,
        NEW.raw_user_meta_data->>'full_name',
        NEW.raw_user_meta_data->>'avatar_url'
    );
    RETURN NEW;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER SET search_path = 'public';

-- Drop existing trigger if exists, then create
DROP TRIGGER IF EXISTS on_auth_user_created ON auth.users;
CREATE TRIGGER on_auth_user_created
    AFTER INSERT ON auth.users
    FOR EACH ROW EXECUTE FUNCTION public.handle_new_user();

-- ============================================
-- SEED DATA: NICHES
-- ============================================

INSERT INTO public.niches (name, display_name, description, is_active) VALUES
('beauty', 'Beauty & Skincare', 'Makeup tutorials, skincare routines, beauty hacks', true),
('fitness', 'Fitness & Health', 'Workouts, nutrition, wellness tips', true),
('finance', 'Finance & Business', 'Money tips, investing, entrepreneurship', true),
('gaming', 'Gaming', 'Gameplay, tips, gaming culture', true),
('cooking', 'Food & Cooking', 'Recipes, cooking tips, food trends', true),
('fashion', 'Fashion & Style', 'Outfits, style tips, fashion hauls', true),
('comedy', 'Comedy & Entertainment', 'Funny videos, skits, memes', true),
('music', 'Music & Dance', 'Music trends, dance challenges, artist content', true),
('tech', 'Technology', 'Tech reviews, gadgets, digital trends', true),
('travel', 'Travel & Adventure', 'Travel vlogs, destinations, adventure content', true),
('education', 'Education & Learning', 'Tutorials, how-to content, educational', true),
('lifestyle', 'Lifestyle', 'Daily life, routines, personal content', true),
('pets', 'Pets & Animals', 'Pet videos, animal content', true),
('diy', 'DIY & Crafts', 'Do-it-yourself projects, crafts, tutorials', true),
('parenting', 'Parenting & Family', 'Family content, parenting tips', true),
('sports', 'Sports', 'Sports highlights, athlete content', true),
('art', 'Art & Creativity', 'Art tutorials, creative content', true),
('relationships', 'Relationships & Dating', 'Dating advice, relationship content', true),
('motivation', 'Motivation & Self-Improvement', 'Inspirational content, personal growth', true),
('news', 'News & Current Events', 'News commentary, trending topics', true)
ON CONFLICT (name) DO NOTHING;

COMMIT;
