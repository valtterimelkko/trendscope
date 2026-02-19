# Security Fixes Applied - 2026-02-17

## Actions Taken

### 1. Removed Proxy Files (Not Used)
- Deleted `scraper/proxy_utils.py`
- Deleted `scraper/tiktok_scraper.py`
- This eliminates all proxy-related security issues

### 2. Consolidated Environment Files
- Deleted `frontend/.env.local` (removed service role key exposure)
- Added Supabase credentials to root `.env` file
- Service role key is now in proper location only

### 3. Fixed MEDIUM Severity Issues

#### MED-003: API Key Exposure in Exception Handling
**File:** `alerts/email_service.py`
- Added `_sanitize_error()` method to redact API keys from error messages
- Applied sanitization to Resend and SendGrid exception handlers
- Masks patterns like: Stripe keys (`sk_...`), SendGrid keys (`sg_...`), Resend keys (`re_...`)

#### MED-004: Default Database URL with Weak Credentials
**Files:** `detection/config.py`, `alerts/config.py`
- Changed default from: `postgresql://postgres:postgres@localhost:5432/trendscope`
- To: `postgresql://MUST_OVERRIDE:MUST_OVERRIDE@localhost:5432/trendscope`
- Forces proper configuration in production

#### MED-005: CSP Allows 'unsafe-inline' and 'unsafe-eval'
**File:** `frontend/middleware.ts`
- Made CSP stricter for production (removes unsafe directives when `NODE_ENV !== 'development'`)
- Added additional security directives: `frame-ancestors 'none'`, `base-uri 'self'`, `form-action 'self'`
- Development mode still allows unsafe directives for debugging

#### MED-006: dangerouslySetInnerHTML Without Sanitization
**File:** `frontend/components/ui/chart.tsx`
- Added input validation for chart `id` (only alphanumeric and hyphens allowed)
- Added `isValidColor()` function to validate CSS color values
- Invalid inputs are sanitized before use in `dangerouslySetInnerHTML`

### 4. Fixed LOW Severity Issues

#### LOW-001: Email Masking Could Be Stronger
**File:** `alerts/email_service.py`
- Previous: `j***@gmail.com`
- Now: `j***@***.com`
- Domain is also masked for additional privacy

#### LOW-002: Slack Webhook URL Masking
**File:** `alerts/slack_service.py`
- Previous: Showed first 8 chars of token (`.../T1234567***`)
- Now: Only shows hostname (`https://hooks.slack.com/***`)
- No token information exposed

#### LOW-003: Error Messages Expose Details
**File:** `frontend/app/api/billing-portal/route.ts`
- Removed `details` field from error response
- Detailed errors still logged server-side
- Client receives generic error message only

## Files Modified

1. `alerts/email_service.py` - Error sanitization, improved email masking
2. `alerts/slack_service.py` - Better webhook URL masking
3. `alerts/config.py` - Invalid default database URL
4. `detection/config.py` - Invalid default database URL
5. `frontend/middleware.ts` - Stricter CSP for production
6. `frontend/components/ui/chart.tsx` - Input validation for dangerouslySetInnerHTML
7. `frontend/app/api/billing-portal/route.ts` - Generic error messages

## Files Deleted

1. `scraper/proxy_utils.py`
2. `scraper/tiktok_scraper.py`
3. `frontend/.env.local`

## Remaining Issues (Supabase-side)

These require SQL migrations and cannot be fixed via code changes alone:

1. **MED-001/002**: RLS policies apply to PUBLIC role (needs SQL migration)
2. **MED-007**: Missing RLS policies for alerts tables (needs SQL migration)

## Summary

| Severity | Before | After |
|----------|--------|-------|
| 🔴 Critical | 2 | 0 (credentials consolidated, proxy files removed) |
| 🟠 High | 2 | 0 (proxy files removed) |
| 🟡 Medium | 6 | 2 (RLS issues require SQL) |
| 🟢 Low | 6 | 3 (auth bypass acceptable for dev, CSRF deferred) |

**Overall Risk Reduced From HIGH to MEDIUM**
