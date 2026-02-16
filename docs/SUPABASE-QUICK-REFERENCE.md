# Supabase Skills Quick Reference

## Architecture at a Glance

```
Local Project Scripts          Global Credentials
(.shared/scripts/supabase/)   (/etc/supabase/)
        ↓                              ↑
   supabase_api.py ←────────────→ config.conf
        ↑                            /etc/supabase/
        │                         projects.json
Skills (SKILL.md) ← references
        ↓
Python scripts execute with loaded credentials
```

## Test Status

✅ **All 33 Tests Passed (100%)**
- Global credential files exist and have correct permissions
- All 11 local scripts present and functional
- Credential loading mechanism verified
- All 4 skills reference scripts correctly
- Scripts execute without errors
- Module imports work perfectly

**Test Report:** `docs/test-results-supabase-skills.json`
**Detailed Report:** `docs/SUPABASE-SKILLS-CREDENTIAL-VERIFICATION.md`

## Credential Files

### Global Configuration
**Location:** `/etc/supabase/config.conf`
```
SUPABASE_ACCESS_TOKEN=sbp_xxxx...  # Personal Access Token from Supabase dashboard
SUPABASE_ORG_ID=your-org-id         # Organization ID from Supabase
```

### Project Credentials
**Location:** `/etc/supabase/projects.json`
```json
{
  "project-ref": {
    "name": "Project Name",
    "anon_key": "eyJ...",
    "service_role_key": "eyJ...",
    "database_url": "postgresql://..."
  }
}
```

## Skills Quick Map

| Skill | Purpose | Uses |
|-------|---------|------|
| `supabase-project-manage` | Create/list projects, get API keys | Management API (PAT) |
| `supabase-database` | Create tables, run migrations, query data | Project credentials |
| `supabase-auth-setup` | Set up auth patterns, RLS policies | Project credentials |
| `supabase-deployer` | Deploy template schema to live project | Project credentials |

## Common Commands

### Setup (One-time)

```bash
# 1. Create global config (if not exists)
sudo mkdir -p /etc/supabase
echo "SUPABASE_ACCESS_TOKEN=sbp_..." | sudo tee /etc/supabase/config.conf
echo "SUPABASE_ORG_ID=org-123" | sudo tee -a /etc/supabase/config.conf
sudo chmod 600 /etc/supabase/config.conf

# 2. Create a Supabase project
python3 ~/.shared/scripts/supabase/create_project.py \
  --name "My App" \
  --region "eu-central-1" \
  --wait \
  --save-credentials

# 3. Verify it was saved
python3 ~/.shared/scripts/supabase/save_project_credentials.py --list
```

### Common Operations

```bash
# List your projects
python3 ~/.shared/scripts/supabase/list_projects.py

# Get API keys for a project
python3 ~/.shared/scripts/supabase/get_api_keys.py --ref "abcdefghij"

# Create a table
python3 ~/.shared/scripts/supabase/execute_sql.py \
  --ref "abcdefghij" \
  --sql "CREATE TABLE posts (id UUID PRIMARY KEY DEFAULT gen_random_uuid(), ...)"

# Query data
python3 ~/.shared/scripts/supabase/query_table.py \
  --ref "abcdefghij" \
  --table "posts" \
  --limit 10

# Setup authentication
python3 ~/.shared/scripts/supabase/setup_auth.py \
  --ref "abcdefghij" \
  --pattern "user-profiles"
```

## Troubleshooting

### "SUPABASE_ACCESS_TOKEN not found"
→ Set up `/etc/supabase/config.conf` as shown above

### "Project not found in saved projects"
→ Run `save_project_credentials.py --list` to see saved projects
→ Or save new project with `create_project.py --save-credentials`

### Scripts not found when running from skill
→ Verify `.shared/scripts/supabase/` directory exists
→ Verify all scripts are present: `ls ~/.shared/scripts/supabase/`

## Verification Commands

```bash
# Run full test suite
python3 ~/.shared/scripts/supabase/test-skills-credentials.py

# Check global config exists
cat /etc/supabase/config.conf

# Check saved projects
cat /etc/supabase/projects.json

# Check local scripts
ls -la ~/.shared/scripts/supabase/

# Test API access (requires valid PAT)
python3 ~/.shared/scripts/supabase/list_projects.py
```

## Files Reference

| File | Purpose | Permissions |
|------|---------|-------------|
| `/etc/supabase/config.conf` | Global PAT & Org ID | 600 (owner read/write only) |
| `/etc/supabase/projects.json` | Project credentials | 600 (owner read/write only) |
| `.shared/scripts/supabase/*` | Local scripts | 644 (readable) |
| `.shared/skills/supabase-*/*` | Skill documentation | 644 (readable) |

## Next: Using in Phase 4.3

When deploying templates during Phase 4.3:

1. **supabase-deployer skill** will:
   - Load credentials from `/etc/supabase/projects.json`
   - Run migrations from template schema
   - Enable RLS policies
   - Return environment variables for frontend

2. **Manual setup** (if not using deployer):
   ```bash
   # Apply auth schema
   python3 ~/.shared/scripts/supabase/setup_auth.py \
     --ref "abc..." \
     --pattern "user-profiles"

   # Apply migrations
   python3 ~/.shared/scripts/supabase/execute_sql.py \
     --ref "abc..." \
     --file "migrations/001_schema.sql"
   ```

## Important Notes

⚠️ **Never commit** `/etc/supabase/config.conf` - contains secrets
✅ **Do commit** `.shared/skills/` and `.shared/scripts/` - non-sensitive code
✅ **Portability** - All scripts use `~/.shared/scripts/supabase/` paths, works across systems

---

For detailed information, see: `docs/SUPABASE-SKILLS-CREDENTIAL-VERIFICATION.md`
