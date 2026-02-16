---
name: supabase-auth-setup
description: Set up authentication patterns for Supabase SaaS projects. Use when the user wants to configure user profiles, organizations, roles, or Row Level Security for a new project.
---

# Supabase Authentication Setup

Set up common authentication patterns for SaaS applications on Supabase.

## Prerequisites

1. Project credentials saved via `save_project_credentials.py`
2. Database URL configured with password
3. PostgreSQL client (`psql`) installed

## When to Use

Use this skill when the user wants to:
- Set up user profiles linked to auth.users
- Create organization/team multi-tenancy
- Implement role-based access control
- Configure RLS for a SaaS application
- Generate auth-related database migrations

## Available Auth Patterns

### 1. User Profiles Pattern

Basic user profiles linked to Supabase Auth:

```bash
# Preview SQL (dry run)
python3 .shared/scripts/supabase/setup_auth.py \
    --ref "abcdefghij" \
    --pattern "user-profiles" \
    --dry-run

# Apply to database
python3 .shared/scripts/supabase/setup_auth.py \
    --ref "abcdefghij" \
    --pattern "user-profiles"

# Save as migration file
python3 .shared/scripts/supabase/setup_auth.py \
    --ref "abcdefghij" \
    --pattern "user-profiles" \
    --save-migration "./migrations/001_user_profiles.sql"
```

**Creates**:
- `profiles` table linked to `auth.users`
- RLS policies for profile access
- Trigger to auto-create profile on signup
- Updated_at trigger

### 2. SaaS Multi-Tenant Pattern

Organizations with team members:

```bash
python3 .shared/scripts/supabase/setup_auth.py \
    --ref "abcdefghij" \
    --pattern "saas-multi-tenant"
```

**Creates**:
- `organizations` table
- `organization_members` table with roles (owner/admin/member)
- `profiles` table
- Helper functions: `is_org_member()`, `is_org_admin()`
- Full RLS policies for org-based access
- Triggers for auto profile creation and org owner assignment

### 3. Role-Based Access Pattern

User roles with granular permissions:

```bash
python3 .shared/scripts/supabase/setup_auth.py \
    --ref "abcdefghij" \
    --pattern "role-based"
```

**Creates**:
- `user_role` enum (user, moderator, admin, super_admin)
- `profiles` table with role column
- Helper functions: `get_user_role()`, `is_admin()`
- RLS policies respecting user roles

## Pattern Details

### User Profiles Schema

```
profiles
├── id (UUID, FK to auth.users)
├── email (TEXT)
├── full_name (TEXT)
├── avatar_url (TEXT)
├── created_at (TIMESTAMPTZ)
└── updated_at (TIMESTAMPTZ)
```

### Multi-Tenant Schema

```
organizations
├── id (UUID)
├── name (TEXT)
├── slug (TEXT, unique)
├── created_at
└── updated_at

organization_members
├── id (UUID)
├── organization_id (FK)
├── user_id (FK to auth.users)
├── role (owner/admin/member)
└── created_at

profiles
├── id (UUID, FK to auth.users)
├── email, full_name, avatar_url
├── created_at
└── updated_at
```

### Role-Based Schema

```
profiles
├── id (UUID, FK to auth.users)
├── email, full_name, avatar_url
├── role (user_role enum)
├── created_at
└── updated_at
```

## Extending Auth Patterns

After applying a base pattern, add custom tables with proper RLS:

### Add Posts Table (User Profiles Pattern)

```bash
python3 .shared/scripts/supabase/execute_sql.py \
    --ref "abcdefghij" \
    --sql "
CREATE TABLE public.posts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE,
    title TEXT NOT NULL,
    content TEXT,
    published BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

ALTER TABLE public.posts ENABLE ROW LEVEL SECURITY;

CREATE POLICY \"Users can view own posts\"
    ON public.posts FOR SELECT
    USING (auth.uid() = user_id);

CREATE POLICY \"Users can create posts\"
    ON public.posts FOR INSERT
    WITH CHECK (auth.uid() = user_id);

CREATE POLICY \"Users can update own posts\"
    ON public.posts FOR UPDATE
    USING (auth.uid() = user_id);

CREATE POLICY \"Users can delete own posts\"
    ON public.posts FOR DELETE
    USING (auth.uid() = user_id);

CREATE POLICY \"Anyone can view published posts\"
    ON public.posts FOR SELECT
    USING (published = true);
"
```

### Add Org-Scoped Table (Multi-Tenant Pattern)

```bash
python3 .shared/scripts/supabase/execute_sql.py \
    --ref "abcdefghij" \
    --sql "
CREATE TABLE public.projects (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id UUID REFERENCES public.organizations(id) ON DELETE CASCADE,
    name TEXT NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

ALTER TABLE public.projects ENABLE ROW LEVEL SECURITY;

CREATE POLICY \"Org members can view projects\"
    ON public.projects FOR SELECT
    USING (public.is_org_member(organization_id));

CREATE POLICY \"Org admins can manage projects\"
    ON public.projects FOR ALL
    USING (public.is_org_admin(organization_id));
"
```

## Frontend Integration

After setting up auth, configure your frontend:

### Environment Variables

```env
NEXT_PUBLIC_SUPABASE_URL=https://abcdefghij.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=eyJhbGc...
```

### Supabase Client (Next.js)

```typescript
import { createClient } from '@supabase/supabase-js'

const supabase = createClient(
  process.env.NEXT_PUBLIC_SUPABASE_URL!,
  process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!
)
```

### Get Current User Profile

```typescript
const { data: profile } = await supabase
  .from('profiles')
  .select('*')
  .single()
```

### Sign Up with Profile Data

```typescript
await supabase.auth.signUp({
  email: 'user@example.com',
  password: 'password',
  options: {
    data: {
      full_name: 'John Doe',
      avatar_url: 'https://...'
    }
  }
})
```

## Auth Provider Configuration

Configure OAuth providers in Supabase Dashboard:
1. Go to Authentication > Providers
2. Enable desired providers (Google, GitHub, etc.)
3. Add OAuth credentials

**Supported providers**: Google, GitHub, GitLab, Bitbucket, Azure, Discord, Facebook, Twitch, Twitter, Apple, Slack, Spotify, Zoom, and more.

## Email Templates

Customize auth emails in Dashboard:
- Authentication > Email Templates
- Confirm signup, Reset password, Magic link, Invite user

## Troubleshooting

**Profile not created on signup**:
- Check trigger exists: `SELECT * FROM pg_trigger WHERE tgname = 'on_auth_user_created'`
- Ensure function has `SECURITY DEFINER`

**RLS blocking access**:
- Temporarily disable: `ALTER TABLE x DISABLE ROW LEVEL SECURITY`
- Check policies: Use `manage_rls.py --list`
- Verify `auth.uid()` returns expected value

**Organization not accessible**:
- Verify membership exists in `organization_members`
- Check `is_org_member()` function works
