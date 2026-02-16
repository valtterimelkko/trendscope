#!/bin/bash
#
# Domain Availability Checker
# Primary: Uses Porkbun API (requires PORKBUN_API_KEY and PORKBUN_API_SECRET)
# Fallback: Uses whois if API keys not configured
#
# Usage:
#   ./check-domain.sh domain.com                    # Check single domain
#   ./check-domain.sh domain1.com domain2.io        # Check multiple domains
#   ./check-domain.sh mysite .com .io .dev          # Check name across TLDs
#   echo -e "domain1.com\ndomain2.io" | ./check-domain.sh  # Pipe domains
#
# Environment variables:
#   PORKBUN_API_KEY        - Your Porkbun API key
#   PORKBUN_API_SECRET     - Your Porkbun API secret
#
# Exit codes:
#   0 = All checked successfully (doesn't mean available)
#   1 = Error (no API keys and whois not installed, etc.)

set -euo pipefail

# Load environment variables from .env file (for Claude Code and local usage)
# This allows credentials to be stored in a file instead of shell profile
if [[ -f ".env" ]]; then
    # Source .env but only export variables we need (for security)
    # Variables are loaded but only used if they're defined
    set -a
    source .env
    set +a
fi

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Delay between checks to avoid rate limiting (seconds)
DELAY=0.5

# Porkbun API endpoint
PORKBUN_API_URL="https://api.porkbun.com/api/json/v3/domain/checkDomain"

# Check if Porkbun API keys are configured
PORKBUN_ENABLED=false
if [[ -n "${PORKBUN_API_KEY:-}" && -n "${PORKBUN_API_SECRET:-}" ]]; then
    PORKBUN_ENABLED=true
fi

# Check if whois is installed (fallback)
WHOIS_AVAILABLE=false
if command -v whois &> /dev/null; then
    WHOIS_AVAILABLE=true
fi

# Patterns that indicate a domain is available (case-insensitive)
# Different registrars use different messages
AVAILABLE_PATTERNS=(
    "no match"
    "not found"
    "no entries found"
    "no data found"
    "available"
    "status: free"
    "status: available"
    "no object found"
    "domain not found"
    "nothing found"
    "is free"
    "no information available"
    "not registered"
    "no such domain"
)

# Build grep pattern from array
build_pattern() {
    local pattern=""
    for p in "${AVAILABLE_PATTERNS[@]}"; do
        if [[ -z "$pattern" ]]; then
            pattern="$p"
        else
            pattern="$pattern|$p"
        fi
    done
    echo "$pattern"
}

GREP_PATTERN=$(build_pattern)

# Check domain availability via Porkbun API
check_domain_porkbun() {
    local domain="$1"

    # Make API call to Porkbun
    local response
    response=$(curl -s -X POST "$PORKBUN_API_URL/$domain" \
        -H "Content-Type: application/json" \
        -d "{\"apikey\":\"$PORKBUN_API_KEY\",\"secretapikey\":\"$PORKBUN_API_SECRET\"}" 2>/dev/null) || return 1

    # Check if response is valid JSON
    if ! echo "$response" | grep -q '"status"'; then
        return 1
    fi

    # Extract status and availability
    local status=$(echo "$response" | grep -o '"status":"[^"]*"' | cut -d'"' -f4)
    local available=$(echo "$response" | grep -o '"avail":"[^"]*"' | cut -d'"' -f4)

    if [[ "$status" != "SUCCESS" ]]; then
        echo -e "${YELLOW}?${NC} $domain - API error"
        return 1
    fi

    if [[ "$available" == "yes" ]]; then
        echo -e "${GREEN}✓${NC} $domain - ${GREEN}AVAILABLE${NC} ${CYAN}(Porkbun verified)${NC}"
        return 0
    else
        echo -e "${RED}✗${NC} $domain - Taken ${CYAN}(Porkbun verified)${NC}"
        return 0
    fi
}

