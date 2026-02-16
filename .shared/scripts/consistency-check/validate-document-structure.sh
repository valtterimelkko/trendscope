#!/bin/bash
#
# Document Structure Validator
# Validates that documents have required sections based on their type
#
# Usage:
#   ./validate-document-structure.sh docs/
#   ./validate-document-structure.sh docs/concept/master-concept.md
#   ./validate-document-structure.sh --json docs/
#   ./validate-document-structure.sh --quiet docs/
#
# Options:
#   --json    Output results as JSON
#   --quiet   Minimal output (only errors)
#
# Exit codes:
#   0 = All documents valid
#   1 = Some documents have issues
#   2 = No documents found or error

set -euo pipefail

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Track overall status
ERRORS_FOUND=0
JSON_OUTPUT=false
QUIET_MODE=false

# JSON accumulator
declare -a JSON_RESULTS=()

# Parse arguments
parse_args() {
    while [[ $# -gt 0 ]]; do
        case "$1" in
            --json)
                JSON_OUTPUT=true
                shift
                ;;
            --quiet)
                QUIET_MODE=true
                shift
                ;;
            -*)
                echo "Unknown option: $1" >&2
                exit 2
                ;;
            *)
                TARGET="$1"
                shift
                ;;
        esac
    done
}

TARGET=""

# Output helpers
log_info() {
    if [[ "$JSON_OUTPUT" == false && "$QUIET_MODE" == false ]]; then
        echo -e "$1"
    fi
}

log_result() {
    local file="$1"
    local status="$2"
    local message="$3"
    local missing="$4"
    
    if [[ "$JSON_OUTPUT" == true ]]; then
        local missing_json="[]"
        if [[ -n "$missing" ]]; then
            missing_json="[\"${missing//,/\",\"}\"]"
        fi
        JSON_RESULTS+=("{\"file\":\"$file\",\"status\":\"$status\",\"message\":\"$message\",\"missing\":$missing_json}")
    fi
}

# Detect document type
detect_document_type() {
    local file="$1"
    local filename
    filename=$(basename "$file")
    local dir
    dir=$(dirname "$file")
    
    # Check if file is in marketing folder
    if [[ "$dir" == *"/marketing"* ]] || [[ "$dir" == "marketing" ]]; then
        case "$filename" in
            "positioning-angles.md") echo "marketing-positioning" ;;
            "keyword-research.md") echo "marketing-keywords" ;;
            "lead-magnet.md") echo "marketing-lead-magnet" ;;
            "direct-response-copy.md") echo "marketing-direct-response" ;;
            "seo-content.md") echo "marketing-seo" ;;
            *) echo "marketing-other" ;;
        esac
        return
    fi
    
    if [[ "$filename" == *"master-concept"* ]]; then
        echo "master-concept"
    elif [[ "$filename" == *"brand"* ]]; then
        echo "brand-kit"
    elif [[ "$filename" == *"ux"* ]]; then
        echo "ux-design"
    elif [[ "$filename" == *"Technical-Architecture"* ]] || [[ "$filename" == *"PRD"* ]]; then
        echo "technical-prd"
    elif [[ "$filename" == "stage-"* ]]; then
        echo "stage-architecture"
    else
        echo "unknown"
    fi
}

