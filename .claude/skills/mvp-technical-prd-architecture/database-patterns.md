# Database Patterns for MVP SaaS

## Schema Management

**All schema changes via migrations:**
```bash
# Migrations in supabase/migrations/
supabase db reset  # Apply locally
# CI/CD applies to staging/production
```

## Core Tables Pattern

### Organizations (Multi-Tenant Root)

```sql
CREATE TABLE public.organizations (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  name TEXT NOT NULL,
  tier TEXT DEFAULT 'free' CHECK (tier IN ('free', 'pro', 'enterprise')),
  settings JSONB DEFAULT '{}',
  created_at TIMESTAMPTZ DEFAULT now(),
  updated_at TIMESTAMPTZ DEFAULT now()
);

-- RLS: Members can read their organizations
CREATE POLICY "org_read" ON public.organizations
FOR SELECT USING (
  id IN (SELECT organization_id FROM public.organization_members WHERE user_id = auth.uid())
);
```

### Organization Members (Tenant Membership)

```sql
CREATE TABLE public.organization_members (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  organization_id UUID REFERENCES public.organizations(id) ON DELETE CASCADE,
  user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE,
  role TEXT DEFAULT 'member' CHECK (role IN ('owner', 'admin', 'member', 'viewer')),
  created_at TIMESTAMPTZ DEFAULT now(),
  UNIQUE(organization_id, user_id)
);

-- Index for RLS performance
CREATE INDEX idx_org_members_user ON public.organization_members(user_id);

-- RLS: Users see their own memberships
CREATE POLICY "member_read" ON public.organization_members
FOR SELECT USING (user_id = auth.uid());
```

### User Profiles

```sql
CREATE TABLE public.profiles (
  id UUID PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
  full_name TEXT,
  avatar_url TEXT,
  settings JSONB DEFAULT '{}',
  created_at TIMESTAMPTZ DEFAULT now(),
  updated_at TIMESTAMPTZ DEFAULT now()
);

-- RLS: Users read/update own profile
CREATE POLICY "profile_read" ON public.profiles
FOR SELECT USING (id = auth.uid());

CREATE POLICY "profile_update" ON public.profiles
FOR UPDATE USING (id = auth.uid());
```

## Tenant-Specific Table Pattern

Every tenant-scoped table follows this pattern:

```sql
CREATE TABLE public.projects (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  organization_id UUID NOT NULL REFERENCES public.organizations(id) ON DELETE CASCADE,
  name TEXT NOT NULL,
  description TEXT,
  status TEXT DEFAULT 'active',
  metadata JSONB DEFAULT '{}',
  created_at TIMESTAMPTZ DEFAULT now(),
  updated_at TIMESTAMPTZ DEFAULT now()
);

-- CRITICAL: Index for RLS performance
CREATE INDEX idx_projects_org ON public.projects(organization_id);

-- RLS: Tenant isolation
CREATE POLICY "tenant_isolation" ON public.projects
FOR ALL USING (
  organization_id IN (
    SELECT organization_id FROM public.organization_members
    WHERE user_id = auth.uid()
  )
);
```

## Role-Based Access Pattern

For granular permissions within tenant:

```sql
-- Admin-only operations
CREATE POLICY "admin_delete" ON public.projects
FOR DELETE USING (
  organization_id IN (
    SELECT organization_id FROM public.organization_members
    WHERE user_id = auth.uid() AND role IN ('owner', 'admin')
  )
);
```

## Common Index Patterns

Beyond organization_id, add indexes for frequent query patterns:

```sql
-- User's own records
CREATE INDEX idx_{table}_user ON public.{table}(user_id) WHERE deleted_at IS NULL;

-- Status filters
CREATE INDEX idx_{table}_status ON public.{table}(status) WHERE deleted_at IS NULL;

-- Date range queries
CREATE INDEX idx_{table}_date ON public.{table}(created_at DESC);

-- Composite for complex filters
CREATE INDEX idx_{table}_composite ON public.{table}(organization_id, status, created_at DESC)
  WHERE deleted_at IS NULL;
```

**IMPORTANT:** Only add indexes for proven slow queries. Over-indexing slows down writes.

## Custom Claims for Performance (Advanced)

**When to use:** Users can belong to multiple organizations (2+). Every RLS subquery checking `organization_members` adds ~5-10ms per request.

