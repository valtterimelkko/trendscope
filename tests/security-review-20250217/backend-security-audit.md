# TrendScope Backend Security Audit Report

**Date:** 2026-02-17  
**Auditor:** Backend Security Auditor  
**Scope:** Python backend components (scraper, detection, alerts, monitoring)  
**Model:** kimi-k2.5

---

## Executive Summary

This security audit examined the TrendScope Python backend components for common security vulnerabilities including credential handling, SQL injection, command injection, and sensitive data exposure. 

**Overall Risk Level:** MEDIUM  
**Critical Issues:** 0  
**High Severity:** 2  
**Medium Severity:** 4  
**Low Severity:** 3

The primary concerns involve non-standard credential loading patterns and potential information leakage through logging. No SQL injection or command injection vulnerabilities were found. The codebase generally follows secure practices for database operations and uses parameterized queries throughout.

---

## Critical Issues

*No critical issues identified.*

---

## High Severity Findings

### HIGH-001: Insecure 2Captcha API Key Loading from .bashrc

**File:** `scraper/tiktok_scraper.py`  
**Lines:** 102-118  
**Severity:** HIGH

**Issue Description:**
The application loads the 2Captcha API key by parsing `/root/.bashrc` directly. This is a significant security anti-pattern because:

1. `.bashrc` is a shell configuration file that may contain many sensitive values
2. Shell history and environment variables could leak the key
3. No validation or sanitization of the parsed content
4. Unusual and unexpected credential storage location

**Code Snippet:**
```python
def _load_captcha_key(self) -> Optional[str]:
    """Load 2captcha key from .bashrc (since env var starts with number)."""
    # Try .bashrc
    try:
        with open('/root/.bashrc', 'r') as f:
            for line in f:
                line = line.strip()
                if '2CAPTCHA_API_KEY=' in line:
                    # Extract value between quotes
                    parts = line.split('=', 1)
                    if len(parts) == 2:
                        value = parts[1].strip('"\'')
                        return value
    except:
        pass
    
    return None
```

**Recommendation:**
```python
def _load_captcha_key(self) -> Optional[str]:
    """Load 2captcha key from environment variable."""
    # Use a prefixed env var name that doesn't start with a number
    # e.g., CAPTCHA_API_KEY_2C instead of 2CAPTCHA_API_KEY
    import os
    return os.environ.get("CAPTCHA_API_KEY_2C") or os.environ.get("TWOCAPTCHA_API_KEY")
```

**Rationale:** Environment variables can use alphanumeric prefixes. Use `TWOCAPTCHA_API_KEY` or `CAPTCHA_API_KEY_2C` instead of trying to read from `.bashrc`.

---

### HIGH-002: Hardcoded Credentials in .env File

**File:** `.env` (root of project)  
**Severity:** HIGH

**Issue Description:**
The `.env` file contains multiple hardcoded production credentials:

```
PROXY_USERNAME=***REMOVED***
PROXY_PASSWORD=***REMOVED***
PORKBUN_API_KEY=pk1_f2d0b8d198d21579479a841a1c7ccfa61b41865136ac963fd067da1aeb07df21
PORKBUN_API_SECRET=sk1_e27a1e1afc236465f02d14722d9746e75d60e81f6a4e2e5989ecd8baf876289e
STRIPE_SECRET_KEY=sk_test_51SkiiuRy5aXrXpv2OWzmHR5q4lzkSHnjxUU6a2J9kM908RI1l1h7nyOp7VKJCAP7Nud2UnWQkPvYlIQvd5niUw2J00iKEZ26MO
RAPIDAPI_KEY=8710e2cdb1msh72b30bdecb99b5bp1fb537jsn33825799b519
```

**Risk:**
- If committed to git, these credentials are permanently exposed in repository history
- Even with `.gitignore`, file permissions or backups could leak credentials
- Test Stripe keys can still be used for abuse

**Recommendation:**
1. Immediately rotate ALL exposed credentials
2. Use `.env.example` with placeholder values for version control
3. Store production credentials in a secrets manager (AWS Secrets Manager, HashiCorp Vault, etc.)
4. Add `.env` to `.gitignore` if not already present
5. Consider using a pre-commit hook like `git-secrets` to prevent accidental commits

