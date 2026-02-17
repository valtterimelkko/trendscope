---
name: supabase-deployer
description: Use when deploying database schema and RLS policies from a template to the user's Supabase project. Runs migrations, configures auth providers, and verifies the deployment.
---

# Supabase Deployer

## Overview

Deploy the template's database schema, Row Level Security (RLS) policies, and auth configuration to the user's Supabase project. This transforms an empty Supabase project into a fully configured backend for the MVP.

**Core principle:** Templates define the schema. This skill deploys it. The user should go from empty Supabase project to fully configured backend with one skill execution.

## When to Use

- After template personalization is complete (Phase 4.3.4)
- When Supabase credentials are configured
- Can run in parallel with `stripe-deployer`

## Pre-Requisites

**Environment variables required:**
```bash
# Verify Supabase credentials exist
echo $SUPABASE_ACCESS_TOKEN | head -c 10
echo $SUPABASE_PROJECT_REF
```
If `docs/supabase-project.json` exists, read `project_ref` and `supabase_url` from it and export `SUPABASE_PROJECT_REF`/`SUPABASE_URL` before running commands.

**Supabase CLI should be available:**
```bash
# Check if Supabase CLI is installed
which supabase || npx supabase --version
```

**Template migrations must exist:**
```bash
ls templates/{selected-template}/supabase/migrations/
# Expected: 00001_auth_schema.sql, 00002_billing_schema.sql, etc.
```

## Understanding Template Schemas

Each template includes pre-built migrations:

### Common Schema (All Templates)

**00001_auth_schema.sql** - User authentication
```sql
-- Profiles table (extends Supabase auth.users)
CREATE TABLE public.profiles (
  id UUID REFERENCES auth.users PRIMARY KEY,
  email TEXT,
  full_name TEXT,
  avatar_url TEXT,
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- RLS: Users can only read/update their own profile
ALTER TABLE public.profiles ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can view own profile"
  ON public.profiles FOR SELECT
  USING (auth.uid() = id);

CREATE POLICY "Users can update own profile"
  ON public.profiles FOR UPDATE
  USING (auth.uid() = id);
```

**00002_billing_schema.sql** - Stripe integration
```sql
-- Customers table (links Supabase user to Stripe customer)
CREATE TABLE public.customers (
  id UUID REFERENCES auth.users PRIMARY KEY,
  stripe_customer_id TEXT UNIQUE,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Subscriptions table
CREATE TABLE public.subscriptions (
  id TEXT PRIMARY KEY,  -- Stripe subscription ID
  user_id UUID REFERENCES auth.users,
  status TEXT,
  price_id TEXT,
  quantity INTEGER DEFAULT 1,
  cancel_at_period_end BOOLEAN DEFAULT FALSE,
  current_period_start TIMESTAMPTZ,
  current_period_end TIMESTAMPTZ,
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW()
);
```

### Template-Specific Schemas

**Analytics Dashboard (00003_app_schema.sql):**
```sql
-- Sites to track
CREATE TABLE public.sites (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID REFERENCES auth.users,
  domain TEXT NOT NULL,
  is_public BOOLEAN DEFAULT FALSE,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Analytics events
CREATE TABLE public.events (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  site_id UUID REFERENCES public.sites,
  event_type TEXT,
  path TEXT,
  referrer TEXT,
  country TEXT,
  created_at TIMESTAMPTZ DEFAULT NOW()
);
```

**Productivity Tool (00003_app_schema.sql):**
```sql
-- Workspaces
CREATE TABLE public.workspaces (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  name TEXT NOT NULL,
  owner_id UUID REFERENCES auth.users,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Workspace members
CREATE TABLE public.workspace_members (
  workspace_id UUID REFERENCES public.workspaces,
  user_id UUID REFERENCES auth.users,
  role TEXT DEFAULT 'member',
  PRIMARY KEY (workspace_id, user_id)
);

-- Tasks
CREATE TABLE public.tasks (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  workspace_id UUID REFERENCES public.workspaces,
  title TEXT NOT NULL,
  description TEXT,
  status TEXT DEFAULT 'todo',
  assignee_id UUID REFERENCES auth.users,
  created_at TIMESTAMPTZ DEFAULT NOW()
);
```

