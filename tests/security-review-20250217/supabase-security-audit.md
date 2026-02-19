# Supabase Security Audit Report

**Project:** TrendScope  
**Project Ref:** <project-ref>  
**Supabase URL:** https://<project-ref>.supabase.co  
**Audit Date:** 2026-02-17  
**Auditor:** Security Audit Agent (MODEL: kimi-k2.5)

---

## Executive Summary

This security audit evaluates the Row Level Security (RLS) configuration and access controls of the TrendScope Supabase project. The database contains 11 tables with RLS enabled on all tables. **Overall Security Status: MODERATE RISK** - several policy gaps and misconfigurations were identified that require attention.

### Key Findings Summary
- ✅ All 11 tables have RLS enabled
- ⚠️ 18 RLS policies defined, but several gaps exist
- ⚠️ Some policies apply to PUBLIC role (includes anon)
- ⚠️ Missing INSERT policies on critical tables
- ⚠️ No write protection for data tables (trends, niches, velocity history)
- ✅ Secure function configuration for user creation trigger

---

## 1. Table RLS Status Overview

| Table | RLS Enabled | Force RLS | Owner | Indexes | Triggers |
|-------|-------------|-----------|-------|---------|----------|
| `profiles` | ✅ Yes | No | postgres | 3 | 2 (updated_at, new_user) |
| `user_niches` | ✅ Yes | No | postgres | 2 | 0 |
| `alert_integrations` | ✅ Yes | No | postgres | 2 | 1 (updated_at) |
| `alerts` | ✅ Yes | No | postgres | 4 | 0 |
| `bookmarks` | ✅ Yes | No | postgres | 2 | 0 |
| `clients` | ✅ Yes | No | postgres | 2 | 1 (updated_at) |
| `client_alerts` | ✅ Yes | No | postgres | 1 | 0 |
| `trends` | ✅ Yes | No | postgres | 5 | 1 (updated_at) |
| `niches` | ✅ Yes | No | postgres | 2 | 0 |
| `trend_velocity_history` | ✅ Yes | No | postgres | 2 | 0 |
| `system_config` | ✅ Yes | No | postgres | 1 | 0 |

### Analysis
- All tables correctly have RLS enabled (`rowsecurity = t`)
- `relforcerowsecurity = f` is expected - allows postgres/admin to bypass RLS for maintenance
- All tables owned by `postgres` (standard Supabase configuration)
- Tables have appropriate indexes for query performance

---

## 2. RLS Policies Detailed Review

### 2.1 Profiles Table
| Policy | Command | Role | Using Clause | Status |
|--------|---------|------|--------------|--------|
| Users can view own profile | SELECT | public | `auth.uid() = id` | ✅ OK |
| Users can update own profile | UPDATE | public | `auth.uid() = id` | ✅ OK |

**⚠️ Security Issue:** No INSERT policy defined. Profiles can only be created via the `handle_new_user` trigger.

### 2.2 User Niches Table
| Policy | Command | Role | Using Clause | Status |
|--------|---------|------|--------------|--------|
| Users can view own niches | SELECT | public | `auth.uid() = user_id` | ⚠️ Issue |
| Users can manage own niches | ALL | public | `auth.uid() = user_id` | ⚠️ Issue |

**⚠️ Security Issue:** Policies apply to `public` role without explicit `TO authenticated`, meaning anon users could attempt queries (though they would return no data due to `auth.uid()` returning NULL).

### 2.3 Alert Integrations Table
| Policy | Command | Role | Using Clause | Status |
|--------|---------|------|--------------|--------|
| Users can view own integrations | SELECT | public | `auth.uid() = user_id` | ⚠️ Issue |
| Users can manage own integrations | ALL | public | `auth.uid() = user_id` | ⚠️ Issue |

**⚠️ Security Issue:** Same as above - applies to `public` role.

### 2.4 Alerts Table
| Policy | Command | Role | Using Clause | Status |
|--------|---------|------|--------------|--------|
| Users can view own alerts | SELECT | public | `auth.uid() = user_id` | ⚠️ Issue |

**🚨 Critical Issue:** Only SELECT policy exists. Missing INSERT, UPDATE, DELETE policies. The application likely relies on service_role for alert creation, which is acceptable for server-generated alerts, but this should be documented.

### 2.5 Bookmarks Table
| Policy | Command | Role | Using Clause | Status |
|--------|---------|------|--------------|--------|
| Users can view own bookmarks | SELECT | public | `auth.uid() = user_id` | ⚠️ Issue |
| Users can manage own bookmarks | ALL | public | `auth.uid() = user_id` | ⚠️ Issue |

**⚠️ Security Issue:** Same as above - applies to `public` role.

### 2.6 Clients Table (Agency Feature)
| Policy | Command | Role | Using Clause | Status |
|--------|---------|------|--------------|--------|
| Agencies can view own clients | SELECT | public | `auth.uid() = agency_id` | ⚠️ Issue |
| Agencies can manage own clients | ALL | public | `auth.uid() = agency_id` | ⚠️ Issue |