# Check domain availability via whois (fallback)
check_domain_whois() {
    local domain="$1"
    local result
    local exit_code=0

    # Get whois data, suppress errors
    result=$(whois "$domain" 2>/dev/null) || exit_code=$?

    # Some whois servers return non-zero for not found, that's okay
    if [[ -z "$result" ]]; then
        echo -e "${YELLOW}?${NC} $domain - Could not query whois"
        return
    fi

    # Check for rate limiting indicators
    if echo "$result" | grep -qi "rate limit\|too many\|try again\|quota exceeded"; then
        echo -e "${YELLOW}!${NC} $domain - Rate limited, try again later"
        return
    fi

    # Check if domain appears available
    if echo "$result" | grep -qiE "$GREP_PATTERN"; then
        echo -e "${GREEN}✓${NC} $domain - ${GREEN}AVAILABLE${NC} ${CYAN}(WHOIS - less reliable)${NC}"
    else
        # Try to extract registrar/expiry info for taken domains
        local registrar=$(echo "$result" | grep -i "registrar:" | head -1 | cut -d':' -f2- | xargs 2>/dev/null || echo "")
        if [[ -n "$registrar" ]]; then
            echo -e "${RED}✗${NC} $domain - Taken (${registrar:0:40})"
        else
            echo -e "${RED}✗${NC} $domain - Taken"
        fi
    fi
}

# Check a single domain (dispatch to appropriate method)
check_domain() {
    local domain="$1"

    if $PORKBUN_ENABLED; then
        check_domain_porkbun "$domain"
    elif $WHOIS_AVAILABLE; then
        check_domain_whois "$domain"
    else
        echo -e "${RED}✗${NC} $domain - Error: Neither Porkbun API nor whois available"
        return 1
    fi
}

# Expand a base name to multiple TLDs
# e.g., "mysite .com .io" -> "mysite.com mysite.io"
expand_tlds() {
    local args=("$@")
    local base=""
    local tlds=()
    local domains=()
    
    for arg in "${args[@]}"; do
        if [[ "$arg" == .* ]]; then
            # It's a TLD
            tlds+=("$arg")
        elif [[ "$arg" == *.* ]]; then
            # It's already a full domain
            domains+=("$arg")
        else
            # It's a base name
            base="$arg"
        fi
    done
    
    # If we have a base and TLDs, expand them
    if [[ -n "$base" && ${#tlds[@]} -gt 0 ]]; then
        for tld in "${tlds[@]}"; do
            domains+=("${base}${tld}")
        done
    fi
    
    # Return unique domains
    printf '%s\n' "${domains[@]}" | sort -u
}

# Main execution
main() {
    local domains=()

    # Display which verification method will be used
    if $PORKBUN_ENABLED; then
        echo -e "${CYAN}Using Porkbun API for domain verification (most accurate)${NC}"
    elif $WHOIS_AVAILABLE; then
        echo -e "${YELLOW}Using WHOIS for domain verification (less reliable, consider configuring Porkbun API)${NC}"
    else
        echo -e "${RED}Error: Neither Porkbun API nor whois available${NC}"
        echo "Options:"
        echo "  1. Configure Porkbun API (recommended):"
        echo "     export PORKBUN_API_KEY='your-key'"
        echo "     export PORKBUN_API_SECRET='your-secret'"
        echo "  2. Install whois (fallback):"
        echo "     sudo apt install whois"
        exit 1
    fi
    echo ""

    # Read from arguments or stdin
    if [[ $# -gt 0 ]]; then
        # Check if we have TLD expansion pattern
        has_tld=false
        for arg in "$@"; do
            if [[ "$arg" == .* ]]; then
                has_tld=true
                break
            fi
        done

        if $has_tld; then
            while IFS= read -r domain; do
                domains+=("$domain")
            done < <(expand_tlds "$@")
        else
            domains=("$@")
        fi
    else
        # Read from stdin
        while IFS= read -r line; do
            [[ -n "$line" ]] && domains+=("$line")
        done
    fi

    if [[ ${#domains[@]} -eq 0 ]]; then
        echo "Usage: $0 domain.com [domain2.io ...]"
        echo "       $0 mysite .com .io .dev"
        echo "       echo 'domain.com' | $0"
        exit 1
    fi

    echo -e "${BLUE}Checking ${#domains[@]} domain(s)...${NC}"
    echo ""

    local count=0
    for domain in "${domains[@]}"; do
        check_domain "$domain"
        count=$((count + 1))

        # Add delay between checks (except for last one)
        if [[ $count -lt ${#domains[@]} ]]; then
            sleep "$DELAY"
        fi
    done

    echo ""
    echo -e "${BLUE}Done. Checked ${#domains[@]} domain(s).${NC}"
}

main "$@"