**Content Creator (00003_app_schema.sql):**
```sql
-- Connected social accounts
CREATE TABLE public.connected_accounts (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID REFERENCES auth.users,
  platform TEXT NOT NULL,  -- 'twitter', 'linkedin', etc.
  access_token TEXT,
  refresh_token TEXT,
  expires_at TIMESTAMPTZ,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Posts
CREATE TABLE public.posts (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID REFERENCES auth.users,
  content TEXT NOT NULL,
  platforms TEXT[],  -- Array of platforms to post to
  scheduled_at TIMESTAMPTZ,
  published_at TIMESTAMPTZ,
  status TEXT DEFAULT 'draft',
  created_at TIMESTAMPTZ DEFAULT NOW()
);
```

## Process Workflow

### Phase 1: Validate Connection

```bash
# Link to Supabase project
npx supabase link --project-ref $SUPABASE_PROJECT_REF

# Verify connection
npx supabase db remote status
```

**Expected output:**
```
Linked to project: your-project-name
Remote database URL: postgresql://...
```

**If connection fails:**
1. Verify `SUPABASE_ACCESS_TOKEN` is valid
2. Verify `SUPABASE_PROJECT_REF` is correct (find in Supabase dashboard URL)
3. Check project exists and user has access
4. Escalate to Co-CEO if cannot resolve

### Phase 2: Check Existing Schema

Before running migrations, check current state:

```bash
# List existing tables
npx supabase db remote query "SELECT table_name FROM information_schema.tables WHERE table_schema = 'public'"
```

**If tables exist:**
- May be from previous deployment
- Check if migrations are compatible
- Consider `--reset` flag for clean slate (DESTRUCTIVE)

### Phase 3: Run Migrations

Execute migrations in order:

```bash
# Push all migrations to remote
npx supabase db push

# Or run specific migration
npx supabase db remote query -f templates/{template}/supabase/migrations/00001_auth_schema.sql
```

**Migration order is critical:**
1. `00001_auth_schema.sql` - Base user tables
2. `00002_billing_schema.sql` - Stripe integration tables
3. `00003_app_schema.sql` - Application-specific tables
4. `00004_billing_enhancements.sql` - Additional billing features

### Phase 4: Verify RLS Policies

After migrations, verify RLS is enabled:

```bash
# Check RLS status on all tables
npx supabase db remote query "
  SELECT tablename, rowsecurity 
  FROM pg_tables 
  WHERE schemaname = 'public'
"
```

**Expected:** All tables should have `rowsecurity = true`

**If RLS is disabled:**
```sql
ALTER TABLE public.{table_name} ENABLE ROW LEVEL SECURITY;
```

### Phase 5: Configure Auth Providers

Configure Google OAuth in Supabase:

1. **Via Dashboard (Recommended for first-time setup):**
   - Go to Authentication → Providers
   - Enable Google
   - Add Client ID and Secret from Google Cloud Console

2. **Via API (for automation):**
```bash
# This typically requires manual dashboard configuration
# Document the required steps for the user
```

**Required OAuth callback URL:**
```
https://{project-ref}.supabase.co/auth/v1/callback
```

### Phase 6: Configure Redirect URLs

Set allowed redirect URLs in Supabase Auth settings:

```
http://localhost:3000/**
https://yourdomain.com/**
```

### Phase 7: Verify Deployment

Run verification checks:

```bash
# List all tables
npx supabase db remote query "SELECT table_name FROM information_schema.tables WHERE table_schema = 'public' ORDER BY table_name"

# Check RLS policies
npx supabase db remote query "SELECT tablename, policyname FROM pg_policies WHERE schemaname = 'public'"

# Verify functions exist
npx supabase db remote query "SELECT routine_name FROM information_schema.routines WHERE routine_schema = 'public'"
```

### Phase 8: Update Environment Template

Update `templates/{template}/frontend/.env.example`:

```bash
# Supabase Configuration
NEXT_PUBLIC_SUPABASE_URL=https://{project-ref}.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=eyJhbGciOiJIUzI1NiIs...
SUPABASE_SERVICE_ROLE_KEY=eyJhbGciOiJIUzI1NiIs...
```

## Helper Script

Location: `.shared/scripts/supabase/run-migrations.py`

**Usage:**
```bash
# Dry run (validate migrations without executing)
python3 .shared/scripts/supabase/run-migrations.py \
  --migrations templates/analytics-dashboard/supabase/migrations/ \
  --dry-run

# Execute migrations
python3 .shared/scripts/supabase/run-migrations.py \
  --migrations templates/analytics-dashboard/supabase/migrations/ \
  --execute

# Verify deployment
python3 .shared/scripts/supabase/run-migrations.py \
  --verify
```

## Error Handling

### Migration Conflicts
If a migration fails due to existing objects:
```sql
-- Option 1: Drop and recreate (DESTRUCTIVE)
DROP TABLE IF EXISTS public.{table_name} CASCADE;

-- Option 2: Skip if exists (SAFE)
CREATE TABLE IF NOT EXISTS public.{table_name} (...);
```

### RLS Policy Errors
If policy already exists:
```sql
DROP POLICY IF EXISTS "policy_name" ON public.{table_name};
CREATE POLICY "policy_name" ON public.{table_name} ...;
```

### Connection Timeouts
- Supabase free tier may have cold starts
- Retry connection after 30 seconds
- Check Supabase status page if persistent

### Insufficient Permissions
- Verify access token has admin rights
- Check project owner vs member permissions
- May need to regenerate access token

## Rollback Strategy

If deployment fails midway:

1. **Check migration state:**
```bash
npx supabase db remote query "SELECT * FROM supabase_migrations.schema_migrations"
```

2. **Manual rollback (if needed):**
```sql
-- Reverse changes manually
DROP TABLE IF EXISTS public.{failed_table} CASCADE;
```

3. **Full reset (DESTRUCTIVE):**
```bash
npx supabase db reset --linked
```

## Output Report

Provide summary to Co-CEO:

```markdown
## Supabase Deployment Complete

**Template:** analytics-dashboard
**Project:** your-project-ref

### Migrations Applied

| Migration | Status | Tables Created |
|-----------|--------|----------------|
| 00001_auth_schema.sql | ✓ Applied | profiles |
| 00002_billing_schema.sql | ✓ Applied | customers, subscriptions |
| 00003_app_schema.sql | ✓ Applied | sites, events |
| 00004_billing_enhancements.sql | ✓ Applied | usage_records |

### RLS Status

| Table | RLS Enabled | Policies |
|-------|-------------|----------|
| profiles | ✓ | 2 policies |
| customers | ✓ | 2 policies |
| subscriptions | ✓ | 2 policies |
| sites | ✓ | 3 policies |
| events | ✓ | 2 policies |

### Auth Configuration

**Google OAuth:** Requires manual configuration
1. Go to Supabase Dashboard → Authentication → Providers
2. Enable Google provider
3. Add OAuth credentials from Google Cloud Console
4. Set callback URL: `https://{project-ref}.supabase.co/auth/v1/callback`

### Environment Variables

Add these to your `.env.local`:
```
NEXT_PUBLIC_SUPABASE_URL=https://{project-ref}.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=your-anon-key
SUPABASE_SERVICE_ROLE_KEY=your-service-role-key
```

### Next Steps

1. Configure Google OAuth in Supabase Dashboard
2. Add environment variables to `.env.local`
3. Test authentication flow locally
```

## Security Notes

1. **Never commit service role key:** This key bypasses RLS
2. **Use anon key for frontend:** This respects RLS policies
3. **Verify RLS on all tables:** Missing RLS = data exposure
4. **Test RLS policies:** Query as authenticated vs anonymous user
5. **Run post-deployment audit:** `.shared/scripts/supabase/security-audit.sh` must pass (search_path on SECURITY DEFINER functions, RLS enabled) before proceeding

## Related Skills

- `stripe-deployer`: Deploy billing (can run in parallel)
- `template-validator`: Verify template structure before deployment
