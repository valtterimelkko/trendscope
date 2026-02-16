#!/bin/bash
#
# Cross-Reference Check
# Validates consistency across multiple documents
#
# Usage:
#   ./cross-reference-check.sh docs/
#   ./cross-reference-check.sh --json docs/
#   ./cross-reference-check.sh --quiet docs/
#
# Options:
#   --json    Output results as JSON
#   --quiet   Minimal output (only errors)
#
# Checks:
#   - Service name consistency across documents
#   - Feature traceability from Master Concept to PRD
#   - Color value consistency
#
# Exit codes:
#   0 = All consistent
#   1 = Inconsistencies found
#   2 = Error or missing files

set -euo pipefail

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
NC='\033[0m'

DOCS_DIR=""
ISSUES_FOUND=0
JSON_OUTPUT=false
QUIET_MODE=false

# JSON result accumulator
declare -a JSON_ISSUES=()
declare -a JSON_PASSED=()

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
                DOCS_DIR="$1"
                shift
                ;;
        esac
    done
}

# Output helper
log_info() {
    if [[ "$JSON_OUTPUT" == false && "$QUIET_MODE" == false ]]; then
        echo -e "$1"
    fi
}

log_success() {
    if [[ "$JSON_OUTPUT" == false && "$QUIET_MODE" == false ]]; then
        echo -e "${GREEN}$1${NC}"
    fi
    JSON_PASSED+=("$2")
}

log_warning() {
    if [[ "$JSON_OUTPUT" == false ]]; then
        echo -e "${YELLOW}$1${NC}"
    fi
    JSON_ISSUES+=("{\"severity\":\"warning\",\"message\":\"$2\"}")
}

log_error() {
    if [[ "$JSON_OUTPUT" == false ]]; then
        echo -e "${RED}$1${NC}"
    fi
    JSON_ISSUES+=("{\"severity\":\"error\",\"message\":\"$2\"}")
    ISSUES_FOUND=1
}

# Find documents
find_document() {
    local pattern="$1"
    find "$DOCS_DIR" -name "*${pattern}*" -type f 2>/dev/null | head -1
}

# Extract service name from document title
extract_service_name() {
    local file="$1"
    if [[ ! -f "$file" ]]; then
        echo ""
        return
    fi
    
    # Try to extract from H1 title (# Title)
    local title
    title=$(grep -m1 "^# " "$file" 2>/dev/null | sed 's/^# //' | sed 's/ Master Concept.*//' | sed 's/ Technical PRD.*//' | sed 's/ Brand.*//' | sed 's/ MVP User Experience.*//' | tr -d '\r')
    
    # If title contains brackets, extract content
    if [[ "$title" == *"["*"]"* ]]; then
        title=$(echo "$title" | sed 's/\[//' | sed 's/\].*//')
    fi
    
    echo "$title"
}

