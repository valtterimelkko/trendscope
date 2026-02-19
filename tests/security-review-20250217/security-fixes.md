# Security Fixes - Quick Reference

## Immediate Actions Required

### 1. Rotate ALL Exposed Credentials (HIGH PRIORITY)

These credentials were exposed in `.env` and must be rotated immediately:

```bash
# IPRoyal Proxy
# Rotate at: https://dashboard.iproyal.com/
# Generate new residential proxy credentials

# Porkbun API
# Rotate at: https://porkbun.com/account/login
# Generate new API keys

# Stripe Test Keys
# Rotate at: https://dashboard.stripe.com/test/apikeys
# Note: These are test keys but can still be abused

# RapidAPI
# Rotate at: https://rapidapi.com/developer/dashboard
# Generate new API keys for TikTok-Scraper7

# Browserless
# Rotate at: https://www.browserless.io/account
# Generate new API key
```

### 2. Fix 2Captcha API Key Loading (HIGH PRIORITY)

**File:** `scraper/tiktok_scraper.py`

Replace lines 102-118 with:

```python
def _load_captcha_key(self) -> Optional[str]:
    """Load 2captcha key from environment variable.
    
    The API key should be set as TWOCAPTCHA_API_KEY or CAPTCHA_KEY_2C
    to avoid issues with environment variables starting with numbers.
    """
    import os
    # Try multiple naming conventions for flexibility
    return (
        os.environ.get("TWOCAPTCHA_API_KEY") or
        os.environ.get("CAPTCHA_KEY_2C") or
        os.environ.get("_2CAPTCHA_API_KEY")  # Some shells allow this
    )
```

**Then update your `.env` file:**
```bash
# Remove from .bashrc!
# Add to .env:
TWOCAPTCHA_API_KEY=your_actual_key_here
```

### 3. Implement Proper Proxy URL Masking (MEDIUM PRIORITY)

**File:** `scraper/proxy_utils.py`

Add this function after the imports:

```python
def mask_proxy_url(proxy_url: str) -> str:
    """Completely mask credentials in proxy URL.
    
    Args:
        proxy_url: Full proxy URL with credentials
        
    Returns:
        URL with credentials fully masked
    """
    if not proxy_url:
        return "<empty>"
    
    try:
        parsed = urlparse(proxy_url)
        if parsed.username or parsed.password:
            # Replace credentials with ***:***
            netloc = f"***:***@{parsed.hostname}"
            if parsed.port:
                netloc += f":{parsed.port}"
            return f"{parsed.scheme}://{netloc}"
        return proxy_url
    except Exception:
        return "***masked***"
```

Then replace all instances of URL truncation:
```python
# Replace this:
proxy_url[:60] + "..."

# With this:
mask_proxy_url(proxy_url)
```

### 4. Update Diagnostic Info Exposure (MEDIUM PRIORITY)

**File:** `scraper/proxy_utils.py`

Replace lines 60-82 in `validate_proxy_url()`:

```python
# Check credentials - only confirm presence, not values
if not parsed.username:
    result["issues"].append("Missing username")
else:
    result["components"]["has_username"] = True

if not parsed.password:
    result["issues"].append("Missing password")
else:
    result["components"]["has_password"] = True
    
    # Check for session lifetime indicator (safe to expose)
    if "lifetime-" in parsed.password:
        result["warnings"].append(
            "Password contains 'lifetime-' - these may be temporary session "
            "credentials that expire (e.g., lifetime-30m = 30 minutes)"
        )
    
    # Check for session ID (safe to expose that session exists)
    if "_session-" in parsed.password:
        result["warnings"].append(
            "Password contains session ID - session may have expired"
        )
```

### 5. Sanitize API Error Messages (MEDIUM PRIORITY)

**File:** `alerts/email_service.py`

Add this helper function:

```python
def _sanitize_error(self, error: str) -> str:
    """Sanitize error messages to remove potential API keys."""
    import re
    
    # Mask common API key patterns
    patterns = [
        (r'[a-zA-Z0-9]{32,64}', '***KEY_REDACTED***'),  # Generic long keys
        (r'sk_[a-zA-Z0-9]{24,}', '***STRIPE_KEY_REDACTED***'),  # Stripe keys
        (r'[a-z]{2}1_[a-f0-9]{64,}', '***API_KEY_REDACTED***'),  # Porkbun pattern
        (r'[a-f0-9]{32}-[a-f0-9]{8}', '***API_KEY_REDACTED***'),  # Some API patterns
    ]
    
    sanitized = error
    for pattern, replacement in patterns:
        sanitized = re.sub(pattern, replacement, sanitized)
    
    return sanitized
```

Then use it in exception handlers:
```python
except Exception as e:
    logger.error(
        "email_resend_failed",
        to=self._mask_email(to_email),
        error=self._sanitize_error(str(e))
    )
```

### 6. Update Default Database URL (LOW PRIORITY)

**Files:** `detection/config.py`, `alerts/config.py`, `scraper/config.py`

Change:
```python
database_url: str = Field(
    default="postgresql://postgres:postgres@localhost:5432/trendscope",
    description="PostgreSQL connection URL for trend persistence"
)
```

