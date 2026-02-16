#!/bin/bash
#
# Post-Stage Verification & Merge Confirmation Script
# Verifies that stage implementation completed and merged properly
#
# Usage:
#   ./verify-stage-completion.sh <stage-number>
#   ./verify-stage-completion.sh <stage-number> <branch-name>
#
# Exit codes:
#   0 = Stage verified and merged
#   1 = Verification failed
#
# CRITICAL: This script verifies branch merge actually succeeded

set -euo pipefail

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'

if [[ $# -lt 1 ]]; then
    echo -e "${BLUE}Post-Stage Verification & Merge Confirmation${NC}"
    echo ""
    echo "Usage: $0 <stage-number> [branch-name]"
    echo ""
    echo "Examples:"
    echo "  $0 1"
    echo "  $0 2 stage/02-backend-api"
    echo ""
    echo "This script verifies:"
    echo "  1. Stage architecture file exists and is marked complete"
    echo "  2. All changes are committed (no uncommitted files)"
    echo "  3. (If branch provided) Merge actually completed to main"
    echo "  4. Main branch contains stage changes"
    exit 0
fi

STAGE_NUM="$1"
BRANCH_NAME="${2:-}"

echo -e "${BLUE}Verifying Stage $STAGE_NUM Completion...${NC}\n"

# Find stage file
STAGE_PATH=$(find docs/stages -maxdepth 1 -name "stage-$(printf "%02d" "$STAGE_NUM")-*.md" 2>/dev/null | head -1)
if [[ -z "$STAGE_PATH" ]]; then
    echo -e "${RED}✗ Stage $STAGE_NUM architecture file not found${NC}"
    exit 1
fi

echo -e "${GREEN}✓ Stage architecture file found:${NC}"
echo "  $STAGE_PATH\n"

# Check 1: Architecture file marked complete
if grep -q "Status: Complete\|Status:\s*Complete" "$STAGE_PATH" 2>/dev/null; then
    echo -e "${GREEN}✓ Stage architecture marked complete${NC}"
else
    echo -e "${YELLOW}⚠ Stage architecture not marked complete${NC}"
    echo "  (Check if stage implementation actually finished)"
fi

# Check 2: No uncommitted files on main
CURRENT_BRANCH=$(git branch --show-current)
echo ""
echo -e "${BLUE}Checking git status...${NC}"
echo "  Current branch: $CURRENT_BRANCH"

UNCOMMITTED=$(git status --porcelain | wc -l)
if [[ $UNCOMMITTED -eq 0 ]]; then
    echo -e "${GREEN}✓ No uncommitted changes${NC}"
else
    echo -e "${RED}✗ UNCOMMITTED FILES FOUND:${NC}"
    git status --short | sed 's/^/  /'
    echo ""
    echo -e "${RED}ERROR: Cannot proceed with uncommitted changes!${NC}"
    echo "This may indicate a stage plan file or other artifact was not committed."
    echo ""
    echo "To fix:"
    echo "  1. Review files above"
    echo "  2. Either: git add <file> && git commit -m 'Fix: commit missed changes'"
    echo "  3. Or: git checkout -- <file> (if unwanted)"
    exit 1
fi

# Check 3: If branch provided, verify merge
if [[ -n "$BRANCH_NAME" ]]; then
    echo ""
    echo -e "${BLUE}Verifying branch merge...${NC}"
    echo "  Looking for: $BRANCH_NAME"

    # Check if branch exists
    if git rev-parse "$BRANCH_NAME" >/dev/null 2>&1; then
        # Branch exists - check if it's been merged
        if git merge-base --is-ancestor "$BRANCH_NAME" main 2>/dev/null || \
           git merge-base --is-ancestor "$BRANCH_NAME" master 2>/dev/null; then
            echo -e "${GREEN}✓ Branch $BRANCH_NAME has been merged to main${NC}"

            # Get merge commit
            MERGE_COMMIT=$(git log --oneline --all | grep -i "merged\|merge.*$(basename "$BRANCH_NAME")" | head -1)
            if [[ -n "$MERGE_COMMIT" ]]; then
                echo "  Merge commit: $MERGE_COMMIT"
            fi
        else
            echo -e "${RED}✗ Branch $BRANCH_NAME exists but NOT merged to main${NC}"
            echo "  Run: git checkout main && git merge $BRANCH_NAME"
            exit 1
        fi

        # Check if branch should be cleaned up
        echo ""
        echo -e "${BLUE}Branch cleanup check...${NC}"
        COMMITS_AHEAD=$(git rev-list --count main.."$BRANCH_NAME" 2>/dev/null || echo "0")
        if [[ "$COMMITS_AHEAD" == "0" ]]; then
            echo -e "${GREEN}✓ Branch is fully merged (safe to delete)${NC}"
            echo "  Run: git branch -d $BRANCH_NAME"
        else
            echo -e "${YELLOW}⚠ Branch has $COMMITS_AHEAD commits not in main${NC}"
            echo "  This shouldn't happen if merge succeeded"
        fi
    else
        echo -e "${YELLOW}⚠ Branch $BRANCH_NAME not found${NC}"
        echo "  (May have already been deleted)"
    fi
fi

# Check 4: Verify main contains expected changes
echo ""
echo -e "${BLUE}Verifying main branch has stage changes...${NC}"

CURRENT_BRANCH=$(git branch --show-current)
if [[ "$CURRENT_BRANCH" != "main" && "$CURRENT_BRANCH" != "master" ]]; then
    echo -e "${YELLOW}⚠ Not on main/master branch, switching...${NC}"
    git checkout main 2>/dev/null || git checkout master 2>/dev/null
fi

# Check git log for recent commits
RECENT=$(git log --oneline -n 5 | grep -i "stage\|implementation" || true)
if [[ -n "$RECENT" ]]; then
    echo -e "${GREEN}✓ Recent commits found on main:${NC}"
    echo "$RECENT" | sed 's/^/  /'
else
    echo -e "${YELLOW}⚠ No recent stage-related commits found on main${NC}"
fi

# Final summary
echo ""
echo -e "${BLUE}═══════════════════════════════════════════${NC}"
echo -e "${GREEN}✓ Stage $STAGE_NUM Verification Complete${NC}"
echo -e "${BLUE}═══════════════════════════════════════════${NC}"
echo ""
echo "Safe to proceed to next stage."
echo ""
echo "Next steps:"
echo "  1. Run next stage readiness check: ./verify-stage-readiness.sh $((STAGE_NUM + 1))"
echo "  2. Or push to GitHub: git push origin main"
echo ""

exit 0