**⚠️ Security Issue:** Same as above - applies to `public` role.

### 2.7 Client Alerts Table
| Policy | Command | Role | Using Clause | Status |
|--------|---------|------|--------------|--------|
| Agencies can view own client alerts | SELECT | public | `EXISTS (SELECT 1 FROM clients c WHERE c.id = client_alerts.client_id AND c.agency_id = auth.uid())` | ⚠️ Issue |

**🚨 Critical Issue:** Only SELECT policy exists. Missing INSERT, UPDATE, DELETE policies.

### 2.8 Trends Table (Global Data)
| Policy | Command | Role | Using Clause | Status |
|--------|---------|------|--------------|--------|
| Authenticated users can view trends | SELECT | authenticated | `true` | ✅ OK |

**⚠️ Security Issue:** No write policies defined. Write operations are only possible via service_role or postgres. This is acceptable for a global data table, but should be documented.

### 2.9 Niches Table (Global Data)
| Policy | Command | Role | Using Clause | Status |
|--------|---------|------|--------------|--------|
| Authenticated users can view niches | SELECT | authenticated | `true` | ✅ OK |

**⚠️ Security Issue:** Same as above - no write policies (acceptable for seed data).

### 2.10 Trend Velocity History Table
| Policy | Command | Role | Using Clause | Status |
|--------|---------|------|--------------|--------|
| Authenticated users can view velocity history | SELECT | authenticated | `true` | ✅ OK |

**⚠️ Security Issue:** Same as above - no write policies (acceptable for system-populated data).

### 2.11 System Config Table
| Policy | Command | Role | Using Clause | Status |
|--------|---------|------|--------------|--------|
| Authenticated users can view system config | SELECT | authenticated | `true` | ✅ OK |

**⚠️ Security Issue:** No write policies - only service_role can modify. Acceptable for system configuration.

---

## 3. Security Issues Identified

### 3.1 🔴 HIGH RISK: Policies Apply to PUBLIC Role

**Description:** Multiple policies target the `public` role without explicit `TO authenticated` restriction:
- `profiles` (2 policies)
- `user_niches` (2 policies)
- `alert_integrations` (2 policies)
- `alerts` (1 policy)
- `bookmarks` (2 policies)
- `clients` (2 policies)
- `client_alerts` (1 policy)

**Risk:** Anonymous (unauthenticated) users can execute queries against these tables. While the `auth.uid()` check returns NULL for anon users (effectively returning no data), this exposes table structure and could lead to information leakage via timing attacks.

**Recommendation:** Update all policies to explicitly specify `TO authenticated`:
```sql
CREATE POLICY "Users can view own profile"
    ON public.profiles FOR SELECT
    TO authenticated  -- Add this
    USING (auth.uid() = id);
```

### 3.2 🟡 MEDIUM RISK: Missing INSERT Policy for Profiles

**Description:** The `profiles` table has no INSERT policy. User profiles are created via the `handle_new_user` trigger on auth.users.

**Risk:** Users cannot directly create profiles via API (which is likely intentional). However, if the trigger fails or is bypassed, users may end up without profiles.

**Recommendation:** Document this design decision. Consider adding an INSERT policy restricted to `service_role` for admin user creation:
```sql
CREATE POLICY "Service role can insert profiles"
    ON public.profiles FOR INSERT
    TO service_role
    WITH CHECK (true);
```

### 3.3 🟡 MEDIUM RISK: Incomplete Policy Coverage

**Tables with limited policies:**

| Table | Missing Operations | Impact |
|-------|-------------------|--------|
| `alerts` | INSERT, UPDATE, DELETE | Alerts can only be created via service_role |
| `client_alerts` | INSERT, UPDATE, DELETE | Client alerts can only be managed via service_role |

**Risk:** These are likely intentional (server-generated alerts), but the design should be documented.

### 3.4 🟢 LOW RISK: Global Data Tables Write Access

**Tables:** `trends`, `niches`, `trend_velocity_history`, `system_config`

**Current State:** Only SELECT policies exist; writes require service_role.

**Assessment:** ✅ **ACCEPTABLE** - These are system-populated tables that should not be modified by users.

### 3.5 🟢 LOW RISK: Function Security Configuration

**Functions Reviewed:**
| Function | Security Definer | Owner | Assessment |
|----------|-----------------|-------|------------|
| `handle_new_user` | ✅ Yes | postgres | ✅ Required for trigger to insert into profiles |
| `handle_updated_at` | ❌ No | postgres | ✅ Safe - simple timestamp update |

**Assessment:** ✅ **CORRECT** - The `handle_new_user` function correctly uses `SECURITY DEFINER` because it needs to insert into the `profiles` table from the auth schema trigger. The function has proper ACL permissions.

---

## 4. Auth Schema Review

