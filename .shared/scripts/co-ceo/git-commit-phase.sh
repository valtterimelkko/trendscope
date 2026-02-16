#!/bin/bash
#
# Git Commit Phase Script
# Commits changes after a phase completes with standardized message format
#
# Usage:
#   ./git-commit-phase.sh <phase-id> <deliverable-name> [--push]
#
# Examples:
#   ./git-commit-phase.sh "1.1" "Master Concept created and validated"
#   ./git-commit-phase.sh "1.2" "Brand Kit created" --push
#
# Exit codes:
#   0 = Success
#   1 = No changes to commit
#   2 = Error

set -euo pipefail

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Validate arguments
if [[ $# -lt 2 ]]; then
    echo -e "${BLUE}Git Commit Phase Script${NC}"
    echo ""
    echo "Usage:"
    echo "  $0 <phase-id> <deliverable-name> [--push]"
    echo ""
    echo "Examples:"
    echo "  $0 \"1.1\" \"Master Concept created and validated\""
    echo "  $0 \"1.2\" \"Brand Kit created\" --push"
    exit 0
fi

PHASE_ID="$1"
DELIVERABLE="$2"
DO_PUSH=false

if [[ "${3:-}" == "--push" ]]; then
    DO_PUSH=true
fi

# Check git status
echo -e "${BLUE}Checking git status...${NC}"
STATUS=$(git status --porcelain)

if [[ -z "$STATUS" ]]; then
    echo -e "${YELLOW}No changes to commit${NC}"
    exit 1
fi

# Stage all changes
echo -e "${BLUE}Staging changes...${NC}"
git add -A

# Create commit with phase context
COMMIT_MSG="[Phase $PHASE_ID] $DELIVERABLE"
echo -e "${BLUE}Creating commit: $COMMIT_MSG${NC}"
git commit -m "$COMMIT_MSG"

echo -e "${GREEN}✓ Committed successfully${NC}"

# Optional push
if [[ "$DO_PUSH" == true ]]; then
    BRANCH=$(git branch --show-current)
    echo -e "${BLUE}Pushing to origin/$BRANCH...${NC}"
    if git push origin "$BRANCH" 2>/dev/null; then
        echo -e "${GREEN}✓ Pushed to GitHub${NC}"
    else
        echo -e "${YELLOW}! Push failed (remote may not be configured)${NC}"
        echo "  To set up remote: git remote add origin <URL>"
        echo "  Then push: git push -u origin $BRANCH"
    fi
else
    BRANCH=$(git branch --show-current)
    echo ""
    echo -e "${BLUE}To push to GitHub:${NC}"
    echo "  git push origin $BRANCH"
fi