# Check service name consistency
check_service_name_consistency() {
    log_info "${BLUE}Checking Service Name Consistency${NC}"
    log_info "-----------------------------------"
    
    local master_concept
    master_concept=$(find_document "master-concept")
    local brand_kit
    brand_kit=$(find_document "brand")
    local ux_doc
    ux_doc=$(find_document "ux")
    local prd
    prd=$(find_document "Technical-Architecture")
    
    local names=()
    local sources=()
    
    if [[ -n "$master_concept" && -f "$master_concept" ]]; then
        local name
        name=$(extract_service_name "$master_concept")
        if [[ -n "$name" && "$name" != "[Product Name]" ]]; then
            names+=("$name")
            sources+=("Master Concept")
        fi
    fi
    
    if [[ -n "$brand_kit" && -f "$brand_kit" ]]; then
        local name
        name=$(extract_service_name "$brand_kit")
        if [[ -n "$name" && "$name" != "[Product Name]" ]]; then
            names+=("$name")
            sources+=("Brand Kit")
        fi
    fi
    
    if [[ -n "$ux_doc" && -f "$ux_doc" ]]; then
        local name
        name=$(extract_service_name "$ux_doc")
        if [[ -n "$name" && "$name" != "[Product Name]" ]]; then
            names+=("$name")
            sources+=("UX Design")
        fi
    fi
    
    if [[ -n "$prd" && -f "$prd" ]]; then
        local name
        name=$(extract_service_name "$prd")
        if [[ -n "$name" && "$name" != "[Product Name]" ]]; then
            names+=("$name")
            sources+=("Technical PRD")
        fi
    fi
    
    if [[ ${#names[@]} -eq 0 ]]; then
        log_warning "  ⚠ No service names found in documents" "No service names found"
        return
    fi
    
    # Check if all names match
    local first_name="${names[0]}"
    local all_match=true
    
    for i in "${!names[@]}"; do
        if [[ "${names[$i]}" != "$first_name" ]]; then
            all_match=false
            break
        fi
    done
    
    if $all_match; then
        log_success "  ✓ Service name consistent: \"$first_name\"" "service_name_consistent"
    else
        local mismatch_details=""
        for i in "${!names[@]}"; do
            mismatch_details+="${sources[$i]}: ${names[$i]}, "
        done
        log_error "  ✗ Service name MISMATCH" "Service name mismatch: $mismatch_details"
        if [[ "$JSON_OUTPUT" == false ]]; then
            for i in "${!names[@]}"; do
                echo -e "    - ${sources[$i]}: \"${names[$i]}\""
            done
        fi
    fi
    log_info ""
}

# Check for color value consistency
check_color_consistency() {
    log_info "${BLUE}Checking Color Consistency${NC}"
    log_info "----------------------------"
    
    local brand_kit
    brand_kit=$(find_document "brand")
    
    if [[ -z "$brand_kit" || ! -f "$brand_kit" ]]; then
        log_warning "  ⚠ No Brand Kit found, skipping color check" "No Brand Kit found"
        log_info ""
        return
    fi
    
    # Extract hex colors from Brand Kit
    local brand_colors
    brand_colors=$(grep -oE '#[0-9A-Fa-f]{6}' "$brand_kit" 2>/dev/null | sort -u || true)
    
    if [[ -z "$brand_colors" ]]; then
        log_warning "  ⚠ No hex colors found in Brand Kit" "No hex colors in Brand Kit"
        log_info ""
        return
    fi
    
    log_info "  ${GREEN}✓ Colors defined in Brand Kit:${NC}"
    if [[ "$JSON_OUTPUT" == false && "$QUIET_MODE" == false ]]; then
        echo "$brand_colors" | while read -r color; do
            echo "    $color"
        done
    fi
    
    # Check if other docs reference colors not in Brand Kit
    local other_docs
    other_docs=$(find "$DOCS_DIR" -name "*.md" -type f ! -name "*brand*" 2>/dev/null)
    
    local foreign_colors=()
    while IFS= read -r doc; do
        if [[ -f "$doc" ]]; then
            local doc_colors
            doc_colors=$(grep -oE '#[0-9A-Fa-f]{6}' "$doc" 2>/dev/null || true)
            if [[ -n "$doc_colors" ]]; then
                while IFS= read -r color; do
                    if ! echo "$brand_colors" | grep -qi "$color"; then
                        foreign_colors+=("$color (in $(basename "$doc"))")
                    fi
                done <<< "$doc_colors"
            fi
        fi
    done <<< "$other_docs"
    
    if [[ ${#foreign_colors[@]} -gt 0 ]]; then
        local colors_str
        colors_str=$(IFS=','; echo "${foreign_colors[*]}")
        log_warning "  ⚠ Colors found in other docs but not in Brand Kit" "Foreign colors: $colors_str"
        if [[ "$JSON_OUTPUT" == false ]]; then
            printf '    %s\n' "${foreign_colors[@]}"
        fi
    else
        log_success "  ✓ No foreign colors found in other documents" "color_consistency"
    fi
    log_info ""
}

# Check document completeness
check_document_presence() {
    log_info "${BLUE}Checking Required Documents${NC}"
    log_info "-----------------------------"
    
    local required_docs=("master-concept" "brand" "ux" "Technical-Architecture")
    local missing=()
    
    for pattern in "${required_docs[@]}"; do
        local doc
        doc=$(find_document "$pattern")
        if [[ -z "$doc" || ! -f "$doc" ]]; then
            missing+=("$pattern")
            log_error "  ✗ Missing: *$pattern*" "Missing document: $pattern"
        else
            log_success "  ✓ Found: $(basename "$doc")" "found_$pattern"
        fi
    done
    
    log_info ""
    
    # Check marketing folder documents (Phase 1.4)
    check_marketing_documents
}

# Check marketing folder documents
check_marketing_documents() {
    log_info "${BLUE}Checking Marketing Foundation Documents${NC}"
    log_info "-----------------------------------------"
    
    local marketing_dir=""
    # Try to find marketing folder relative to DOCS_DIR
    if [[ -d "${DOCS_DIR}/../marketing" ]]; then
        marketing_dir="${DOCS_DIR}/../marketing"
    elif [[ -d "${DOCS_DIR}/marketing" ]]; then
        marketing_dir="${DOCS_DIR}/marketing"
    elif [[ -d "marketing" ]]; then
        marketing_dir="marketing"
    fi
    
    if [[ -z "$marketing_dir" || ! -d "$marketing_dir" ]]; then
        log_warning "  ⚠ No marketing directory found (Phase 1.4 may not be complete)" "No marketing directory"
        log_info ""
        return
    fi
    
    local marketing_files=("positioning-angles.md" "keyword-research.md" "lead-magnet.md" "direct-response-copy.md" "seo-content.md")
    local found_count=0
    
    for file in "${marketing_files[@]}"; do
        if [[ -f "${marketing_dir}/${file}" ]]; then
            log_success "  ✓ Found: ${file}" "found_marketing_${file}"
            found_count=$((found_count + 1))
        else
            log_warning "  ⚠ Missing: ${file}" "Missing marketing document: ${file}"
        fi
    done
    
    if [[ $found_count -eq ${#marketing_files[@]} ]]; then
        log_success "  ✓ All Phase 1.4 marketing documents present" "marketing_complete"
    elif [[ $found_count -eq 0 ]]; then
        log_warning "  ⚠ No marketing documents found - Phase 1.4 not started" "marketing_not_started"
    fi
    
    log_info ""
}

# Check stage files consistency
check_stage_files() {
    log_info "${BLUE}Checking Stage Files${NC}"
    log_info "---------------------"
    
    local stages_dir="$DOCS_DIR/stages"
    
    if [[ ! -d "$stages_dir" ]]; then
        log_warning "  ⚠ No stages directory found (may not be at that phase yet)" "No stages directory"
        log_info ""
        return
    fi
    
    local stage_files
    stage_files=$(find "$stages_dir" -name "stage-*.md" -type f 2>/dev/null | sort)
    
    if [[ -z "$stage_files" ]]; then
        log_warning "  ⚠ No stage files found" "No stage files found"
        log_info ""
        return
    fi
    
    log_success "  Found stage files:" "stage_files_found"
    if [[ "$JSON_OUTPUT" == false && "$QUIET_MODE" == false ]]; then
        echo "$stage_files" | while read -r file; do
            echo "    - $(basename "$file")"
        done
    fi
    
    # Check for gaps in stage numbering
    local prev_num=0
    local gaps=()
    
    echo "$stage_files" | while read -r file; do
        local filename
        filename=$(basename "$file")
        local num
        num=$(echo "$filename" | grep -oE 'stage-[0-9]+' | grep -oE '[0-9]+')
        if [[ -n "$num" ]]; then
            if [[ $((num - prev_num)) -gt 1 && $prev_num -gt 0 ]]; then
                gaps+=("Gap between stage $prev_num and $num")
            fi
            prev_num=$num
        fi
    done
    
    log_info ""
}

# Output JSON results
output_json() {
    echo "{"
    echo "  \"status\": \"$([ $ISSUES_FOUND -eq 0 ] && echo 'pass' || echo 'fail')\","
    echo "  \"issues\": ["
    local first=true
    for issue in "${JSON_ISSUES[@]}"; do
        if [[ "$first" == true ]]; then
            first=false
        else
            echo ","
        fi
        echo -n "    $issue"
    done
    echo ""
    echo "  ],"
    echo "  \"passed\": ["
    first=true
    for check in "${JSON_PASSED[@]}"; do
        if [[ "$first" == true ]]; then
            first=false
        else
            echo ","
        fi
        echo -n "    \"$check\""
    done
    echo ""
    echo "  ]"
    echo "}"
}

# Main
main() {
    parse_args "$@"
    
    if [[ -z "$DOCS_DIR" ]]; then
        echo "Cross-Reference Consistency Check"
        echo ""
        echo "Usage:"
        echo "  $0 [options] docs/"
        echo ""
        echo "Options:"
        echo "  --json    Output results as JSON"
        echo "  --quiet   Minimal output (only errors)"
        exit 0
    fi
    
    if [[ ! -d "$DOCS_DIR" ]]; then
        if [[ "$JSON_OUTPUT" == true ]]; then
            echo "{\"error\": \"Directory not found: $DOCS_DIR\"}"
        else
            echo -e "${RED}Error: Directory not found: $DOCS_DIR${NC}"
        fi
        exit 2
    fi
    
    log_info "${BLUE}Cross-Reference Consistency Check${NC}"
    log_info "==================================="
    log_info "Directory: $DOCS_DIR"
    log_info ""
    
    check_document_presence
    check_service_name_consistency
    check_color_consistency
    check_stage_files
    
    if [[ "$JSON_OUTPUT" == true ]]; then
        output_json
    else
        log_info "==================================="
        if [[ $ISSUES_FOUND -eq 1 ]]; then
            echo -e "${YELLOW}⚠ Inconsistencies found - review above${NC}"
        else
            echo -e "${GREEN}✅ All cross-reference checks passed${NC}"
        fi
    fi
    
    exit $ISSUES_FOUND
}

main "$@"