---

## Medium Severity Findings

### MED-001: Insufficient Proxy URL Truncation May Leak Credentials

**File:** `scraper/proxy_utils.py`  
**Lines:** 29, 139, 236, 269  
**Severity:** MEDIUM

**Issue Description:**
Multiple locations truncate proxy URLs to 60-70 characters for display/logging, but this may still expose partial credentials:

**Code Snippets:**
```python
# Line 29
"url": proxy_url[:60] + "..." if len(proxy_url) > 60 else proxy_url,

# Line 139
"proxy_url": proxy_url[:60] + "..." if len(proxy_url) > 60 else proxy_url,

# Line 236
status["proxy_url"] = proxy_url[:60] + "..." if len(proxy_url) > 60 else proxy_url,

# Line 269
print(f"\n📋 Proxy URL: {proxy_url[:70]}...")
```

**Example Risk:**
A proxy URL like `http://username:password@host:port` could expose:
- Full username if short enough
- Partial password depending on lengths

For example, `http://user:mysecretpassword123@proxy.example.com:8080` truncated to 60 chars might reveal `http://user:mysecretpassword123@proxy.example.com:80`

**Recommendation:**
```python
def mask_proxy_url(proxy_url: str) -> str:
    """Completely mask credentials in proxy URL."""
    from urllib.parse import urlparse, urlunparse
    
    try:
        parsed = urlparse(proxy_url)
        # Replace credentials with ***
        netloc = f"***:***@{parsed.hostname}"
        if parsed.port:
            netloc += f":{parsed.port}"
        return urlunparse((
            parsed.scheme, netloc, parsed.path, 
            parsed.params, parsed.query, parsed.fragment
        ))
    except Exception:
        return "***masked***"
```

---

### MED-002: Proxy Credential Exposure Through Diagnostics

**File:** `scraper/proxy_utils.py`  
**Lines:** 64, 69  
**Severity:** MEDIUM

**Issue Description:**
The `validate_proxy_url` function exposes credential metadata through diagnostics:

```python
if not parsed.username:
    result["issues"].append("Missing username")
else:
    result["components"]["username"] = parsed.username[:10] + "..."  # Line 64

if not parsed.password:
    result["issues"].append("Missing password")
else:
    result["components"]["password_length"] = len(parsed.password)  # Line 69
```

While the username is partially masked, exposing `password_length` could aid attackers in brute-force attempts by revealing the credential complexity.

**Recommendation:**
```python
if not parsed.username:
    result["issues"].append("Missing username")
else:
    result["components"]["has_username"] = True  # Don't expose even partial username

if not parsed.password:
    result["issues"].append("Missing password")
else:
    result["components"]["has_password"] = True  # Don't expose password length
```

---

### MED-003: Potential API Key Exposure in Exception Handling

**File:** `alerts/email_service.py`  
**Lines:** 434-440, 479-485  
**Severity:** MEDIUM

**Issue Description:**
Email service API calls may expose API keys in exception logs:

```python
except Exception as e:
    logger.error(
        "email_resend_failed",
        to=self._mask_email(to_email),
        error=str(e)  # Could contain API key in error message
    )
    return False
```

Third-party API error messages (Resend, SendGrid) sometimes include the API key in error responses for authentication failures.

**Recommendation:**
```python
except Exception as e:
    error_msg = str(e)
    # Sanitize error messages to remove potential API keys
    import re
    # Mask potential API key patterns
    error_msg = re.sub(r'[a-zA-Z0-9]{32,}', '***API_KEY_REDACTED***', error_msg)
    logger.error(
        "email_resend_failed",
        to=self._mask_email(to_email),
        error=error_msg
    )
```

---

### MED-004: Default Database URL with Weak Credentials

**File:** `detection/config.py` (line 27), `alerts/config.py` (line 37), `scraper/config.py` (line 27)  
**Severity:** MEDIUM

**Issue Description:**
Default database URLs use weak credentials:

```python
database_url: str = Field(
    default="postgresql://postgres:postgres@localhost:5432/trendscope",
    description="PostgreSQL connection URL for trend persistence"
)
```

**Risk:**
- If used in production without override, creates a known credential attack vector
- Default credentials are common in automated attack scanners

