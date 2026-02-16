#!/bin/bash
#
# Load Phase Context Script
# Outputs the relevant skill content for a given phase
# Used by Co-CEO to load only the phase-specific instructions it needs
#
# Usage:
#   ./load-phase-context.sh <phase-id>
#   ./load-phase-context.sh --deps <phase-id>
#
# Exit codes:
#   0 = Success
#   1 = Phase not found
#   2 = Skill file not found

set -euo pipefail

# Colors for output (only when not piped)
if [[ -t 1 ]]; then
    GREEN='\033[0;32m'
    RED='\033[0;31m'
    YELLOW='\033[0;33m'
    BLUE='\033[0;34m'
    NC='\033[0m'
else
    GREEN=''
    RED=''
    YELLOW=''
    BLUE=''
    NC=''
fi

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SKILLS_DIR="$SCRIPT_DIR/../../skills/co-ceo-phases"

# Phase to skill mapping
declare -A PHASE_SKILLS=(
    ["1.1"]="phase-1-1-master-concept"
    ["1.2"]="phase-1-2-brand-kit"
    ["1.3"]="phase-1-3-naming-domain"
    ["1.4"]="phase-1-4-marketing-foundation"
    ["2.1"]="phase-2-1-ux-design"
    ["2.2"]="phase-2-2-technical-prd"
    ["3.1"]="phase-3-1-quality-gate"
    ["4.1"]="phase-4-1-notion-sync"
    ["4.2"]="phase-4-2-user-approval"
    ["4.2.5"]="phase-4-2-5-infrastructure-prerequisites"
    ["4.3"]="phase-4-3-template-integration"
    ["4.3.5"]="phase-4-3-5-supabase-security-audit"
    ["4.4"]="phase-4-4-stage-planning"
    ["5.1"]="phase-5-1-architecture-check"
    ["6.1"]="phase-6-1-stage-execution"
    ["6.2"]="phase-6-2-security-review"
    ["6.9"]="phase-6-9-build-verification"
    ["7.1"]="phase-7-1-completion"
)

# Phase dependencies
declare -A PHASE_DEPS=(
    ["1.1"]=""
    ["1.2"]="1.1"
    ["1.3"]="1.1:1.2"
    ["1.4"]="1.1:1.2:1.3"
    ["2.1"]="1.1:1.2:1.3:1.4"
    ["2.2"]="1.1:1.2:2.1"
    ["3.1"]="1.1:1.2:1.3:1.4:2.1:2.2"
    ["4.1"]="3.1"
    ["4.2"]="4.1"
    ["4.2.5"]="4.2"
    ["4.3"]="4.2.5"
    ["4.3.5"]="4.3"
    ["4.4"]="4.3.5"
    ["5.1"]="4.4:2.2"
    ["6.2"]="4.3.5:5.1"
    ["6.1"]="6.2"
    ["6.9"]="6.1:6.2"
    ["7.1"]="6.1:6.2:6.9"
)

# Load a phase skill
load_phase() {
    local phase_id="$1"
    
    if [[ -z "${PHASE_SKILLS[$phase_id]:-}" ]]; then
        echo -e "${RED}Unknown phase: $phase_id${NC}" >&2
        echo "" >&2
        echo "Available phases:" >&2
        for p in $(echo "${!PHASE_SKILLS[@]}" | tr ' ' '\n' | sort -V); do
            echo "  $p" >&2
        done
        return 1
    fi
    
    local skill_name="${PHASE_SKILLS[$phase_id]}"
    local skill_file="$SKILLS_DIR/$skill_name/SKILL.md"
    
    if [[ ! -f "$skill_file" ]]; then
        echo -e "${RED}Skill file not found: $skill_file${NC}" >&2
        return 2
    fi
    
    echo -e "${BLUE}=== Phase $phase_id Context ===${NC}"
    echo ""
    cat "$skill_file"
}

# Show phase dependencies
show_deps() {
    local phase_id="$1"
    
    if [[ -z "${PHASE_DEPS[$phase_id]:-}" ]]; then
        if [[ -z "${PHASE_SKILLS[$phase_id]:-}" ]]; then
            echo -e "${RED}Unknown phase: $phase_id${NC}" >&2
            return 1
        fi
        echo -e "${BLUE}Phase $phase_id has no dependencies${NC}"
        return 0
    fi
    
    local deps="${PHASE_DEPS[$phase_id]}"
    echo -e "${BLUE}Phase $phase_id dependencies:${NC}"
    
    IFS=':' read -ra dep_array <<< "$deps"
    for dep in "${dep_array[@]}"; do
        local skill_name="${PHASE_SKILLS[$dep]}"
        echo "  → Phase $dep ($skill_name)"
    done
}

# List all phases with their skills
list_phases() {
    echo -e "${BLUE}Phase to Skill Mapping${NC}"
    echo "======================"
    echo ""
    
    for phase_id in $(echo "${!PHASE_SKILLS[@]}" | tr ' ' '\n' | sort -V); do
        local skill_name="${PHASE_SKILLS[$phase_id]}"
        local skill_file="$SKILLS_DIR/$skill_name/SKILL.md"
        local status="${GREEN}✓${NC}"
        
        if [[ ! -f "$skill_file" ]]; then
            status="${RED}✗${NC}"
        fi
        
        printf "  %s Phase %-5s → %s\n" "$status" "$phase_id" "$skill_name"
    done
}

# Main
main() {
    if [[ $# -eq 0 ]]; then
        echo "Load Phase Context Script"
        echo ""
        echo "Usage:"
        echo "  $0 <phase-id>         # Load phase skill content"
        echo "  $0 --deps <phase-id>  # Show phase dependencies"
        echo "  $0 --list             # List all phases and skills"
        echo ""
        list_phases
        exit 0
    fi
    
    case "$1" in
        --deps)
            if [[ $# -lt 2 ]]; then
                echo "Usage: $0 --deps <phase-id>" >&2
                exit 1
            fi
            show_deps "$2"
            ;;
        --list)
            list_phases
            ;;
        *)
            load_phase "$1"
            ;;
    esac
}

main "$@"