**Trade-off:** More complex auth triggers vs. faster queries. Start without this, add when RLS becomes bottleneck.

### Implementation

```sql
-- Trigger to inject claims into JWT on login
CREATE OR REPLACE FUNCTION public.handle_user_login()
RETURNS TRIGGER AS $$
BEGIN
  -- Set custom claims based on user's memberships
  UPDATE auth.users SET raw_app_meta_data =
    raw_app_meta_data || jsonb_build_object(
      'org_ids', (SELECT array_agg(organization_id) FROM organization_members WHERE user_id = NEW.id)
    )
  WHERE id = NEW.id;
  RETURN NEW;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Also update when memberships change
CREATE TRIGGER refresh_user_claims
  AFTER INSERT OR UPDATE OR DELETE ON public.organization_members
  FOR EACH ROW EXECUTE FUNCTION public.handle_user_login();
```

Then in RLS:
```sql
-- Faster: check JWT claims instead of subquery
CREATE POLICY "fast_tenant_check" ON public.documents
FOR SELECT USING (
  organization_id = ANY((auth.jwt() -> 'app_metadata' -> 'org_ids')::uuid[])
);
```

**IMPORTANT:** Must refresh claims when user joins/leaves orgs, otherwise JWT is stale until next login.

## JSONB for Flexible Fields

Use for settings, metadata, integration configs:

```sql
-- Column definition
settings JSONB DEFAULT '{}'

-- Query with containment
SELECT * FROM projects WHERE settings @> '{"archived": true}';

-- Index for JSONB queries
CREATE INDEX idx_projects_settings ON public.projects USING gin(settings);
```

## Soft Delete Pattern

Never hard-delete business data:

```sql
ALTER TABLE public.projects ADD COLUMN deleted_at TIMESTAMPTZ;

-- RLS excludes soft-deleted by default
CREATE POLICY "exclude_deleted" ON public.projects
FOR SELECT USING (
  deleted_at IS NULL AND
  organization_id IN (SELECT organization_id FROM organization_members WHERE user_id = auth.uid())
);
```

## Audit Trail Pattern

```sql
CREATE TABLE public.audit_logs (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  organization_id UUID REFERENCES public.organizations(id),
  user_id UUID REFERENCES auth.users(id),
  action TEXT NOT NULL,
  table_name TEXT NOT NULL,
  record_id UUID,
  old_data JSONB,
  new_data JSONB,
  created_at TIMESTAMPTZ DEFAULT now()
);

-- Trigger for automatic auditing
CREATE OR REPLACE FUNCTION audit_trigger()
RETURNS TRIGGER AS $$
BEGIN
  INSERT INTO audit_logs (organization_id, user_id, action, table_name, record_id, old_data, new_data)
  VALUES (
    COALESCE(NEW.organization_id, OLD.organization_id),
    auth.uid(),
    TG_OP,
    TG_TABLE_NAME,
    COALESCE(NEW.id, OLD.id),
    CASE WHEN TG_OP = 'DELETE' THEN to_jsonb(OLD) ELSE NULL END,
    CASE WHEN TG_OP != 'DELETE' THEN to_jsonb(NEW) ELSE NULL END
  );
  RETURN COALESCE(NEW, OLD);
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;
```

## Updated_At Trigger Pattern

Apply this trigger to ALL tables with `updated_at` column:

```sql
-- Create trigger function once
CREATE OR REPLACE FUNCTION public.handle_updated_at()
RETURNS TRIGGER AS $$
BEGIN
  NEW.updated_at = now();
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Apply to each table
CREATE TRIGGER {table_name}_updated_at
  BEFORE UPDATE ON public.{table_name}
  FOR EACH ROW EXECUTE FUNCTION public.handle_updated_at();
```

**IMPORTANT:** Every table with `updated_at` must have this trigger, or the column will be stale.

## Key Constraints Checklist

For every new table:
- [ ] UUID primary key
- [ ] organization_id FK (if tenant-scoped)
- [ ] Index on organization_id
- [ ] RLS enabled: `ALTER TABLE public.X ENABLE ROW LEVEL SECURITY;`
- [ ] RLS policy for tenant isolation
- [ ] created_at TIMESTAMPTZ
- [ ] updated_at TIMESTAMPTZ with trigger (see pattern above)
- [ ] Soft delete column if business data