**Recommendation:**
```python
database_url: str = Field(
    default="postgresql://user:pass@localhost:5432/trendscope",
    description="PostgreSQL connection URL (MUST be overridden in production)"
)
```

Use obviously invalid defaults to force proper configuration.

---

## Low Severity Findings

### LOW-001: Email Address Masking Could Be Stronger

**File:** `alerts/email_service.py`  
**Lines:** 487-502  
**Severity:** LOW

**Issue Description:**
Current email masking preserves domain information which could be sensitive:

```python
def _mask_email(self, email: str) -> str:
    if not email or "@" not in email:
        return "<invalid>"

    local, domain = email.split("@", 1)
    masked_local = local[0] + "***" if len(local) > 1 else "***"

    return f"{masked_local}@{domain}"  # Domain is fully exposed
```

**Recommendation:**
```python
def _mask_email(self, email: str) -> str:
    if not email or "@" not in email:
        return "<invalid>"

    local, domain = email.split("@", 1)
    masked_local = local[0] + "***" if len(local) > 1 else "***"
    # Also mask domain for privacy
    domain_parts = domain.split(".")
    if len(domain_parts) > 1:
        masked_domain = f"***.{domain_parts[-1]}"
    else:
        masked_domain = "***"

    return f"{masked_local}@{masked_domain}"
```

---

### LOW-002: Slack Webhook URL Masking Could Reveal More Than Intended

**File:** `alerts/slack_service.py`  
**Lines:** 462-479  
**Severity:** LOW

**Issue Description:**
The current masking implementation:

```python
def _mask_webhook_url(self, url: str) -> str:
    if not url:
        return "<empty>"

    # Show only the workspace part
    parts = url.split("/")
    if len(parts) >= 5:
        return f".../{parts[4][:8]}***"

    return "***masked***"
```

This exposes the first 8 characters of the webhook token, which could theoretically aid in identification.

**Recommendation:**
```python
def _mask_webhook_url(self, url: str) -> str:
    if not url:
        return "<empty>"

    from urllib.parse import urlparse
    try:
        parsed = urlparse(url)
        # Only show the service name
        return f"{parsed.scheme}://{parsed.netloc}/***"
    except Exception:
        return "***masked***"
```

---

### LOW-003: Logging of Configuration on Startup

**File:** Multiple config files  
**Severity:** LOW

**Issue Description:**
If any config module logs its full configuration at startup (not currently observed but common pattern), credentials could be exposed in logs.

**Recommendation:**
Add a method to create a safe, redacted version of config for logging:

```python
def get_safe_config(self) -> dict:
    """Return config with sensitive fields redacted."""
    import copy
    safe = copy.deepcopy(self.model_dump())
    sensitive_fields = ['api_key', 'password', 'secret', 'token', 'key']
    
    def redact_sensitive(obj, path=""):
        if isinstance(obj, dict):
            for k, v in obj.items():
                new_path = f"{path}.{k}" if path else k
                if any(s in k.lower() for s in sensitive_fields):
                    obj[k] = "***REDACTED***"
                else:
                    redact_sensitive(v, new_path)
    
    redact_sensitive(safe)
    return safe
```

---

## Positive Security Findings

### SEC-001: Proper SQL Injection Prevention

**File:** `detection/persistence.py`  
**Status:** SECURE

The codebase uses asyncpg with parameterized queries throughout, preventing SQL injection:

```python
# Line 94-100 - Parameterized query
row = await conn.fetchrow(
    """
    SELECT * FROM trends
    WHERE type = $1 AND platform_id = $2
    """,
    trend_type.value,
    platform_id
)
```

All database operations use proper parameterization with `$1`, `$2`, etc.

### SEC-002: SQL Injection Prevention in Dynamic Queries

**File:** `detection/persistence.py`  
**Lines:** 167-174  
**Status:** SECURE

The `get_trends` method properly validates the `order_by` parameter:

```python
# Validate order_by to prevent SQL injection
valid_columns = {
    "velocity_score", "saturation_percent", "first_detected_at",
    "video_count_current", "growth_rate", "name"
}
order_parts = order_by.split()
if order_parts[0] not in valid_columns:
    order_by = "velocity_score DESC"
```

### SEC-003: No Command Injection Risks

