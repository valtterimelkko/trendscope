#!/bin/bash
#
# Infrastructure Prerequisites Checker
#
# Validates that Stripe and Supabase are properly configured before
# Phase 4.3 deployment. This is called during Phase 4.2.5.
#
# Usage:
#   ./check-infrastructure-prerequisites.sh          # Interactive check
#   ./check-infrastructure-prerequisites.sh --stripe # Check Stripe only
#   ./check-infrastructure-prerequisites.sh --supabase # Check Supabase only
#   ./check-infrastructure-prerequisites.sh --json   # JSON output
#

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../../.." && pwd)"
STRIPE_SCRIPT="$PROJECT_ROOT/.shared/scripts/stripe/test_connection.py"
SUPABASE_SCRIPT="$PROJECT_ROOT/.shared/scripts/supabase/test_connection.py"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Parse arguments
CHECK_STRIPE=true
CHECK_SUPABASE=true
JSON_OUTPUT=false

while [[ $# -gt 0 ]]; do
    case $1 in
        --stripe)
            CHECK_SUPABASE=false
            shift
            ;;
        --supabase)
            CHECK_STRIPE=false
            shift
            ;;
        --json)
            JSON_OUTPUT=true
            shift
            ;;
        *)
            shift
            ;;
    esac
done

# Results tracking
STRIPE_STATUS="not_checked"
STRIPE_MODE="unknown"
STRIPE_ACCOUNT=""
STRIPE_PRODUCTS=0
SUPABASE_STATUS="not_checked"
SUPABASE_PROJECT=""
SUPABASE_PROJECT_NAME=""
SUPABASE_TABLES=0
OVERALL_STATUS="incomplete"
SUPABASE_METADATA_FILE="$PROJECT_ROOT/docs/supabase-project.json"

load_supabase_metadata() {
    if [ -f "$SUPABASE_METADATA_FILE" ]; then
        SUPABASE_PROJECT=$(python3 - "$SUPABASE_METADATA_FILE" <<'PY' 2>/dev/null || true
import json,sys
try:
    data=json.load(open(sys.argv[1]))
    print(data.get("project_ref",""))
except Exception:
    pass
PY
)
        SUPABASE_PROJECT_NAME=$(python3 - "$SUPABASE_METADATA_FILE" <<'PY' 2>/dev/null || true
import json,sys
try:
    data=json.load(open(sys.argv[1]))
    print(data.get("project_name",""))
except Exception:
    pass
PY
)
        if [ -z "$SUPABASE_URL" ]; then
            SUPABASE_URL=$(python3 - "$SUPABASE_METADATA_FILE" <<'PY' 2>/dev/null || true
import json,sys
try:
    data=json.load(open(sys.argv[1]))
    print(data.get("supabase_url",""))
except Exception:
    pass
PY
)
        fi
    fi
}

print_header() {
    if [ "$JSON_OUTPUT" = false ]; then
        echo ""
        echo -e "${BLUE}============================================${NC}"
        echo -e "${BLUE}  Infrastructure Prerequisites Check${NC}"
        echo -e "${BLUE}============================================${NC}"
        echo ""
    fi
}

print_section() {
    if [ "$JSON_OUTPUT" = false ]; then
        echo ""
        echo -e "${YELLOW}--- $1 ---${NC}"
    fi
}

print_success() {
    if [ "$JSON_OUTPUT" = false ]; then
        echo -e "${GREEN}[PASS]${NC} $1"
    fi
}

print_warning() {
    if [ "$JSON_OUTPUT" = false ]; then
        echo -e "${YELLOW}[WARN]${NC} $1"
    fi
}

print_fail() {
    if [ "$JSON_OUTPUT" = false ]; then
        echo -e "${RED}[FAIL]${NC} $1"
    fi
}

print_info() {
    if [ "$JSON_OUTPUT" = false ]; then
        echo -e "       $1"
    fi
}

