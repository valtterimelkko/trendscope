---
name: supabase-project-manage
description: Manage Supabase projects - create projects, list organizations, get API keys, save credentials. Use when the user wants to set up a new Supabase project or manage existing projects.
---

# Manage Supabase Projects

Manage Supabase projects and organizations via the Management API.

## Prerequisites

**CRITICAL**: Before using this skill, ensure:

1. Supabase Personal Access Token (PAT) is configured in `/etc/supabase/config.conf`
2. User has created PAT at: https://supabase.com/dashboard/account/tokens

If config file doesn't exist, inform user to:
```bash
sudo mkdir -p /etc/supabase
echo "SUPABASE_ACCESS_TOKEN=your_pat_here" | sudo tee /etc/supabase/config.conf
echo "SUPABASE_ORG_ID=your_org_id" | sudo tee -a /etc/supabase/config.conf
sudo chmod 600 /etc/supabase/config.conf
```

## When to Use

Use this skill when the user wants to:
- List their Supabase organizations
- List existing Supabase projects
- Create a new Supabase project
- Get project details or API keys
- Save project credentials for local use

## Available Operations

### 1. List Organizations

```bash
python3 .shared/scripts/supabase/list_organizations.py
```

Returns all organizations the user has access to with their IDs.

### 2. List Projects

```bash
python3 .shared/scripts/supabase/list_projects.py
```

Returns all projects with ref IDs, names, regions, and status.

### 3. Create New Project

**Basic creation** (returns immediately, you check status later):
```bash
python3 .shared/scripts/supabase/create_project.py \
    --name "My SaaS App" \
    --region "eu-central-1"
```

**Full automation** (waits for ready, saves all credentials):
```bash
python3 .shared/scripts/supabase/create_project.py \
    --name "My SaaS App" \
    --region "eu-central-1" \
    --wait \
    --save-credentials
```

This will:
1. Auto-generate a secure database password
2. Create the project
3. Wait for it to become ACTIVE_HEALTHY (~1-2 min)
4. Fetch API keys (anon + service_role)
5. Save all credentials to `/etc/supabase/projects.json`
6. Return database_url ready for SQL execution

**Available Regions**:
- `us-east-1` (N. Virginia)
- `us-west-1` (N. California)
- `eu-central-1` (Frankfurt)
- `eu-west-1` (Ireland)
- `eu-west-2` (London)
- `ap-southeast-1` (Singapore)
- `ap-northeast-1` (Tokyo)

**Flags**:
- `--wait`: Wait for project to be ready before returning
- `--save-credentials`: Auto-save all credentials for immediate use
- `--db-pass`: Specify password instead of auto-generating

### 4. Get Project Details

```bash
# Basic info
python3 .shared/scripts/supabase/get_project.py --ref "abcdefghij"

# Include API keys
python3 .shared/scripts/supabase/get_project.py --ref "abcdefghij" --include-keys
```

### 5. Get API Keys

```bash
python3 .shared/scripts/supabase/get_api_keys.py --ref "abcdefghij"
```

Returns `anon` (public) key and `service_role` (admin) key.

### 6. Get Connection String

```bash
python3 .shared/scripts/supabase/get_connection_string.py --ref "abcdefghij"
```

Returns database host, port, and connection string template.

### 7. Save Project Credentials

Save credentials locally for use with database and auth skills:

```bash
python3 .shared/scripts/supabase/save_project_credentials.py \
    --ref "abcdefghij" \
    --name "My Project" \
    --anon-key "eyJhbGc..." \
    --service-key "eyJhbGc..." \
    --db-url "postgresql://postgres:password@db.xxx.supabase.co:5432/postgres"
```

**List saved projects**:
```bash
python3 .shared/scripts/supabase/save_project_credentials.py --list
```

### 8. Delete Project

**CAUTION**: This permanently deletes the project and all its data.

```bash
# Preview (shows project name, requires confirmation)
python3 .shared/scripts/supabase/delete_project.py --ref "abcdefghij"

# Actually delete
python3 .shared/scripts/supabase/delete_project.py --ref "abcdefghij" --confirm
```

This also removes saved credentials from `/etc/supabase/projects.json`.

## Typical New Project Workflow

When user wants to start a new SaaS project with Supabase:

1. **List organizations** to get org ID
2. **Create project** with chosen name and region
3. **Wait** for project status to become `ACTIVE_HEALTHY`
4. **Get API keys** (anon and service_role)
5. **Save credentials** locally for database operations
6. **Persist metadata (no secrets) to git for reuse**: write `docs/supabase-project.json` with `project_ref`, `project_name`, `supabase_url`, and `credentials_location: "/etc/supabase/projects.json"`
6. **Use supabase-auth-setup skill** to set up authentication
7. **Use supabase-database skill** for schema changes

## API Key Types

| Key Type | Use Case | Security |
|----------|----------|----------|
| `anon` | Client-side, public | Respects RLS policies |
| `service_role` | Server-side, admin | Bypasses RLS |

## Project Reference (ref)

The project `ref` is the 20-character ID in your Supabase URL:
- URL: `https://abcdefghij.supabase.co`
- Ref: `abcdefghij`

## Error Handling

Common errors:
- **401 Unauthorized**: PAT invalid or expired - regenerate at dashboard
- **403 Forbidden**: No access to organization - check org membership
- **409 Conflict**: Project name already exists - choose different name
