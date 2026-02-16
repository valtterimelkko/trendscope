#!/bin/bash
#
# Stage Complexity Detector Script
# Analyzes stage architecture files to determine appropriate git workflow
#
# Usage:
#   ./detect-stage-complexity.sh
#   ./detect-stage-complexity.sh --verbose
#
# Exit codes:
#   0 = Analysis complete
#   1 = Stages not found or error
#
# Output: JSON-formatted analysis with recommendation

set -euo pipefail

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
NC='\033[0m'

VERBOSE="${1:-}"
STAGE_DIR="docs/stages"

# Check if stages exist
if [[ ! -d "$STAGE_DIR" ]]; then
    echo -e "${RED}Error: No $STAGE_DIR directory found${NC}"
    echo "Stages must be created before complexity detection"
    exit 1
fi

# Count stage files
STAGE_COUNT=$(find "$STAGE_DIR" -maxdepth 1 -name "stage-*.md" 2>/dev/null | wc -l)

if [[ $STAGE_COUNT -eq 0 ]]; then
    echo -e "${RED}Error: No stage files found in $STAGE_DIR${NC}"
    exit 1
fi

# Analysis function
analyze_stages() {
    local total_complexity=0
    local total_dependencies=0
    local max_affected_files=0
    local has_external_deps=false
    local parallelizable_count=0
    local sequential_only_count=0

    if [[ "$VERBOSE" == "--verbose" ]]; then
        echo -e "${BLUE}Analyzing $STAGE_COUNT stages...${NC}\n"
    fi

    for stage_file in "$STAGE_DIR"/stage-*.md; do
        local stage_name=$(basename "$stage_file")
        local complexity=0
        local affected_files=0

        # Count "Technical Components to Build" entries (higher = more complex)
        local components=$(grep -c "^-" "$stage_file" || true)
        complexity=$((components * 5))

        # Count "Depends on" entries
        local deps=$(grep -E "^\s*-\s+Stage|^\s*-\s+Phase|^\s*-\s+External" "$stage_file" | wc -l)
        total_dependencies=$((total_dependencies + deps))

        # Estimate affected files (rough: count mentions of "src/", "api/", "lib/", etc.)
        affected_files=$(grep -E "src/|api/|lib/|components/|pages/" "$stage_file" | wc -l)
        if [[ $affected_files -gt $max_affected_files ]]; then
            max_affected_files=$affected_files
        fi

        # Check for external integrations (stripe, supabase, oauth, etc.)
        if grep -qi "stripe\|supabase\|oauth\|external\|third.party\|webhook" "$stage_file"; then
            has_external_deps=true
            complexity=$((complexity + 15))
        fi

        # Check if stage can run in parallel (no database schema changes = parallelizable)
        if ! grep -qi "database.*schema\|migration\|sql" "$stage_file"; then
            parallelizable_count=$((parallelizable_count + 1))
        else
            sequential_only_count=$((sequential_only_count + 1))
        fi

        total_complexity=$((total_complexity + complexity))

        if [[ "$VERBOSE" == "--verbose" ]]; then
            printf "  %-40s complexity: %3d  deps: %d  files: %d\n" \
                "$stage_name" "$complexity" "$deps" "$affected_files"
        fi
    done

    # Calculate metrics
    local avg_complexity=$((total_complexity / STAGE_COUNT))
    local avg_dependencies=$((total_dependencies / STAGE_COUNT))

    # Determine recommendation
    local recommendation="single-branch"
    local reasoning=""

    # Decision logic:
    # - Simple & sequential: avg complexity < 40, max dependencies < 3, few affected files
    # - Complex: avg complexity >= 40, external deps, or schema changes needed
    if [[ $avg_complexity -lt 40 && $total_dependencies -lt 6 && $max_affected_files -lt 15 && "$sequential_only_count" -lt 2 ]]; then
        recommendation="single-branch"
        reasoning="Stages are simple, sequential, and affect isolated file sets. No worktree overhead needed."
    elif [[ $parallelizable_count -gt 2 && "$has_external_deps" == false ]]; then
        recommendation="single-branch"
        reasoning="Multiple stages can run in parallel with minimal conflicts. Single branch strategy sufficient."
    else
        recommendation="hybrid-worktrees"
        reasoning="Stages have external dependencies, schema changes, or high complexity. Worktrees provide safety for rollback."
    fi

    # Output JSON-formatted analysis
    cat <<EOF
{
  "analysis": {
    "total_stages": $STAGE_COUNT,
    "avg_complexity_score": $avg_complexity,
    "avg_dependencies": $avg_dependencies,
    "max_affected_files": $max_affected_files,
    "external_dependencies": $([ "$has_external_deps" = true ] && echo "true" || echo "false"),
    "stages_parallelizable": $parallelizable_count,
    "stages_sequential_only": $sequential_only_count
  },
  "recommendation": "$recommendation",
  "reasoning": "$reasoning",
  "strategy": {
    "use_worktrees": $([ "$recommendation" = "hybrid-worktrees" ] && echo "true" || echo "false"),
    "parallel_stages_safe": $([ $parallelizable_count -gt 2 ] && echo "true" || echo "false"),
    "verification_required": "always"
  }
}
EOF
}

# Main
if [[ $STAGE_COUNT -eq 0 ]]; then
    echo -e "${RED}No stages found. Cannot perform complexity analysis.${NC}"
    exit 1
fi

if [[ "$VERBOSE" == "--verbose" ]]; then
    echo -e "${BLUE}Stage Complexity Analysis${NC}"
    echo "=========================="
    echo ""
fi

analyze_stages

if [[ "$VERBOSE" == "--verbose" ]]; then
    echo ""
    echo -e "${BLUE}Analysis complete. Check JSON output above for strategy recommendation.${NC}"
fi

exit 0