check_stripe() {
    print_section "Stripe Connection"

    # Check if script exists
    if [ ! -f "$STRIPE_SCRIPT" ]; then
        print_fail "Stripe test script not found"
        STRIPE_STATUS="script_missing"
        return 1
    fi

    # Check for API key in environment
    if [ -z "$STRIPE_SECRET_KEY" ]; then
        # Try loading from .env
        if [ -f "$PROJECT_ROOT/.env" ]; then
            export $(grep -v '^#' "$PROJECT_ROOT/.env" | xargs 2>/dev/null) || true
        fi
        if [ -f "$PROJECT_ROOT/.env.local" ]; then
            export $(grep -v '^#' "$PROJECT_ROOT/.env.local" | xargs 2>/dev/null) || true
        fi
    fi

    if [ -z "$STRIPE_SECRET_KEY" ]; then
        print_fail "STRIPE_SECRET_KEY not found in environment or .env file"
        print_info "Get your API key from: https://dashboard.stripe.com/apikeys"
        STRIPE_STATUS="no_api_key"
        return 1
    fi

    # Detect key type
    if [[ "$STRIPE_SECRET_KEY" == sk_live_* ]]; then
        STRIPE_MODE="live"
        print_success "Stripe API key found (LIVE mode)"
        print_warning "You're using a LIVE key. Ensure business verification is complete."
    elif [[ "$STRIPE_SECRET_KEY" == sk_test_* ]]; then
        STRIPE_MODE="test"
        print_success "Stripe API key found (TEST mode)"
        print_info "Test mode is good for development. Switch to live for production."
    else
        print_warning "Stripe API key format unrecognized"
        STRIPE_MODE="unknown"
    fi

    # Test connection
    RESULT=$(python3 "$STRIPE_SCRIPT" --test connection 2>&1) || true

    if echo "$RESULT" | grep -q '"success": true'; then
        print_success "Connected to Stripe successfully"
        STRIPE_ACCOUNT=$(echo "$RESULT" | grep -o '"id": "[^"]*"' | head -1 | cut -d'"' -f4)
        print_info "Account: $STRIPE_ACCOUNT"
        STRIPE_STATUS="connected"
    else
        print_fail "Failed to connect to Stripe"
        ERROR=$(echo "$RESULT" | grep -o '"error": "[^"]*"' | head -1 | cut -d'"' -f4)
        print_info "Error: $ERROR"
        STRIPE_STATUS="connection_failed"
        return 1
    fi

    # Check for existing products
    PRODUCT_RESULT=$(python3 "$STRIPE_SCRIPT" --test products 2>&1) || true
    STRIPE_PRODUCTS=$(echo "$PRODUCT_RESULT" | grep -o '"count": [0-9]*' | head -1 | cut -d' ' -f2)
    STRIPE_PRODUCTS=${STRIPE_PRODUCTS:-0}

    if [ "$STRIPE_PRODUCTS" -gt 0 ]; then
        print_info "Existing products: $STRIPE_PRODUCTS"
    else
        print_info "No products yet (will be created during deployment)"
    fi

    return 0
}

check_supabase() {
    print_section "Supabase Connection"

    # Check if script exists
    if [ ! -f "$SUPABASE_SCRIPT" ]; then
        print_fail "Supabase test script not found"
        SUPABASE_STATUS="script_missing"
        return 1
    fi

    # Check for URL and key in environment
    SUPABASE_URL="${SUPABASE_URL:-$NEXT_PUBLIC_SUPABASE_URL}"
    SUPABASE_KEY="${SUPABASE_SERVICE_ROLE_KEY:-$SUPABASE_ANON_KEY}"
    SUPABASE_KEY="${SUPABASE_KEY:-$NEXT_PUBLIC_SUPABASE_ANON_KEY}"

    if [ -z "$SUPABASE_URL" ] || [ -z "$SUPABASE_KEY" ]; then
        # Try loading from .env
        if [ -f "$PROJECT_ROOT/.env" ]; then
            export $(grep -v '^#' "$PROJECT_ROOT/.env" | xargs 2>/dev/null) || true
        fi
        if [ -f "$PROJECT_ROOT/.env.local" ]; then
            export $(grep -v '^#' "$PROJECT_ROOT/.env.local" | xargs 2>/dev/null) || true
        fi

        SUPABASE_URL="${SUPABASE_URL:-$NEXT_PUBLIC_SUPABASE_URL}"
        SUPABASE_KEY="${SUPABASE_SERVICE_ROLE_KEY:-$SUPABASE_ANON_KEY}"
        SUPABASE_KEY="${SUPABASE_KEY:-$NEXT_PUBLIC_SUPABASE_ANON_KEY}"
    fi

    if [ -z "$SUPABASE_URL" ]; then
        print_fail "SUPABASE_URL not found in environment or .env file"
        print_info "Create a project at: https://supabase.com/dashboard"
        print_info "Then add SUPABASE_URL to your .env file"
        SUPABASE_STATUS="no_url"
        return 1
    fi

    if [ -z "$SUPABASE_KEY" ]; then
        print_fail "SUPABASE_ANON_KEY or SUPABASE_SERVICE_ROLE_KEY not found"
        print_info "Get your keys from: https://supabase.com/dashboard/project/_/settings/api"
        SUPABASE_STATUS="no_api_key"
        return 1
    fi

    print_success "Supabase credentials found"

    # Extract project reference from URL
    SUPABASE_PROJECT=$(echo "$SUPABASE_URL" | sed 's|https://||' | cut -d'.' -f1)
    print_info "Project: $SUPABASE_PROJECT"

    # Test connection
    RESULT=$(python3 "$SUPABASE_SCRIPT" --test connection 2>&1) || true

    if echo "$RESULT" | grep -q '"success": true'; then
        print_success "Connected to Supabase successfully"
        SUPABASE_STATUS="connected"
    else
        print_fail "Failed to connect to Supabase"
        ERROR=$(echo "$RESULT" | grep -o '"error": "[^"]*"' | head -1 | cut -d'"' -f4)
        print_info "Error: $ERROR"
        SUPABASE_STATUS="connection_failed"
        return 1
    fi

    # Check for existing tables
    TABLE_RESULT=$(python3 "$SUPABASE_SCRIPT" --test tables 2>&1) || true
    SUPABASE_TABLES=$(echo "$TABLE_RESULT" | grep -o '"tables_found": [0-9]*' | head -1 | cut -d' ' -f2)
    SUPABASE_TABLES=${SUPABASE_TABLES:-0}

    if [ "$SUPABASE_TABLES" -gt 0 ]; then
        print_info "Existing tables: $SUPABASE_TABLES"
    else
        print_info "No tables yet (will be created during deployment)"
    fi

    return 0
}

