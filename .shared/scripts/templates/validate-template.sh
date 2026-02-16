#!/bin/bash
# Template Validation Master Script
# Runs all validation checks on a template directory
# Usage: ./validate-template.sh <template-path>

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TEMPLATE_PATH="$1"

if [ -z "$TEMPLATE_PATH" ]; then
    echo "Usage: $0 <template-path>"
    echo "Example: $0 templates/analytics-dashboard"
    exit 1
fi

if [ ! -d "$TEMPLATE_PATH" ]; then
    echo "Error: Template directory not found: $TEMPLATE_PATH"
    exit 2
fi

TEMPLATE_NAME=$(basename "$TEMPLATE_PATH")
BLOCKERS=0
WARNINGS=0
SUGGESTIONS=0

echo "=============================================="
echo "  Template Validation Report"
echo "=============================================="
echo ""
echo "Template:    $TEMPLATE_NAME"
echo "Path:        $TEMPLATE_PATH"
echo "Date:        $(date '+%Y-%m-%d %H:%M:%S')"
echo ""
echo "----------------------------------------------"

# Function to print section headers
section() {
    echo ""
    echo "## $1"
    echo ""
}

# Function to record issues
blocker() {
    echo "❌ BLOCKER: $1"
    ((BLOCKERS++))
}

warning() {
    echo "⚠️  WARNING: $1"
    ((WARNINGS++))
}

suggestion() {
    echo "💡 SUGGESTION: $1"
    ((SUGGESTIONS++))
}

pass() {
    echo "✅ $1"
}

# ============================================
# 1. STRUCTURE VALIDATION
# ============================================
section "1. Structure Validation"

REQUIRED_FILES=(
    "manifest.json"
    "README.md"
    "frontend/package.json"
    "frontend/next.config.js"
    "frontend/tsconfig.json"
    "frontend/tailwind.config.js"
    "frontend/app/layout.tsx"
    "frontend/app/page.tsx"
    "frontend/styles/tokens.css"
    "supabase/config.toml"
    "stripe/products.json"
    "content/slots.json"
)

REQUIRED_DIRS=(
    "frontend/app/(auth)/login"
    "frontend/app/(auth)/signup"
    "frontend/app/(auth)/callback"
    "frontend/app/(dashboard)"
    "frontend/app/(dashboard)/settings"
    "frontend/app/api/stripe"
    "frontend/components"
    "frontend/lib/supabase"
    "frontend/lib/stripe"
    "supabase/migrations"
)

STRUCTURE_PASS=true

for file in "${REQUIRED_FILES[@]}"; do
    if [ ! -f "$TEMPLATE_PATH/$file" ]; then
        blocker "Missing required file: $file"
        STRUCTURE_PASS=false
    fi
done

for dir in "${REQUIRED_DIRS[@]}"; do
    if [ ! -d "$TEMPLATE_PATH/$dir" ]; then
        blocker "Missing required directory: $dir"
        STRUCTURE_PASS=false
    fi
done

if [ "$STRUCTURE_PASS" = true ]; then
    pass "All required files and directories present"
fi

# ============================================
# 2. MANIFEST VALIDATION
# ============================================
section "2. Manifest Validation"

if [ -f "$TEMPLATE_PATH/manifest.json" ]; then
    # Check if valid JSON
    if python3 -c "import json; json.load(open('$TEMPLATE_PATH/manifest.json'))" 2>/dev/null; then
        pass "manifest.json is valid JSON"
        
        # Run Python validation
        python3 "$SCRIPT_DIR/check-manifest.py" "$TEMPLATE_PATH/manifest.json" "$TEMPLATE_NAME"
        if [ $? -ne 0 ]; then
            ((BLOCKERS++))
        fi
    else
        blocker "manifest.json is not valid JSON"
    fi
else
    blocker "manifest.json not found"
fi

# ============================================
# 3. CONTENT SLOTS VALIDATION
# ============================================
section "3. Content Slots Validation"

if [ -f "$TEMPLATE_PATH/content/slots.json" ]; then
    python3 "$SCRIPT_DIR/check-content-slots.py" "$TEMPLATE_PATH/content/slots.json"
    SLOTS_EXIT=$?
    if [ $SLOTS_EXIT -eq 1 ]; then
        ((BLOCKERS++))
    elif [ $SLOTS_EXIT -eq 2 ]; then
        ((WARNINGS++))
    fi
else
    blocker "content/slots.json not found"
fi

# ============================================
# 4. BRAND TOKENS VALIDATION
# ============================================
section "4. Brand Tokens Validation"

