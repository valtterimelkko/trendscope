#!/usr/bin/env bash
#
# Supabase Security Audit
# Runs minimal hardening checks against the linked Supabase project.
#
# Checks:
#   1) Supabase DB lint (if available) for ERROR/WARNING findings
#   2) SECURITY DEFINER functions missing immutable search_path
#   3) Public tables with RLS disabled
#
# Usage:
#   SUPABASE_PROJECT_REF=abc123 SUPABASE_ACCESS_TOKEN=... ./security-audit.sh
#

set -euo pipefail

REPORT_FILE="${REPORT_FILE:-docs/supabase-security-audit.md}"
mkdir -p "$(dirname "$REPORT_FILE")"

command -v npx >/dev/null 2>&1 || { echo "npx not found. Install Node/npm."; exit 1; }

status_msg() { printf "%b\n" "$1" | tee -a "$REPORT_FILE"; }

lint_output=""
lint_exit=0
search_path_output=""
rls_output=""
issues=0

# Ensure Supabase CLI can reach the project (linked or env configured)
if ! npx supabase db remote status >/dev/null 2>&1; then
  echo "Supabase CLI is not linked or credentials are missing. Link the project before running."
  exit 1
fi

truncate -s 0 "$REPORT_FILE"
status_msg "# Supabase Security Audit"
status_msg ""
status_msg "_Generated: $(date -u +"%Y-%m-%dT%H:%M:%SZ")_"
status_msg ""

# 1) Run lint (best-effort; still continue if lint not available)
status_msg "## Supabase DB Lint"
if lint_output=$(npx supabase db lint 2>&1); then
status_msg "Lint command succeeded."
status_msg ""
status_msg "```
${lint_output}
```"
  if echo "$lint_output" | grep -qi "error"; then
    issues=1
  fi
else
  lint_exit=$?
  status_msg "Lint command failed (exit ${lint_exit}). Output recorded for triage:"
  status_msg ""
  status_msg "```
${lint_output}
```"
  issues=1
fi
status_msg ""

# Helper to count data rows (exclude header/blank)
row_count() {
  echo "$1" | awk 'NR>2 && NF>0 {c++} END {print c+0}'
}

# 2) SECURITY DEFINER functions missing immutable search_path
status_msg "## SECURITY DEFINER functions missing search_path='public'"
search_path_query=$(cat <<'SQL'
SELECT n.nspname || '.' || p.proname AS function_name
FROM pg_proc p
JOIN pg_namespace n ON n.oid = p.pronamespace
WHERE n.nspname = 'public'
  AND p.prosecdef = true
  AND (
    p.proconfig IS NULL
    OR NOT EXISTS (
      SELECT 1 FROM unnest(p.proconfig) conf WHERE conf ~* '^[[:space:]]*search_path[[:space:]]*=[[:space:]]*\"?public\"?[[:space:]]*$'
    )
  )
ORDER BY 1;
SQL
)

if search_path_output=$(npx supabase db remote query "$search_path_query" 2>&1); then
  status_msg "```
${search_path_output}
```"
  if [[ "$(row_count "$search_path_output")" -gt 0 ]]; then
    issues=1
  fi
else
  status_msg "Query failed. Output:"
  status_msg "```
${search_path_output}
```"
  issues=1
fi
status_msg ""

# 3) Public tables with RLS disabled
status_msg "## Public tables with RLS disabled"
rls_query=$(cat <<'SQL'
SELECT tablename
FROM pg_tables
WHERE schemaname = 'public'
  AND rowsecurity = false
ORDER BY tablename;
SQL
)

if rls_output=$(npx supabase db remote query "$rls_query" 2>&1); then
  status_msg "```
${rls_output}
```"
  if [[ "$(row_count "$rls_output")" -gt 0 ]]; then
    issues=1
  fi
else
  status_msg "Query failed. Output:"
  status_msg "```
${rls_output}
```"
  issues=1
fi
status_msg ""

status_msg "## Audit Result"
if [[ "$issues" -gt 0 ]]; then
  status_msg "- ❌ Issues detected. Resolve before proceeding to implementation."
  exit 1
else
  status_msg "- ✅ Passed: No lint errors, no SECURITY DEFINER search_path gaps, and RLS enabled."
fi