check_stripe_verification() {
    print_section "Stripe Account Status"

    if [ "$STRIPE_MODE" = "live" ]; then
        print_info "Using LIVE mode - business verification may be required"
        print_info "Check verification status at: https://dashboard.stripe.com/account"
        print_warning "If not verified, payments cannot be processed in production"
    elif [ "$STRIPE_MODE" = "test" ]; then
        print_info "Using TEST mode - no verification required for testing"
        print_info "To accept real payments, switch to LIVE mode and complete verification"
    fi
}

print_summary() {
    if [ "$JSON_OUTPUT" = false ]; then
        echo ""
        echo -e "${BLUE}============================================${NC}"
        echo -e "${BLUE}  Summary${NC}"
        echo -e "${BLUE}============================================${NC}"
        echo ""

        if [ "$STRIPE_STATUS" = "connected" ] && [ "$SUPABASE_STATUS" = "connected" ]; then
            OVERALL_STATUS="ready"
            echo -e "${GREEN}[READY]${NC} Infrastructure prerequisites met!"
            echo ""
            echo "You can proceed to Phase 4.3 (Template Integration)"
            echo ""
            echo "Next steps:"
            echo "  1. Phase 4.3.1: Brand personalization"
            echo "  2. Phase 4.3.2: Content generation"
            echo "  3. Phase 4.3.3: Stripe product deployment"
            echo "  4. Phase 4.3.4: Supabase migration deployment"
        elif [ "$STRIPE_STATUS" = "connected" ] && [ "$SUPABASE_STATUS" != "connected" ]; then
            OVERALL_STATUS="partial"
            echo -e "${YELLOW}[PARTIAL]${NC} Stripe ready, Supabase needs setup"
            echo ""
            echo "To set up Supabase:"
            echo "  1. Create a project at https://supabase.com/dashboard"
            echo "  2. Copy the project URL and keys from Settings > API"
            echo "  3. Add to your .env file:"
            echo "     SUPABASE_URL=https://xxxxx.supabase.co"
            echo "     SUPABASE_ANON_KEY=eyJhbG..."
            echo "     SUPABASE_SERVICE_ROLE_KEY=eyJhbG..."
        elif [ "$STRIPE_STATUS" != "connected" ] && [ "$SUPABASE_STATUS" = "connected" ]; then
            OVERALL_STATUS="partial"
            echo -e "${YELLOW}[PARTIAL]${NC} Supabase ready, Stripe needs setup"
            echo ""
            echo "To set up Stripe:"
            echo "  1. Create/log in at https://dashboard.stripe.com"
            echo "  2. Get your API key from Developers > API keys"
            echo "  3. Add to your .env file:"
            echo "     STRIPE_SECRET_KEY=sk_test_xxx (for testing)"
            echo "     STRIPE_SECRET_KEY=sk_live_xxx (for production)"
        else
            OVERALL_STATUS="not_ready"
            echo -e "${RED}[NOT READY]${NC} Both Stripe and Supabase need setup"
            echo ""
            echo "Please set up both services before proceeding."
        fi
        echo ""
    fi
}

output_json() {
    cat << EOF
{
  "overall_status": "$OVERALL_STATUS",
  "stripe": {
    "status": "$STRIPE_STATUS",
    "mode": "$STRIPE_MODE",
    "account": "$STRIPE_ACCOUNT",
    "products_count": $STRIPE_PRODUCTS
  },
  "supabase": {
    "status": "$SUPABASE_STATUS",
    "project": "$SUPABASE_PROJECT",
    "tables_count": $SUPABASE_TABLES
  },
  "ready_for_deployment": $([ "$OVERALL_STATUS" = "ready" ] && echo "true" || echo "false")
}
EOF
}

# Main execution
print_header

if [ "$CHECK_STRIPE" = true ]; then
    check_stripe || true
    check_stripe_verification || true
fi

if [ "$CHECK_SUPABASE" = true ]; then
    load_supabase_metadata || true
    check_supabase || true
fi

# Determine overall status
if [ "$STRIPE_STATUS" = "connected" ] && [ "$SUPABASE_STATUS" = "connected" ]; then
    OVERALL_STATUS="ready"
elif [ "$STRIPE_STATUS" = "connected" ] || [ "$SUPABASE_STATUS" = "connected" ]; then
    OVERALL_STATUS="partial"
else
    OVERALL_STATUS="not_ready"
fi

if [ "$JSON_OUTPUT" = true ]; then
    output_json
else
    print_summary
fi

# Exit with appropriate code
if [ "$OVERALL_STATUS" = "ready" ]; then
    exit 0
elif [ "$OVERALL_STATUS" = "partial" ]; then
    exit 1
else
    exit 2
fi
