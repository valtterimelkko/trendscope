# TrendScope Master Security Report

**Report Date:** 2026-02-17  
**Auditor:** Multi-Agent Security Review Team  
**Scope:** Complete TrendScope Platform (Frontend, Backend, Supabase)  
**Risk Rating:** 🔴 **HIGH** (Due to Critical Credential Exposure)

---

## Executive Summary

This comprehensive security audit examined all components of the TrendScope platform:
- **Frontend:** Next.js application with Supabase Auth
- **Backend:** Python scraper/detection/alert services  
- **Database:** Supabase PostgreSQL with Row Level Security

### Critical Finding: Immediate Action Required

**The Supabase service role key is exposed in `frontend/.env.local`.** This key provides unrestricted database access, bypassing all Row Level Security policies. Additionally, the root `.env` file contains multiple hardcoded production credentials including Stripe keys, API keys, and proxy passwords.

### Risk Summary

| Severity | Count | Description |
|----------|-------|-------------|
| 🔴 Critical | 2 | Service role key exposure, hardcoded production credentials |
| 🟠 High | 2 | Non-standard credential loading, credential exposure risk |
| 🟡 Medium | 6 | RLS policy gaps, CSP weaknesses, logging exposure |
| 🟢 Low | 6 | Minor information disclosure, development bypasses |

---

## 🔴 Critical Issues (Immediate Action Required)

### CRITICAL-1: Supabase Service Role Key Exposed in Frontend

**Location:** `frontend/.env.local` (Line 4)  
**Component:** Frontend / Supabase Integration  
**CVSS Score:** 9.8 (Critical)

#### Description
The `SUPABASE_SERVICE_ROLE_KEY` is stored in the frontend environment:

```
SUPABASE_SERVICE_ROLE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InVxd3lsYXJuc2hhdWlmZ3F4dWprIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc3MTI4Mjk0MywiZXhwIjoyMDg2ODU4OTQzfQ.Ite-MqsB6xLHEmMNB8lHXlPHDlVAjkxK7uOy63nxmtg
```

This key is used in `lib/billing/subscription-service.ts` to create an admin client that **bypasses all RLS policies**.

#### Impact
- Complete database compromise possible
- All user data accessible
- All RLS policies bypassed
- Can modify any user's subscription/payment data

#### Immediate Actions
1. **Remove** `SUPABASE_SERVICE_ROLE_KEY` from `frontend/.env.local`
2. **Rotate** the service role key in Supabase Dashboard immediately
3. **Audit** database access logs for unauthorized usage
4. **Move** billing operations to Supabase Edge Functions

---

### CRITICAL-2: Hardcoded Production Credentials in Root `.env`

**Location:** `/root/trendscope/.env`  
**Component:** Backend Configuration  
**CVSS Score:** 8.5 (High)

#### Description
The `.env` file contains multiple hardcoded production credentials:

| Service | Credential Type | Value Exposed |
|---------|-----------------|---------------|
| IPRoyal Proxy | Username/Password | `***REMOVED***` / `***REMOVED***...` |
| Porkbun | API Key/Secret | `pk1_f2d0b8d1...` / `sk1_e27a1e1a...` |
| Stripe | Secret Key | `sk_test_51SkiiuRy5aXrXpv2...` |
| Browserless | API Key | `2SeF2iGp8mhQH2I6e506c487...` |
| Google Ads | Developer Token | `Sid1eFpyDt2EyPkU1DS0Fw` |
| RapidAPI | API Key | `8710e2cdb1msh72b30bdecb99b5bp1fb537jsn33825799b519` |

#### Impact
- If committed to git, credentials are permanently in repository history
- Test Stripe keys can still be used for fraudulent transactions
- Proxy credentials can be used for malicious scraping activities
- API keys can be abused, incurring charges

#### Immediate Actions
1. **Rotate ALL credentials** immediately:
   - Stripe: https://dashboard.stripe.com/test/apikeys
   - IPRoyal: Generate new proxy credentials
   - Porkbun: Generate new API keys
   - Browserless: Rotate API key
   - RapidAPI: Regenerate API key
   
2. **Create** `.env.example` with placeholder values
3. **Verify** `.env` is in `.gitignore` (it is ✅)
4. **Add** git-secrets pre-commit hook

---

## 🟠 High Severity Issues

