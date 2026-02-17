-- Security Fix: Enable RLS on system_config table
-- Version: 1.0.1
-- Description: Add RLS policy to system_config table (missed in initial schema)
-- Date: 2026-02-17

BEGIN;

-- Enable RLS on system_config
ALTER TABLE public.system_config ENABLE ROW LEVEL SECURITY;

-- Allow authenticated users to read system config (for app settings)
CREATE POLICY "Authenticated users can view system config"
    ON public.system_config FOR SELECT
    TO authenticated
    USING (true);

-- Note: Write operations (INSERT/UPDATE/DELETE) are restricted to service role only
-- No user-facing policies for writes are needed

COMMIT;