# Validate a single document
validate_document() {
    local file="$1"
    local doc_type
    doc_type=$(detect_document_type "$file")
    
    if [[ "$doc_type" == "unknown" ]]; then
        if [[ "$JSON_OUTPUT" == false && "$QUIET_MODE" == false ]]; then
            echo -e "${YELLOW}⚠ Skipping unknown document type: $file${NC}"
        fi
        return 0
    fi
    
    log_info "${BLUE}Validating: $file (type: $doc_type)${NC}"
    
    local content
    content=$(cat "$file")
    local missing=()
    
    # Define sections to check based on document type
    local sections_to_check=""
    case "$doc_type" in
        "master-concept")
            sections_to_check="Executive Summary|Problem|Target Audience|Solution|MVP Scope|Must Have|Won't Have|Metrics|Risk"
            ;;
        "brand-kit")
            sections_to_check="Logo|Color|Typography|Voice|Tone"
            ;;
        "ux-design")
            sections_to_check="Overview|User Flow|Screen|Accessibility"
            ;;
        "technical-prd")
            sections_to_check="Executive Summary|Steel Thread|Critical User Journey|Database|API|Implementation|Stage"
            ;;
        "stage-architecture")
            sections_to_check="Overview|Dependencies|Technical Components|Testing|Critical Constraints|Progress Log|Issues"
            ;;
        "marketing-positioning")
            sections_to_check="Position|Angle|Headline|Target|Value Proposition"
            ;;
        "marketing-keywords")
            sections_to_check="Keyword|Priority|Intent|Volume|Competition"
            ;;
        "marketing-lead-magnet")
            sections_to_check="Lead Magnet|Target|Format|Hook|Delivery"
            ;;
        "marketing-direct-response")
            sections_to_check="Headline|CTA|Pain|Benefit|Urgency"
            ;;
        "marketing-seo")
            sections_to_check="Content|Strategy|Topic|Calendar|Pillar"
            ;;
        "marketing-other")
            # Skip unknown marketing files
            sections_to_check=""
            ;;
    esac
    
    # Check each required section
    IFS='|' read -ra sections_array <<< "$sections_to_check"
    for section in "${sections_array[@]}"; do
        if ! echo "$content" | grep -qi "$section"; then
            missing+=("$section")
        fi
    done
    
    # Report results
    if [[ ${#missing[@]} -eq 0 ]]; then
        if [[ "$JSON_OUTPUT" == false && "$QUIET_MODE" == false ]]; then
            echo -e "  ${GREEN}✓ All required sections present${NC}"
        fi
        log_result "$file" "pass" "All required sections present" ""
        return 0
    else
        if [[ "$JSON_OUTPUT" == false ]]; then
            echo -e "  ${RED}✗ Missing sections:${NC}"
            for section in "${missing[@]}"; do
                echo -e "    - $section"
            done
        fi
        local missing_str
        missing_str=$(IFS=','; echo "${missing[*]}")
        log_result "$file" "fail" "Missing sections" "$missing_str"
        ERRORS_FOUND=1
        return 1
    fi
}

# Process directory
process_directory() {
    local dir="$1"
    local found_docs=0
    
    # Find all markdown files
    while IFS= read -r -d '' file; do
        found_docs=$((found_docs + 1))
        validate_document "$file" || true
        log_info ""
    done < <(find "$dir" -name "*.md" -type f -print0)
    
    if [[ $found_docs -eq 0 ]]; then
        if [[ "$JSON_OUTPUT" == true ]]; then
            echo "{\"error\": \"No markdown files found in $dir\"}"
        else
            echo -e "${RED}No markdown files found in $dir${NC}"
        fi
        exit 2
    fi
}

# Output JSON
output_json() {
    echo "{"
    echo "  \"status\": \"$([ $ERRORS_FOUND -eq 0 ] && echo 'pass' || echo 'fail')\","
    echo "  \"results\": ["
    local first=true
    for result in "${JSON_RESULTS[@]}"; do
        if [[ "$first" == true ]]; then
            first=false
        else
            echo ","
        fi
        echo -n "    $result"
    done
    echo ""
    echo "  ]"
    echo "}"
}

# Main
main() {
    parse_args "$@"
    
    if [[ -z "$TARGET" ]]; then
        echo "Document Structure Validator"
        echo ""
        echo "Usage:"
        echo "  $0 [options] path/to/docs/"
        echo "  $0 [options] path/to/document.md"
        echo ""
        echo "Options:"
        echo "  --json    Output results as JSON"
        echo "  --quiet   Minimal output (only errors)"
        exit 0
    fi
    
    log_info "${BLUE}Document Structure Validation${NC}"
    log_info "================================"
    log_info ""
    
    if [[ -d "$TARGET" ]]; then
        process_directory "$TARGET"
    elif [[ -f "$TARGET" ]]; then
        validate_document "$TARGET"
    else
        if [[ "$JSON_OUTPUT" == true ]]; then
            echo "{\"error\": \"$TARGET not found\"}"
        else
            echo -e "${RED}Error: $TARGET not found${NC}"
        fi
        exit 2
    fi
    
    if [[ "$JSON_OUTPUT" == true ]]; then
        output_json
    else
        log_info "================================"
        if [[ $ERRORS_FOUND -eq 1 ]]; then
            echo -e "${RED}❌ Some documents have missing sections${NC}"
        else
            echo -e "${GREEN}✅ All documents valid${NC}"
        fi
    fi
    
    exit $ERRORS_FOUND
}

main "$@"