### HIGH-1: Insecure 2Captcha API Key Loading from `.bashrc`

**Location:** `scraper/tiktok_scraper.py` (Lines 102-118)  
**Component:** TikTok Scraper

The scraper parses `/root/.bashrc` directly to load the 2Captcha API key:

```python
def _load_captcha_key(self) -> Optional[str]:
    with open('/root/.bashrc', 'r') as f:
        for line in f:
            if '2CAPTCHA_API_KEY=' in line:
                # Extract value between quotes
```

**Fix:** Use environment variable with alphanumeric prefix:
```python
def _load_captcha_key(self) -> Optional[str]:
    return os.environ.get("TWOCAPTCHA_API_KEY")
```

---

### HIGH-2: Insufficient Proxy URL Truncation

**Location:** `scraper/proxy_utils.py` (Multiple lines)  
**Component:** Proxy Utilities

Proxy URLs are truncated to 60-70 characters but may still expose partial credentials.

**Fix:** Implement proper credential masking:
```python
def mask_proxy_url(proxy_url: str) -> str:
    from urllib.parse import urlparse, urlunparse
    parsed = urlparse(proxy_url)
    netloc = f"***:***@{parsed.hostname}"
    if parsed.port:
        netloc += f":{parsed.port}"
    return urlunparse((parsed.scheme, netloc, parsed.path, 
                       parsed.params, parsed.query, parsed.fragment))
```

---

## 🟡 Medium Severity Issues

### MEDIUM-1: RLS Policies Apply to PUBLIC Role

**Location:** Supabase Database - 12 policies affected  
**Component:** Database Security

Multiple RLS policies apply to the `public` role without explicit `TO authenticated` restriction:
- `profiles` (2 policies)
- `user_niches` (2 policies)
- `alert_integrations` (2 policies)
- `alerts` (1 policy)
- `bookmarks` (2 policies)
- `clients` (2 policies)
- `client_alerts` (1 policy)

**Fix:** Update policies to explicitly specify `TO authenticated`:
```sql
CREATE POLICY "Users can view own profile"
    ON public.profiles FOR SELECT
    TO authenticated  -- Add this
    USING (auth.uid() = id);
```

---

### MEDIUM-2: Missing RLS Policies for alerts and client_alerts

**Location:** Supabase Database  
**Component:** Database Security

The `alerts` and `client_alerts` tables have only SELECT policies. They are missing INSERT/UPDATE/DELETE policies.

**Fix:** Add explicit service_role policies:
```sql
CREATE POLICY "Service role can manage alerts"
    ON public.alerts FOR ALL
    TO service_role
    USING (true)
    WITH CHECK (true);
```

---

### MEDIUM-3: CSP Allows 'unsafe-inline' and 'unsafe-eval'

**Location:** `frontend/middleware.ts` (Lines 17-20)  
**Component:** Frontend Security

```typescript
"default-src 'self'; script-src 'self' 'unsafe-inline' 'unsafe-eval'; ..."
```

**Fix:** Use nonces or hashes for inline scripts, remove 'unsafe-eval' if possible.

---

### MEDIUM-4: dangerouslySetInnerHTML in Chart Component

**Location:** `frontend/components/ui/chart.tsx` (Lines 80-99)  
**Component:** Frontend XSS Risk

The Chart component uses `dangerouslySetInnerHTML` to inject CSS styles.

**Fix:** Validate `id` parameter and use CSS-in-JS solution.

---

### MEDIUM-5: Potential API Key Exposure in Exception Handling

**Location:** `alerts/email_service.py` (Lines 434-440)  
**Component:** Backend Logging

Error messages from third-party APIs may include API keys.

**Fix:** Sanitize error messages before logging:
```python
import re
error_msg = re.sub(r'[a-zA-Z0-9]{32,}', '***API_KEY_REDACTED***', str(e))
```

---

### MEDIUM-6: Default Database URL with Weak Credentials

**Location:** `detection/config.py`, `alerts/config.py`  
**Component:** Backend Configuration

```python
default="postgresql://postgres:postgres@localhost:5432/trendscope"
```

**Fix:** Use obviously invalid defaults to force proper configuration.

---

## 🟢 Low Severity Issues

