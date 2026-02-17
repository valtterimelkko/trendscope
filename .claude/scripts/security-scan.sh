#!/bin/bash
#
# MVP Security Scanner
# Runs automated security checks for MVP projects
#
# Usage:
#   ./security-scan.sh [project-path]    # Scan specific directory
#   ./security-scan.sh                   # Scan current directory
#
# Checks:
#   - Dependency vulnerabilities (npm audit, pip-audit)
#   - Secret detection in files (high-entropy strings, common patterns)
#   - Security-sensitive code patterns
#   - Missing security headers in config files
#
# Exit codes:
#   0 = All checks passed
#   1 = Issues found (review output)
#   2 = Error (tool not available)

set -euo pipefail

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
NC='\033[0m'

PROJECT_PATH="${1:-.}"
ISSUES_FOUND=0

echo -e "${BLUE}═══════════════════════════════════════════════════════════════${NC}"
echo -e "${BLUE}          MVP Security Scanner                                  ${NC}"
echo -e "${BLUE}═══════════════════════════════════════════════════════════════${NC}"
echo ""
echo -e "Scanning: ${PROJECT_PATH}"
echo -e "Date: $(date)"
echo ""

# Helper function to check if command exists
command_exists() {
    command -v "$1" &> /dev/null
}

# Section header
section() {
    echo ""
    echo -e "${BLUE}───────────────────────────────────────────────────────────────${NC}"
    echo -e "${BLUE}  $1${NC}"
    echo -e "${BLUE}───────────────────────────────────────────────────────────────${NC}"
}

# ============================================================================
# 1. DEPENDENCY VULNERABILITY SCANNING
# ============================================================================
section "1. Dependency Vulnerability Scan"

# Check for package.json (Node.js)
if [[ -f "${PROJECT_PATH}/package.json" ]]; then
    echo -e "Found package.json - running npm audit..."
    cd "${PROJECT_PATH}"
    if npm audit --audit-level=high 2>/dev/null; then
        echo -e "${GREEN}✓ No high/critical npm vulnerabilities${NC}"
    else
        echo -e "${RED}✗ npm vulnerabilities found (see above)${NC}"
        ISSUES_FOUND=1
    fi
    cd - > /dev/null
else
    echo "No package.json found - skipping npm audit"
fi

# Check for requirements.txt or pyproject.toml (Python)
if [[ -f "${PROJECT_PATH}/requirements.txt" ]] || [[ -f "${PROJECT_PATH}/pyproject.toml" ]]; then
    if command_exists pip-audit; then
        echo -e "Found Python project - running pip-audit..."
        cd "${PROJECT_PATH}"
        if pip-audit 2>/dev/null; then
            echo -e "${GREEN}✓ No Python vulnerabilities${NC}"
        else
            echo -e "${RED}✗ pip vulnerabilities found${NC}"
            ISSUES_FOUND=1
        fi
        cd - > /dev/null
    else
        echo -e "${YELLOW}! pip-audit not installed. Install with: pip install pip-audit${NC}"
    fi
fi

# ============================================================================
# 2. SECRET DETECTION
# ============================================================================
section "2. Secret Detection"

# Common secret patterns to search for
SECRET_PATTERNS=(
    "password\s*=\s*['\"][^'\"]+['\"]"
    "api[_-]?key\s*=\s*['\"][^'\"]+['\"]"
    "secret\s*=\s*['\"][^'\"]+['\"]"
    "token\s*=\s*['\"][a-zA-Z0-9_\-]+['\"]"
    "PRIVATE[_-]?KEY"
    "-----BEGIN.*PRIVATE KEY-----"
    "aws_access_key_id"
    "aws_secret_access_key"
    "sk_live_"
    "pk_live_"
    "ghp_[a-zA-Z0-9]{36}"
    "gho_[a-zA-Z0-9]{36}"
)

# Files to exclude from secret scanning
EXCLUDE_OPTS=(
    --exclude-dir=node_modules
    --exclude-dir=.git
    --exclude-dir=venv
    --exclude-dir=__pycache__
    --exclude-dir=dist
    --exclude-dir=build
    --exclude='*.lock'
    --exclude=package-lock.json
    --exclude=yarn.lock
)

