-- Security Fix: Update RLS policies to use authenticated role
-- Version: 1.0.2
-- Description: Fix policies that incorrectly apply to PUBLIC role
-- Date: 2026-02-17

BEGIN;

-- ============================================
-- FIX 1: Update profiles policies to use authenticated role
-- ============================================

-- Drop existing policies
DROP POLICY IF EXISTS "Users can view own profile" ON public.profiles;
DROP POLICY IF EXISTS "Users can update own profile" ON public.profiles;

-- Recreate with explicit TO authenticated
CREATE POLICY "Users can view own profile"
    ON public.profiles FOR SELECT
    TO authenticated
    USING (auth.uid() = id);

CREATE POLICY "Users can update own profile"
    ON public.profiles FOR UPDATE
    TO authenticated
    USING (auth.uid() = id);

-- Add INSERT policy for service_role (admin operations)
CREATE POLICY "Service role can insert profiles"
    ON public.profiles FOR INSERT
    TO service_role
    WITH CHECK (true);

-- ============================================
-- FIX 2: Update user_niches policies
-- ============================================

DROP POLICY IF EXISTS "Users can view own niches" ON public.user_niches;
DROP POLICY IF EXISTS "Users can manage own niches" ON public.user_niches;

CREATE POLICY "Users can view own niches"
    ON public.user_niches FOR SELECT
    TO authenticated
    USING (auth.uid() = user_id);

CREATE POLICY "Users can manage own niches"
    ON public.user_niches FOR ALL
    TO authenticated
    USING (auth.uid() = user_id);

-- ============================================
-- FIX 3: Update alert_integrations policies
-- ============================================

DROP POLICY IF EXISTS "Users can view own integrations" ON public.alert_integrations;
DROP POLICY IF EXISTS "Users can manage own integrations" ON public.alert_integrations;

CREATE POLICY "Users can view own integrations"
    ON public.alert_integrations FOR SELECT
    TO authenticated
    USING (auth.uid() = user_id);

CREATE POLICY "Users can manage own integrations"
    ON public.alert_integrations FOR ALL
    TO authenticated
    USING (auth.uid() = user_id);

-- ============================================
-- FIX 4: Update alerts policies (add missing operations)
-- ============================================

DROP POLICY IF EXISTS "Users can view own alerts" ON public.alerts;

CREATE POLICY "Users can view own alerts"
    ON public.alerts FOR SELECT
    TO authenticated
    USING (auth.uid() = user_id);

-- Add service_role policy for server-side alert management
CREATE POLICY "Service role can manage alerts"
    ON public.alerts FOR ALL
    TO service_role
    USING (true)
    WITH CHECK (true);

-- ============================================
-- FIX 5: Update bookmarks policies
-- ============================================

DROP POLICY IF EXISTS "Users can view own bookmarks" ON public.bookmarks;
DROP POLICY IF EXISTS "Users can manage own bookmarks" ON public.bookmarks;

CREATE POLICY "Users can view own bookmarks"
    ON public.bookmarks FOR SELECT
    TO authenticated
    USING (auth.uid() = user_id);

CREATE POLICY "Users can manage own bookmarks"
    ON public.bookmarks FOR ALL
    TO authenticated
    USING (auth.uid() = user_id);

-- ============================================
-- FIX 6: Update clients policies
-- ============================================

DROP POLICY IF EXISTS "Agencies can view own clients" ON public.clients;
DROP POLICY IF EXISTS "Agencies can manage own clients" ON public.clients;

CREATE POLICY "Agencies can view own clients"
    ON public.clients FOR SELECT
    TO authenticated
    USING (auth.uid() = agency_id);

CREATE POLICY "Agencies can manage own clients"
    ON public.clients FOR ALL
    TO authenticated
    USING (auth.uid() = agency_id);

-- ============================================
-- FIX 7: Update client_alerts policies (add missing operations)
-- ============================================

DROP POLICY IF EXISTS "Agencies can view own client alerts" ON public.client_alerts;

CREATE POLICY "Agencies can view own client alerts"
    ON public.client_alerts FOR SELECT
    TO authenticated
    USING (
        EXISTS (
            SELECT 1 FROM public.clients c
            WHERE c.id = client_alerts.client_id
            AND c.agency_id = auth.uid()
        )
    );

-- Add service_role policy for server-side client alert management
CREATE POLICY "Service role can manage client alerts"
    ON public.client_alerts FOR ALL
    TO service_role
    USING (true)
    WITH CHECK (true);

-- ============================================
-- DOCUMENTATION: Add comments to policies
-- ============================================

COMMENT ON POLICY "Users can view own profile" ON public.profiles IS 
'Allows authenticated users to view only their own profile. Restricted to authenticated role.';

COMMENT ON POLICY "Users can update own profile" ON public.profiles IS 
'Allows authenticated users to update only their own profile. Restricted to authenticated role.';

COMMENT ON POLICY "Service role can manage alerts" ON public.alerts IS 
'Allows service_role (server-side operations) to manage all alerts for background job processing.';

COMMENT ON POLICY "Service role can manage client alerts" ON public.client_alerts IS 
'Allows service_role (server-side operations) to manage all client alerts for background job processing.';

COMMIT;