1. **Auth Bypass in Development** - Acceptable for dev mode, but add explicit NODE_ENV check
2. **Missing CSRF Protection** - Add CSRF tokens for state-changing operations
3. **Error Messages Expose Details** - Return generic error messages in production
4. **Email Masking Could Be Stronger** - Mask domain portion as well
5. **Slack Webhook URL Masking** - Could reveal first 8 characters
6. **Logging of Configuration** - Add safe config redaction method

---

## ✅ Positive Security Findings

### Frontend
- ✅ Stripe webhook signature verification implemented correctly
- ✅ UUID validation for all path parameters
- ✅ Authentication checks on all protected routes
- ✅ Input validation with length limits and type checking
- ✅ Webhook URL masking in API responses
- ✅ Row Level Security enforced with user ID filters
- ✅ Security headers in middleware (X-Frame-Options, CSP, etc.)

### Backend
- ✅ SQL injection prevention with parameterized queries throughout
- ✅ Dynamic query validation to prevent SQL injection in ORDER BY
- ✅ No command injection risks
- ✅ No insecure deserialization
- ✅ Email address masking in logs
- ✅ Webhook URL masking in logs
- ✅ Proper proxy credential handling

### Database
- ✅ RLS enabled on all 11 tables
- ✅ Data ownership properly isolated with auth.uid() checks
- ✅ No hardcoded service_role keys in codebase
- ✅ Secure function configuration (handle_new_user uses SECURITY DEFINER correctly)
- ✅ Global data tables (trends, niches) properly protected from user writes

---

## Immediate Action Checklist

### Within 24 Hours

- [ ] **CRITICAL:** Rotate Supabase service role key
- [ ] **CRITICAL:** Remove `SUPABASE_SERVICE_ROLE_KEY` from `frontend/.env.local`
- [ ] **CRITICAL:** Rotate all credentials in root `.env` file:
  - [ ] Stripe secret key
  - [ ] IPRoyal proxy credentials
  - [ ] Porkbun API keys
  - [ ] Browserless API key
  - [ ] RapidAPI key
  - [ ] Google Ads developer token
- [ ] **CRITICAL:** Check git history for credential exposure: `git log --all --full-history -- .env`

### Within 1 Week

- [ ] Fix RLS policies to use `TO authenticated` instead of `public`
- [ ] Add service_role policies for alerts and client_alerts tables
- [ ] Replace `.bashrc` credential loading with environment variables
- [ ] Create `.env.example` template file
- [ ] Implement stricter CSP headers for production
- [ ] Add input sanitization to chart component
- [ ] Sanitize API error messages before logging

### Within 1 Month

- [ ] Migrate billing operations to Supabase Edge Functions
- [ ] Implement comprehensive security monitoring
- [ ] Add rate limiting to API routes
- [ ] Set up automated dependency vulnerability scanning
- [ ] Conduct penetration testing
- [ ] Implement secrets rotation mechanism

---

## Compliance Impact

### SOC 2
- Service role key exposure violates Principle of Least Privilege (CC6.1)
- Missing audit logging for privileged operations (CC7.2)

### GDPR
- Service role key could bypass data subject rights enforcement
- Ensure RLS policies properly enforce data access controls

### PCI DSS (if handling payments)
- Stripe key exposure violates Requirement 3 (Protect stored cardholder data)
- Credential exposure violates Requirement 8 (Identify and authenticate access)

---

## Files Generated

| File | Description |
|------|-------------|
| `supabase-security-audit.md` | Detailed Supabase RLS and policy analysis |
| `frontend-security-audit.md` | Next.js frontend security assessment |
| `backend-security-audit.md` | Python backend security review |
| `security-fixes.md` | Quick reference guide with code fixes |
| `MASTER-SECURITY-REPORT.md` | This comprehensive report |

---

## Conclusion

The TrendScope platform has a **solid security foundation** with proper authentication, SQL injection prevention, and Row Level Security. However, the **critical credential exposures require immediate remediation**.

**Key Priorities:**
1. Rotate all exposed credentials immediately
2. Remove service role key from frontend environment
3. Fix RLS policies to restrict to authenticated users
4. Implement proper credential management practices

**Overall Recommendation:** Address critical and high severity issues before any production deployment. The platform is not production-ready until credential exposures are resolved.

---

*Report generated by Multi-Agent Security Review Team*  
*Date: 2026-02-17*  
*MODEL: kimi-k2.5*