### 4.1 Auth Tables
The auth schema contains standard Supabase auth tables:
- `users`, `identities`, `sessions`, `refresh_tokens`
- `mfa_factors`, `mfa_challenges`, `mfa_amr_claims`
- `sso_providers`, `sso_domains`, `saml_providers`
- `audit_log_entries`, `instances`, `schema_migrations`
- `one_time_tokens`, `flow_state`
- OAuth tables: `oauth_clients`, `oauth_authorizations`, `oauth_consents`, `oauth_client_states`

### 4.2 Auth Roles
| Role | Superuser | Create Role | Create DB | Inherit |
|------|-----------|-------------|-----------|---------|
| `authenticated` | No | No | No | Yes |
| `anon` | No | No | No | Yes |
| `service_role` | No | No | No | Yes |

**Assessment:** ✅ Standard Supabase role configuration.

---

## 5. Codebase Security Review

### 5.1 Service Role Key Handling
- Searched for hardcoded service_role keys in codebase
- Found only references in management scripts (expected)
- No exposed keys in `.env` or configuration files
- No keys committed to repository

**Assessment:** ✅ No exposed credentials found in codebase.

---

## 6. Recommendations

### Immediate Actions (High Priority)

1. **Fix PUBLIC Role Policies**
   ```sql
   -- Drop existing policies
   DROP POLICY IF EXISTS "Users can view own profile" ON public.profiles;
   DROP POLICY IF EXISTS "Users can update own profile" ON public.profiles;
   -- ... (repeat for all affected tables)

   -- Recreate with explicit TO authenticated
   CREATE POLICY "Users can view own profile"
       ON public.profiles FOR SELECT
       TO authenticated
       USING (auth.uid() = id);

   CREATE POLICY "Users can update own profile"
       ON public.profiles FOR UPDATE
       TO authenticated
       USING (auth.uid() = id);
   ```

2. **Add Missing service_role Policies**
   ```sql
   -- For alerts table
   CREATE POLICY "Service role can manage alerts"
       ON public.alerts FOR ALL
       TO service_role
       USING (true)
       WITH CHECK (true);

   -- For client_alerts table
   CREATE POLICY "Service role can manage client alerts"
       ON public.client_alerts FOR ALL
       TO service_role
       USING (true)
       WITH CHECK (true);
   ```

### Documentation Actions (Medium Priority)

3. **Document Security Model**
   - Document which tables are user-managed vs system-managed
   - Clarify service_role usage for background jobs
   - Create security policy reference in project docs

4. **Add RLS Policy Comments**
   ```sql
   COMMENT ON POLICY "Users can view own profile" ON public.profiles IS 
   'Allows authenticated users to view only their own profile. Users cannot see other users profiles.';
   ```

### Monitoring Actions (Ongoing)

5. **Set up RLS Policy Monitoring**
   - Monitor for policy violations in Supabase logs
   - Set up alerts for unusual query patterns
   - Regular quarterly audits of policy effectiveness

---

## 7. Migration File Analysis

### 001_initial_schema.sql
- ✅ RLS enabled on all tables
- ✅ Policies created with proper ownership checks
- ✅ Triggers for auto-updating timestamps
- ✅ Trigger for auto-creating user profiles
- ⚠️ Some policies missing explicit `TO authenticated` (noted above)

### 003_security_rls_fix.sql
- ✅ Correctly adds RLS to `system_config` table (missed in initial schema)
- ✅ Proper read-only policy for authenticated users
- ✅ Documents that writes are service_role only

---

## 8. Security Checklist

| Item | Status | Notes |
|------|--------|-------|
| RLS enabled on all tables | ✅ Pass | 11/11 tables |
| No anon write access | ✅ Pass | No anon write policies |
| Users see only own data | ✅ Pass | Proper auth.uid() checks |
| Service role documented | ⚠️ Partial | Needs explicit policies |
| No hardcoded keys | ✅ Pass | Clean codebase |
| Functions use SECURITY DEFINER correctly | ✅ Pass | handle_new_user configured |
| Policies restrict to authenticated | ❌ Fail | Most use PUBLIC role |
| Indexes on foreign keys | ✅ Pass | Good indexing strategy |

---

## 9. Conclusion

The TrendScope Supabase database has a **solid foundation** with RLS enabled on all tables and proper data ownership isolation. The main security concern is that most policies apply to the `public` role rather than explicitly restricting to `authenticated` users. While the `auth.uid()` check provides data-level protection, explicitly restricting policies to authenticated users is a defense-in-depth best practice.

**Risk Rating: MODERATE**
- Current state: Functional but not optimal
- No immediate critical vulnerabilities
- Recommended fixes are straightforward policy updates

**Next Steps:**
1. Apply migration to fix PUBLIC role policies (HIGH)
2. Add explicit service_role policies for server operations (MEDIUM)
3. Document security model for development team (MEDIUM)
4. Schedule follow-up audit in 3 months

---

*Report generated by Supabase Security Audit Agent*  
*MODEL: kimi-k2.5*  
*Date: 2026-02-17*