**File:** All files  
**Status:** SECURE

No use of `os.system()`, `subprocess.call()`, or similar functions with user input found.

### SEC-004: No Insecure Deserialization

**File:** All files  
**Status:** SECURE

Uses Pydantic models for data validation and `json` module for JSON serialization (safe).

### SEC-005: Proper Webhook URL Masking in Logs

**File:** `alerts/slack_service.py`  
**Lines:** 364-417  
**Status:** SECURE

The Slack service consistently uses masked URLs in all log statements:

```python
# Line 365
masked_url = self._mask_webhook_url(webhook_url)

# Lines 376-380
logger.info(
    "slack_delivery_success",
    masked_url=masked_url,
    attempt=attempt
)
```

### SEC-006: Secure Proxy URL Parsing

**File:** `scraper/tiktok_scraper.py`  
**Lines:** 277-291  
**Status:** SECURE

Proxy credentials are properly extracted without logging:

```python
def _parse_proxy_config(self) -> Optional[Dict[str, str]]:
    if not self.proxy_url:
        return None
    
    try:
        parsed = urlparse(self.proxy_url)
        return {
            "server": f"{parsed.scheme}://{parsed.hostname}:{parsed.port}",
            "username": parsed.username,
            "password": parsed.password
        }
    except Exception as e:
        logger.error(f"Failed to parse proxy URL: {e}")
        return None
```

---

## Compliance and Best Practices

### 1. Environment Variable Usage
- ✅ Proper use of environment variables for configuration
- ✅ Pydantic settings with validation
- ⚠️ Non-standard credential storage (.bashrc) should be eliminated

### 2. Database Security
- ✅ Parameterized queries throughout
- ✅ Connection pooling with limits
- ✅ No SQL injection vulnerabilities found

### 3. External API Security
- ✅ API keys loaded from environment
- ⚠️ Error messages may leak API keys (sanitize recommended)
- ✅ No hardcoded keys in source code

### 4. Logging Security
- ✅ Email addresses masked in logs
- ✅ Webhook URLs masked in logs
- ⚠️ Proxy URL truncation could be more aggressive
- ⚠️ No central PII/sensitive data redaction

### 5. Secret Management
- ❌ Multiple credentials in `.env` file
- ❌ `.env` file contains production-ready secrets
- ❌ No evidence of secrets rotation mechanism
- ❌ No evidence of secrets encryption at rest

---

## Recommendations Summary

| Priority | Action | Estimated Effort |
|----------|--------|------------------|
| HIGH | Rotate all credentials exposed in `.env` | 2 hours |
| HIGH | Replace `.bashrc` credential loading with env vars | 1 hour |
| HIGH | Implement `.env.example` and git-secrets | 1 hour |
| MEDIUM | Implement proper proxy URL masking | 2 hours |
| MEDIUM | Sanitize API error messages before logging | 2 hours |
| MEDIUM | Change default database credentials to invalid values | 30 minutes |
| LOW | Strengthen email and webhook masking | 1 hour |
| LOW | Implement central PII redaction utility | 3 hours |

---

## Appendix: Files Audited

1. `scraper/proxy_utils.py` - Proxy credential handling ✅
2. `scraper/tiktok_scraper.py` - API key management (2captcha) ✅
3. `scraper/config.py` - Configuration ✅
4. `scraper/tiktok_scraper7_client.py` - RapidAPI client ✅
5. `detection/persistence.py` - Database operations ✅
6. `detection/config.py` - Database URL handling ✅
7. `alerts/email_service.py` - Email API key handling ✅
8. `alerts/slack_service.py` - Webhook security ✅
9. `alerts/config.py` - Alert configuration ✅
10. `monitoring/config.py` - Monitoring configuration ✅
11. `alerts/models.py` - Data models ✅
12. `detection/models.py` - Data models ✅
13. `.env` - Environment configuration ✅

---

## Conclusion

The TrendScope backend demonstrates good security practices in database operations, SQL injection prevention, and parameterized queries. The primary concerns are around credential management and potential information leakage through logging. Addressing the HIGH severity findings should be the immediate priority, followed by implementing stronger masking and sanitization practices.

**Signed:** Backend Security Auditor  
**Date:** 2026-02-17