SECRETS_FOUND=0
for pattern in "${SECRET_PATTERNS[@]}"; do
    if grep -rEi "${EXCLUDE_OPTS[@]}" "$pattern" "${PROJECT_PATH}" 2>/dev/null | grep -v "\.env\.example" | head -5; then
        SECRETS_FOUND=1
    fi
done

if [[ $SECRETS_FOUND -eq 1 ]]; then
    echo -e "${RED}✗ Potential secrets found in source code (see above)${NC}"
    ISSUES_FOUND=1
else
    echo -e "${GREEN}✓ No obvious secrets in source code${NC}"
fi

# Check for commented-out secrets
echo "Checking for commented secrets..."
COMMENTED_SECRETS=0
if grep -rEi "${EXCLUDE_OPTS[@]}" '^[ \t]*(//|#).*["\x27].*[a-zA-Z0-9]{20,}["\x27]|^[ \t]*(//|#).*(password|api[_-]?key|secret).*=.*["\x27]' "${PROJECT_PATH}" 2>/dev/null | grep -v "\.env\.example" | head -5; then
    COMMENTED_SECRETS=1
fi

if [[ $COMMENTED_SECRETS -eq 1 ]]; then
    echo -e "${YELLOW}! Potential secrets in comments (review above)${NC}"
else
    echo -e "${GREEN}✓ No secrets in comments${NC}"
fi

# Check for .env in git
if [[ -d "${PROJECT_PATH}/.git" ]]; then
    if git -C "${PROJECT_PATH}" ls-files --error-unmatch .env 2>/dev/null; then
        echo -e "${RED}✗ .env file is tracked by git!${NC}"
        ISSUES_FOUND=1
    else
        echo -e "${GREEN}✓ .env not tracked by git${NC}"
    fi
fi

# ============================================================================
# 3. SECURITY-SENSITIVE CODE PATTERNS
# ============================================================================
section "3. Security-Sensitive Code Patterns"

# Dangerous patterns to flag
check_pattern() {
    local pattern="$1"
    local message="$2"
    local severity="$3"
    
    local count
    count=$(grep -rEi "${EXCLUDE_OPTS[@]}" "$pattern" "${PROJECT_PATH}" 2>/dev/null | wc -l) || count=0
    count=$((count + 0))  # Force numeric
    if [[ $count -gt 0 ]]; then
        if [[ "$severity" == "HIGH" ]]; then
            echo -e "${RED}✗ $message ($count occurrences)${NC}"
            ISSUES_FOUND=1
        else
            echo -e "${YELLOW}! $message ($count occurrences)${NC}"
        fi
        grep -rEi "${EXCLUDE_OPTS[@]}" "$pattern" "${PROJECT_PATH}" 2>/dev/null | head -3
        echo "  ..."
    fi
}

# React/Vue XSS risks
check_pattern "dangerouslySetInnerHTML" "React dangerouslySetInnerHTML usage" "HIGH"
check_pattern "v-html" "Vue v-html usage" "HIGH"

# SQL Injection risks - detect string concatenation in queries and SQL strings
check_pattern 'query.*\+.*(SELECT|INSERT|UPDATE|DELETE|WHERE)|["\x27](SELECT|INSERT|UPDATE|DELETE).*\+' "Potential SQL injection (string concatenation)" "HIGH"

# Eval and similar
check_pattern "eval\s*\(" "eval() usage" "HIGH"
check_pattern "new\s+Function\s*\(" "new Function() usage" "HIGH"

# localStorage for tokens
check_pattern "localStorage\.setItem\s*\(\s*['\"].*token" "Token stored in localStorage" "HIGH"
check_pattern "sessionStorage\.setItem\s*\(\s*['\"].*token" "Token stored in sessionStorage" "MEDIUM"

# Weak crypto
check_pattern "createHash\s*\(\s*['\"]md5" "MD5 hash usage" "HIGH"
check_pattern "createHash\s*\(\s*['\"]sha1" "SHA1 hash usage" "MEDIUM"

