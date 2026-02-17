#!/bin/bash
#
# Pre-Stage Verification Script
# Verifies that a stage is ready for implementation and git is in clean state
#
# Usage:
#   ./verify-stage-readiness.sh <stage-number>
#   ./verify-stage-readiness.sh <stage-number> --strict
#
# Exit codes:
#   0 = Ready to proceed
#   1 = Pre-conditions not met
#

set -euo pipefail

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
NC='\033[0m'

if [[ $# -lt 1 ]]; then
    echo -e "${BLUE}Pre-Stage Verification Script${NC}"
    echo ""
    echo "Usage: $0 <stage-number> [--strict]"
    echo ""
    echo "Examples:"
    echo "  $0 1"
    echo "  $0 2 --strict"
    exit 0
fi

STAGE_NUM="$1"
STRICT_MODE="${2:-}"
STAGE_FILE="docs/stages/stage-$(printf "%02d" "$STAGE_NUM")-*.md"

# Check if stage architecture file exists
echo -e "${BLUE}Verifying Stage $STAGE_NUM readiness...${NC}\n"

STAGE_PATH=$(find docs/stages -maxdepth 1 -name "stage-$(printf "%02d" "$STAGE_NUM")-*.md" 2>/dev/null | head -1)
if [[ -z "$STAGE_PATH" ]]; then
    echo -e "${RED}✗ Stage $STAGE_NUM architecture file not found${NC}"
    echo "  Expected: docs/stages/stage-$(printf "%02d" "$STAGE_NUM")-*.md"
    exit 1
fi

echo -e "${GREEN}✓ Stage $STAGE_NUM architecture file found:${NC}"
echo "  $STAGE_PATH"

# Check git status
echo ""
echo -e "${BLUE}Checking git status...${NC}"

# Ensure we're on main/master
CURRENT_BRANCH=$(git branch --show-current)
if [[ "$CURRENT_BRANCH" != "main" && "$CURRENT_BRANCH" != "master" ]]; then
    echo -e "${YELLOW}! Currently on branch: $CURRENT_BRANCH${NC}"
    echo "  (Not on main/master - may be finishing previous stage)"
fi

# Check for uncommitted changes
UNCOMMITTED=$(git status --porcelain | wc -l)
if [[ $UNCOMMITTED -gt 0 ]]; then
    echo -e "${RED}✗ Uncommitted changes found:${NC}"
    git status --short | sed 's/^/  /'

    if [[ "$STRICT_MODE" == "--strict" ]]; then
        echo -e "${RED}  Stage cannot proceed with uncommitted changes in strict mode${NC}"
        exit 1
    else
        echo -e "${YELLOW}  Warning: Proceeding with uncommitted changes${NC}"
    fi
else
    echo -e "${GREEN}✓ Working directory clean${NC}"
fi

# Check for staged but uncommitted changes
STAGED=$(git diff --cached --name-only | wc -l)
if [[ $STAGED -gt 0 ]]; then
    echo -e "${YELLOW}! Staged changes found:${NC}"
    git diff --cached --name-only | sed 's/^/  /'
fi

# Verify previous stage was completed (if not stage 1)
if [[ $STAGE_NUM -gt 1 ]]; then
    PREV_STAGE=$((STAGE_NUM - 1))
    PREV_STAGE_FILE=$(find docs/stages -maxdepth 1 -name "stage-$(printf "%02d" "$PREV_STAGE")-*.md" 2>/dev/null | head -1)

    if [[ -n "$PREV_STAGE_FILE" ]]; then
        if grep -q "Status: Complete" "$PREV_STAGE_FILE" 2>/dev/null; then
            echo -e "${GREEN}✓ Previous stage $PREV_STAGE marked complete${NC}"
        else
            echo -e "${YELLOW}! Previous stage $PREV_STAGE not marked complete in architecture file${NC}"
            echo "  (This is informational - proceeding with stage $STAGE_NUM)"
        fi
    fi
fi

echo ""
echo -e "${BLUE}Pre-stage verification complete.${NC}"
echo -e "${GREEN}Stage $STAGE_NUM is ready for implementation.${NC}"
echo ""
echo "Next step:"
echo "  1. Review stage architecture: $STAGE_PATH"
echo "  2. Create/checkout stage branch: git checkout -b stage/$(printf "%02d" "$STAGE_NUM")-\<stage-name\>"
echo "  3. Spawn implementation agent"
echo ""

exit 0
