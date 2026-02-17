---
name: supabase-database
description: Execute SQL and manage database schema on Supabase. Use when the user wants to create tables, run migrations, query data, or manage Row Level Security policies.
---

# Supabase Database Operations

Execute SQL, manage schema, and handle RLS policies on Supabase projects.

## Prerequisites

**CRITICAL**: Before using this skill:

1. Project credentials must be saved using `save_project_credentials.py`
2. PostgreSQL client (`psql`) must be installed for SQL execution
3. Database URL must include the password

**Check saved projects**:
```bash
python3 .shared/scripts/supabase/save_project_credentials.py --list
```

**Install psql if missing**:
```bash
sudo apt-get install postgresql-client
```

## When to Use

Use this skill when the user wants to:
- Create tables or modify schema
- Run SQL migrations
- Query data directly
- List tables and columns
- Manage RLS policies
- Execute raw SQL statements

## Available Operations

### 1. Execute SQL

Run any SQL statement:

```bash
# Simple query
python3 .shared/scripts/supabase/execute_sql.py \
    --ref "abcdefghij" \
    --sql "SELECT * FROM profiles LIMIT 5"

# Create table
python3 .shared/scripts/supabase/execute_sql.py \
    --ref "abcdefghij" \
    --sql "CREATE TABLE posts (id UUID PRIMARY KEY DEFAULT gen_random_uuid(), title TEXT, content TEXT, user_id UUID REFERENCES auth.users(id), created_at TIMESTAMPTZ DEFAULT NOW())"

# Execute from file
python3 .shared/scripts/supabase/execute_sql.py \
    --ref "abcdefghij" \
    --file "/path/to/migration.sql"

# Dry-run (preview SQL without executing)
python3 .shared/scripts/supabase/execute_sql.py \
    --ref "abcdefghij" \
    --sql "DROP TABLE users" \
    --dry-run
```

**Drop a table**:
```bash
python3 .shared/scripts/supabase/execute_sql.py \
    --ref "abcdefghij" \
    --sql "DROP TABLE IF EXISTS my_table CASCADE"
```

### 2. List Tables

```bash
# List all tables in public schema
python3 .shared/scripts/supabase/list_tables.py --ref "abcdefghij"

# List tables in specific schema
python3 .shared/scripts/supabase/list_tables.py --ref "abcdefghij" --schema "auth"

# Get columns for a table
python3 .shared/scripts/supabase/list_tables.py --ref "abcdefghij" --table "profiles"
```

### 3. Query Data (PostgREST)

Use PostgREST API for CRUD operations:

```bash
# Basic query
python3 .shared/scripts/supabase/query_table.py \
    --ref "abcdefghij" \
    --table "profiles"

# With filters
python3 .shared/scripts/supabase/query_table.py \
    --ref "abcdefghij" \
    --table "posts" \
    --filter "status=eq.published" \
    --select "id,title,created_at" \
    --limit 10 \
    --order "created_at.desc"
```

**PostgREST filter operators**:
- `eq` - equals
- `neq` - not equals
- `gt`, `gte` - greater than (or equal)
- `lt`, `lte` - less than (or equal)
- `like`, `ilike` - pattern matching
- `in` - in list: `status=in.(draft,published)`

### 4. Mutate Data (Insert/Update/Delete)

```bash
# Insert single row
python3 .shared/scripts/supabase/mutate_table.py \
    --ref "abcdefghij" \
    --table "posts" \
    --insert '{"title": "Hello", "content": "World"}'

# Insert multiple rows (batch)
python3 .shared/scripts/supabase/mutate_table.py \
    --ref "abcdefghij" \
    --table "posts" \
    --insert '[{"title": "Post 1"}, {"title": "Post 2"}, {"title": "Post 3"}]'

# Update (filter required)
python3 .shared/scripts/supabase/mutate_table.py \
    --ref "abcdefghij" \
    --table "posts" \
    --update '{"status": "published"}' \
    --filter "id=eq.123"

# Delete (filter required)
python3 .shared/scripts/supabase/mutate_table.py \
    --ref "abcdefghij" \
    --table "posts" \
    --delete \
    --filter "status=eq.draft"
```

### 5. Manage RLS Policies

```bash
# Enable RLS on table
python3 .shared/scripts/supabase/manage_rls.py \
    --ref "abcdefghij" \
    --table "posts" \
    --enable

# List existing policies
python3 .shared/scripts/supabase/manage_rls.py \
    --ref "abcdefghij" \
    --table "posts" \
    --list

# Add policy
python3 .shared/scripts/supabase/manage_rls.py \
    --ref "abcdefghij" \
    --table "posts" \
    --add-policy \
    --policy-name "Users can view own posts" \
    --operation "SELECT" \
    --using "auth.uid() = user_id"

# Drop policy
python3 .shared/scripts/supabase/manage_rls.py \
    --ref "abcdefghij" \
    --table "posts" \
    --drop-policy "Users can view own posts"
```

## Common RLS Patterns

### Owner-based access
```sql
-- Users can only see their own rows
USING (auth.uid() = user_id)
```

### Public read, owner write
```sql
-- SELECT: anyone can read
USING (true)

-- UPDATE/DELETE: only owner
USING (auth.uid() = user_id)
```

### Organization-based
```sql
-- Users in same org can access
USING (
    organization_id IN (
        SELECT organization_id FROM organization_members
        WHERE user_id = auth.uid()
    )
)
```

## Migration File Best Practices

When creating migration files:

1. **Use transactions** for safety:
```sql
BEGIN;
-- Your changes here
COMMIT;
```

2. **Make idempotent** with IF NOT EXISTS:
```sql
CREATE TABLE IF NOT EXISTS ...
CREATE INDEX IF NOT EXISTS ...
```

3. **Include rollback comments**:
```sql
-- ROLLBACK: DROP TABLE posts;
```

4. **Save migrations** to project directory:
```
migrations/
├── 001_initial_schema.sql
├── 002_add_posts.sql
└── 003_add_rls_policies.sql
```

## Supabase-Specific SQL

### UUID generation
```sql
gen_random_uuid()
```

### Timestamps
```sql
created_at TIMESTAMPTZ DEFAULT NOW()
updated_at TIMESTAMPTZ DEFAULT NOW()
```

### Reference auth.users
```sql
user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE
```

### Get current user
```sql
auth.uid()           -- Current user's UUID
auth.jwt()           -- Full JWT claims
auth.role()          -- Current role
```

## Error Handling

Common errors:
- **Connection refused**: Check database URL and password
- **Permission denied**: Service role key may be needed
- **Relation does not exist**: Table not created yet
- **Policy already exists**: Drop existing policy first