# CORS wildcards
check_pattern 'Access-Control-Allow-Origin.*\*' "CORS wildcard origin" "MEDIUM"
check_pattern 'origin:\s*true|origin:\s*\*' "Permissive CORS config" "MEDIUM"

# Python-specific security risks
check_pattern "shell\s*=\s*True" "Python shell=True (command injection risk)" "HIGH"
check_pattern "exec\s*\(|compile\s*\(" "Python exec/compile usage" "HIGH"
check_pattern "pickle\.loads|pickle\.load\s*\(|yaml\.load\s*\([^,)]*\)" "Unsafe deserialization (pickle/yaml)" "HIGH"

echo ""
echo -e "${GREEN}✓ Pattern scan complete${NC}"

# ============================================================================
# 4. CONFIGURATION CHECKS
# ============================================================================
section "4. Configuration Checks"

# Check for security headers in common config locations
check_config_file() {
    local file="$1"
    local check="$2"
    local message="$3"
    
    if [[ -f "${PROJECT_PATH}/${file}" ]]; then
        if grep -qi "$check" "${PROJECT_PATH}/${file}" 2>/dev/null; then
            echo -e "${GREEN}✓ $message${NC}"
        else
            echo -e "${YELLOW}! Missing: $message${NC}"
        fi
    fi
}

# Common config files
if [[ -f "${PROJECT_PATH}/next.config.js" ]] || [[ -f "${PROJECT_PATH}/next.config.mjs" ]]; then
    echo "Checking Next.js config..."
    check_config_file "next.config.js" "headers" "Security headers configured"
    check_config_file "next.config.mjs" "headers" "Security headers configured"
fi

if [[ -f "${PROJECT_PATH}/vercel.json" ]]; then
    echo "Checking Vercel config..."
    check_config_file "vercel.json" "headers" "Security headers configured"
fi

# Check for .gitignore with .env
if [[ -f "${PROJECT_PATH}/.gitignore" ]]; then
    if grep -q "\.env" "${PROJECT_PATH}/.gitignore"; then
        echo -e "${GREEN}✓ .env in .gitignore${NC}"
    else
        echo -e "${RED}✗ .env NOT in .gitignore${NC}"
        ISSUES_FOUND=1
    fi
else
    echo -e "${YELLOW}! No .gitignore found${NC}"
fi

# Check for .env.example when env vars are used
ENV_VAR_COUNT=$(grep -rE "process\.env\.|os\.getenv|ENV\[|System\.getenv" "${PROJECT_PATH}" --exclude-dir=node_modules --exclude-dir=venv 2>/dev/null | wc -l) || ENV_VAR_COUNT=0
ENV_VAR_COUNT=$((ENV_VAR_COUNT + 0))  # Force numeric

if [[ $ENV_VAR_COUNT -gt 0 ]]; then
    if [[ -f "${PROJECT_PATH}/.env.example" ]] || [[ -f "${PROJECT_PATH}/.env.template" ]]; then
        echo -e "${GREEN}✓ .env.example exists (found $ENV_VAR_COUNT env var references)${NC}"
    else
        echo -e "${YELLOW}! No .env.example found but $ENV_VAR_COUNT env var references detected${NC}"
    fi
fi

# ============================================================================
# SUMMARY
# ============================================================================
section "Summary"

if [[ $ISSUES_FOUND -eq 0 ]]; then
    echo -e "${GREEN}═══════════════════════════════════════════════════════════════${NC}"
    echo -e "${GREEN}  ✓ No critical security issues found                          ${NC}"
    echo -e "${GREEN}═══════════════════════════════════════════════════════════════${NC}"
    exit 0
else
    echo -e "${RED}═══════════════════════════════════════════════════════════════${NC}"
    echo -e "${RED}  ✗ Security issues found - review above                        ${NC}"
    echo -e "${RED}═══════════════════════════════════════════════════════════════${NC}"
    echo ""
    echo "Recommended next steps:"
    echo "  1. Fix any hardcoded secrets"
    echo "  2. Update vulnerable dependencies"
    echo "  3. Review flagged code patterns"
    echo "  4. Add security headers to config"
    exit 1
fi