To:
```python
database_url: str = Field(
    default="postgresql://MUST_OVERRIDE:MUST_OVERRIDE@localhost:5432/trendscope",
    description="PostgreSQL connection URL (MUST be overridden in production)"
)
```

---

## Security Checklist

- [ ] Rotate all exposed credentials
- [ ] Remove 2CAPTCHA_API_KEY from .bashrc
- [ ] Add TWOCAPTCHA_API_KEY to .env
- [ ] Implement proxy URL masking function
- [ ] Update all proxy URL logging to use masking
- [ ] Remove credential metadata from diagnostics
- [ ] Add error message sanitization
- [ ] Update default database credentials
- [ ] Add .env.example file
- [ ] Install git-secrets or similar pre-commit hook
- [ ] Verify .env is in .gitignore
- [ ] Review application logs for any credential exposure
- [ ] Set up secrets rotation schedule

---

## Recommended .env.example

Create `/.env.example`:

```bash
# =============================================================================
# TrendScope Environment Configuration
# =============================================================================
# Copy this file to .env and fill in your actual values
# NEVER commit .env to version control!

# =============================================================================
# IPRoyal Residential Proxy Credentials
# Get from: https://dashboard.iproyal.com/
# =============================================================================
PROXY_URL=http://USERNAME:PASSWORD@geo.iproyal.com:12321

# =============================================================================
# Database Configuration
# =============================================================================
DATABASE_URL=postgresql://user:password@localhost:5432/trendscope
REDIS_URL=redis://localhost:6379/0

# =============================================================================
# 2Captcha Configuration
# Get from: https://2captcha.com/
# =============================================================================
TWOCAPTCHA_API_KEY=your_2captcha_api_key_here

# =============================================================================
# Porkbun API Credentials (for domain management)
# Get from: https://porkbun.com/account/
# =============================================================================
PORKBUN_API_KEY=your_porkbun_api_key_here
PORKBUN_API_SECRET=your_porkbun_api_secret_here

# =============================================================================
# Stripe API Credentials
# Get from: https://dashboard.stripe.com/apikeys
# =============================================================================
STRIPE_SECRET_KEY=sk_test_...
STRIPE_PUBLISHABLE_KEY=pk_test_...

# =============================================================================
# Browserless API Key
# Get from: https://www.browserless.io/
# =============================================================================
BROWSERLESS_API_KEY=your_browserless_key_here

# =============================================================================
# RapidAPI / TikTok Scraper
# Get from: https://rapidapi.com/tiktok-scraper7/
# =============================================================================
RAPIDAPI_KEY=your_rapidapi_key_here
RAPIDAPI_HOST=tiktok-scraper7.p.rapidapi.com

# =============================================================================
# Google Ads Developer Token
# Get from: Google Ads API Console
# =============================================================================
GOOGLE_ADS_DEVELOPER_TOKEN=your_dev_token_here

# =============================================================================
# Monitoring
# =============================================================================
METRICS_PORT=9090
LOG_LEVEL=INFO

# =============================================================================
# Application Environment
# =============================================================================
APP_ENV=development
```

---

## Git Security Setup

### 1. Add/Update .gitignore

```gitignore
# Environment variables
.env
.env.local
.env.*.local
!.env.example

# Credentials
*.pem
*.key
*.p12
*.pfx

# Local development
.bashrc.local
.zshrc.local
```

### 2. Install git-secrets (Optional but Recommended)

```bash
# Install git-secrets
brew install git-secrets  # macOS
# or download from: https://github.com/awslabs/git-secrets

# Set up in repository
git secrets --install
git secrets --register-aws  # If using AWS
git secrets --add 'password.*=.*'
git secrets --add 'api_key.*=.*'
git secrets --add 'secret.*=.*'

# Scan repository
git secrets --scan
```

### 3. Pre-commit Hook Example

Create `.git/hooks/pre-commit`:

```bash
#!/bin/bash
# Pre-commit hook to prevent credential leaks

# Check for .env files
if git diff --cached --name-only | grep -E '\.env$' > /dev/null; then
    echo "ERROR: Attempting to commit .env file!"
    echo "If this is intentional, use: git commit --no-verify"
    exit 1
fi

# Check for potential API keys
git diff --cached | grep -E '(api[_-]?key|apikey|secret[_-]?key|password)\s*=\s*["\'][a-zA-Z0-9]{20,}' && {
    echo "WARNING: Potential API key or password detected in commit!"
    echo "Review the changes above."
    exit 1
}

echo "Pre-commit checks passed!"
```

Make it executable:
```bash
chmod +x .git/hooks/pre-commit
```

---

## Verification Commands

After implementing fixes, verify with:

```bash
# 1. Check no credentials in code
grep -r "api_key\|apikey\|password\|secret" --include="*.py" . | grep -v "\.pyc" | grep -v "__pycache__"

# 2. Verify .env is not tracked
git ls-files | grep "\.env"
# Should return nothing

# 3. Check for hardcoded URLs with credentials
grep -r "http://.*:.*@" --include="*.py" .

# 4. Run security linter (if bandit is installed)
bandit -r scraper/ detection/ alerts/ monitoring/ -f json -o bandit-report.json
```

---

## Contact

For questions about these security fixes, consult the security audit report or contact the security team.