if [ -f "$TEMPLATE_PATH/frontend/styles/tokens.css" ]; then
    python3 "$SCRIPT_DIR/check-brand-tokens.py" "$TEMPLATE_PATH/frontend/styles/tokens.css"
    TOKENS_EXIT=$?
    if [ $TOKENS_EXIT -eq 1 ]; then
        ((BLOCKERS++))
    elif [ $TOKENS_EXIT -eq 2 ]; then
        ((WARNINGS++))
    fi
else
    blocker "frontend/styles/tokens.css not found"
fi

# ============================================
# 5. SUPABASE SCHEMA VALIDATION
# ============================================
section "5. Supabase Schema Validation"

MIGRATIONS_DIR="$TEMPLATE_PATH/supabase/migrations"
if [ -d "$MIGRATIONS_DIR" ] && [ "$(ls -A $MIGRATIONS_DIR 2>/dev/null)" ]; then
    python3 "$SCRIPT_DIR/check-supabase-schema.py" "$MIGRATIONS_DIR"
    SCHEMA_EXIT=$?
    if [ $SCHEMA_EXIT -eq 1 ]; then
        ((BLOCKERS++))
    elif [ $SCHEMA_EXIT -eq 2 ]; then
        ((WARNINGS++))
    fi
else
    blocker "No migration files found in supabase/migrations/"
fi

# ============================================
# 6. STRIPE CONFIG VALIDATION
# ============================================
section "6. Stripe Configuration Validation"

if [ -f "$TEMPLATE_PATH/stripe/products.json" ]; then
    python3 "$SCRIPT_DIR/check-stripe-config.py" "$TEMPLATE_PATH/stripe/products.json"
    STRIPE_EXIT=$?
    if [ $STRIPE_EXIT -eq 1 ]; then
        ((BLOCKERS++))
    elif [ $STRIPE_EXIT -eq 2 ]; then
        ((WARNINGS++))
    fi
else
    blocker "stripe/products.json not found"
fi

# ============================================
# 7. AUTH FLOW VALIDATION
# ============================================
section "7. Authentication Flow Validation"

AUTH_FILES=(
    "frontend/app/(auth)/callback/route.ts"
    "frontend/lib/supabase/client.ts"
    "frontend/lib/supabase/server.ts"
)

AUTH_PASS=true
for file in "${AUTH_FILES[@]}"; do
    if [ ! -f "$TEMPLATE_PATH/$file" ]; then
        blocker "Missing auth file: $file"
        AUTH_PASS=false
    fi
done

# Check for OAuth implementation
if [ -d "$TEMPLATE_PATH/frontend/components/auth" ]; then
    if grep -rq "signInWithOAuth" "$TEMPLATE_PATH/frontend" 2>/dev/null; then
        pass "Google OAuth implementation found"
    else
        warning "No OAuth implementation found (signInWithOAuth)"
    fi
else
    warning "frontend/components/auth directory not found"
fi

# Check for hardcoded secrets
if grep -rq "sk_live_\|sk_test_\|supabase.*key.*=.*['\"]ey" "$TEMPLATE_PATH/frontend" 2>/dev/null; then
    blocker "Hardcoded API keys found in frontend code"
else
    pass "No hardcoded secrets detected"
fi

if [ "$AUTH_PASS" = true ]; then
    pass "All required auth files present"
fi

# ============================================
# 8. CODE QUALITY CHECKS
# ============================================
section "8. Code Quality Validation"

# Check TypeScript config
if [ -f "$TEMPLATE_PATH/frontend/tsconfig.json" ]; then
    if grep -q '"strict": true' "$TEMPLATE_PATH/frontend/tsconfig.json"; then
        pass "TypeScript strict mode enabled"
    else
        warning "TypeScript strict mode not enabled"
    fi
fi

# Check for 'any' types (simple grep)
ANY_COUNT=$(grep -r ": any" "$TEMPLATE_PATH/frontend" --include="*.ts" --include="*.tsx" 2>/dev/null | wc -l)
if [ "$ANY_COUNT" -gt 5 ]; then
    warning "Found $ANY_COUNT uses of 'any' type - consider adding proper types"
else
    pass "Minimal use of 'any' types ($ANY_COUNT)"
fi

# ============================================
# SUMMARY
# ============================================
echo ""
echo "=============================================="
echo "  VALIDATION SUMMARY"
echo "=============================================="
echo ""
echo "Template:     $TEMPLATE_NAME"
echo "Blockers:     $BLOCKERS"
echo "Warnings:     $WARNINGS"
echo "Suggestions:  $SUGGESTIONS"
echo ""

if [ $BLOCKERS -gt 0 ]; then
    echo "❌ FAILED - Fix $BLOCKERS blocker(s) before use"
    exit 2
elif [ $WARNINGS -gt 0 ]; then
    echo "⚠️  PASSED WITH WARNINGS - $WARNINGS issue(s) should be fixed"
    exit 1
else
    echo "✅ PASSED - Template is ready for integration"
    exit 0
fi
