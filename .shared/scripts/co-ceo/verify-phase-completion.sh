#!/bin/bash
#
# Verify Phase Completion Script
# Checks if a phase has been completed based on expected deliverables
#
# Usage:
#   ./verify-phase-completion.sh <phase-id>
#   ./verify-phase-completion.sh --list
#   ./verify-phase-completion.sh --all
#
# Exit codes:
#   0 = Phase complete
#   1 = Phase incomplete
#   2 = Unknown phase or error

set -euo pipefail

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Phase definitions: phase_id -> expected files (colon-separated)
declare -A PHASE_FILES=(
    ["1.1"]="docs/concept/master-concept.md"
    ["1.2"]="docs/brand/brand-kit-guide.md"
    ["1.3"]="docs/concept/master-concept.md:docs/brand/brand-kit-guide.md"
    ["1.4"]="marketing/positioning-angles.md:marketing/keyword-research.md:marketing/lead-magnet.md:marketing/direct-response-copy.md:marketing/seo-content.md"
    ["1.5"]="docs/concept/master-concept.md:marketing/positioning-angles.md"
    ["2.1"]="docs/mvp-ux-*.md"
    ["2.2"]="docs/Project-Technical-Architecture.md"
    ["3.1"]="docs/concept/master-concept.md:docs/brand/brand-kit-guide.md:docs/mvp-ux-*.md:docs/Project-Technical-Architecture.md"
    ["4.1"]="docs/concept/master-concept.md"
    ["4.2"]="docs/selected-template.txt"
    ["4.2.5"]="docs/infrastructure-verified.json"
    ["4.3"]="docs/deployment-record.json:templates/*/frontend/styles/tokens.css"
    ["4.3.5"]="docs/supabase-security-audit.md"
    ["4.4"]="docs/stages/stage-*.md"
    ["5.1"]="docs/stages/stage-*.md:docs/Project-Technical-Architecture.md"
    ["6.1"]="docs/stages/stage-*.md"
    ["6.2"]="docs/Project-Technical-Architecture.md"
    ["6.9"]="docs/build-verification-report.md"
    ["7.1"]="docs/Project-Technical-Architecture.md"
)

# Phase names for display
declare -A PHASE_NAMES=(
    ["1.1"]="Master Concept Refinement"
    ["1.2"]="Brand Kit & Guide Creation"
    ["1.3"]="Service Naming & Domain"
    ["1.4"]="Marketing Foundation"
    ["1.5"]="Session Break (Optional)"
    ["2.1"]="MVP UX Design"
    ["2.2"]="Technical PRD & Git Structure"
    ["3.1"]="Consistency & Quality Check"
    ["4.1"]="Notion Database Building"
    ["4.2"]="User Approval & Template Selection"
    ["4.2.5"]="Infrastructure Prerequisites"
    ["4.3"]="Template Integration"
    ["4.3.5"]="Supabase Security Audit"
    ["4.4"]="Stage Architecture Planning"
    ["5.1"]="Architecture Consistency Check"
    ["6.1"]="Stage Execution"
    ["6.2"]="Security Review"
    ["6.9"]="Build Verification Gate"
    ["7.1"]="Final Validation & Handoff"
)

# Check if a file pattern exists
check_file_exists() {
    local pattern="$1"
    # Use find for safer pattern matching instead of ls with unquoted expansion
    # This handles special characters and glob patterns safely
    if [[ "$pattern" == *"*"* ]]; then
        # Pattern contains wildcard, use find with -path
        local dir
        local name
        dir=$(dirname "$pattern")
        name=$(basename "$pattern")
        [[ -d "$dir" ]] && find "$dir" -maxdepth 1 -name "$name" -print -quit 2>/dev/null | grep -q .
    else
        # No wildcard, just check if file exists
        [[ -f "$pattern" ]]
    fi
    return $?
}

# Verify a single phase
verify_phase() {
    local phase_id="$1"
    
    if [[ -z "${PHASE_FILES[$phase_id]:-}" ]]; then
        echo -e "${RED}Unknown phase: $phase_id${NC}"
        return 2
    fi
    
    local phase_name="${PHASE_NAMES[$phase_id]}"
    echo -e "${BLUE}Verifying Phase $phase_id: $phase_name${NC}"
    
    local files="${PHASE_FILES[$phase_id]}"
    local all_present=true
    local missing=()
    
    IFS=':' read -ra file_array <<< "$files"
    for file in "${file_array[@]}"; do
        if check_file_exists "$file"; then
            echo -e "  ${GREEN}✓${NC} $file"
        else
            echo -e "  ${RED}✗${NC} $file - MISSING"
            missing+=("$file")
            all_present=false
        fi
    done
    
    echo ""
    if [[ "$all_present" == true ]]; then
        echo -e "${GREEN}✓ Phase $phase_id complete${NC}"
        return 0
    else
        echo -e "${RED}✗ Phase $phase_id incomplete${NC}"
        echo "  Missing ${#missing[@]} file(s)"
        return 1
    fi
}

# List all phases and their status
list_phases() {
    echo -e "${BLUE}Phase Completion Status${NC}"
    echo "========================"
    echo ""
    
    local complete=0
    local incomplete=0
    
    for phase_id in $(echo "${!PHASE_NAMES[@]}" | tr ' ' '\n' | sort -V); do
        local phase_name="${PHASE_NAMES[$phase_id]}"
        local files="${PHASE_FILES[$phase_id]}"
        local status="${GREEN}✓${NC}"
        
        IFS=':' read -ra file_array <<< "$files"
        for file in "${file_array[@]}"; do
            if ! check_file_exists "$file"; then
                status="${RED}✗${NC}"
                break
            fi
        done
        
        if [[ "$status" == "${GREEN}✓${NC}" ]]; then
            complete=$((complete + 1))
        else
            incomplete=$((incomplete + 1))
        fi
        
        printf "  %s Phase %-5s %s\n" "$status" "$phase_id" "$phase_name"
    done
    
    echo ""
    echo "Summary: $complete complete, $incomplete incomplete"
}

# Verify all phases
verify_all() {
    echo -e "${BLUE}Verifying All Phases${NC}"
    echo "===================="
    echo ""
    
    local failed=0
    
    for phase_id in $(echo "${!PHASE_NAMES[@]}" | tr ' ' '\n' | sort -V); do
        verify_phase "$phase_id" || failed=$((failed + 1))
        echo ""
    done
    
    echo "===================="
    if [[ $failed -eq 0 ]]; then
        echo -e "${GREEN}All phases complete!${NC}"
        return 0
    else
        echo -e "${RED}$failed phase(s) incomplete${NC}"
        return 1
    fi
}

# Main
main() {
    if [[ $# -eq 0 ]]; then
        echo "Verify Phase Completion Script"
        echo ""
        echo "Usage:"
        echo "  $0 <phase-id>     # Verify specific phase (e.g., 1.1, 2.2)"
        echo "  $0 --list         # List all phases and status"
        echo "  $0 --all          # Verify all phases"
        echo ""
        echo "Available phases:"
        for phase_id in $(echo "${!PHASE_NAMES[@]}" | tr ' ' '\n' | sort -V); do
            echo "  $phase_id - ${PHASE_NAMES[$phase_id]}"
        done
        exit 0
    fi
    
    case "$1" in
        --list)
            list_phases
            ;;
        --all)
            verify_all
            ;;
        *)
            verify_phase "$1"
            ;;
    esac
}

main "$@"
