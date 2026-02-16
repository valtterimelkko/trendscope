#!/bin/bash
#
# Master Concept Document Validator
# Checks a Master Concept document for completeness and structure
#
# Usage:
#   ./validate-concept.sh path/to/master-concept.md
#   ./validate-concept.sh --generate-template [output-path]
#
# Exit codes:
#   0 = All required sections present
#   1 = Missing required sections
#   2 = File not found or error

set -euo pipefail

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Required sections (must be present)
REQUIRED_SECTIONS=(
    "Executive Summary"
    "Problem Statement"
    "Target Audience"
    "Solution Vision"
    "MVP Scope"
    "Must Have"
    "Won't Have"
    "Business Model"
    "Key Metrics"
    "Risks"
    "Critical Assumptions"
)

# Recommended sections (warn if missing)
RECOMMENDED_SECTIONS=(
    "Current State"
    "Why Now"
    "Job to Be Done"
    "Unique Value Proposition"
    "User Journey"
    "Should Have"
    "Could Have"
    "Riskiest Assumption"
    "Validation Plan"
    "FAQ"
)

# Generate template function
generate_template() {
    local output="${1:-docs/concept/master-concept.md}"
    
    cat << 'TEMPLATE'
# [Product Name] Master Concept

## Executive Summary
*One paragraph elevator pitch explaining the product, target user, and key value.*

---

## Problem Statement & Market Context

### The Pain
*What specific problem are we solving? Describe the user's pain point in concrete terms.*

### Current State
*How is this problem solved today? What competitors or workarounds exist?*

### Why Now?
*What market shift, technology change, or opportunity makes this the right time?*

---

## Target Audience

### Primary Persona
*Who is the early adopter? Describe behavioral characteristics, not just demographics.*

*Example: "Solo SaaS founders who are technical but time-constrained, actively building products and frustrated by context-switching between tools."*

### Job to Be Done
*What is the user trying to accomplish? What struggle/friction prevents them?*

*Format: "When [situation], I want to [motivation], so I can [expected outcome]."*

---

## Solution Vision

### The Concept
*High-level description. Use an analogy if helpful (e.g., "Uber for X").*

### Unique Value Proposition
*Why is this better than the status quo? What's the key differentiator?*

### User Journey
*Narrative "Day in the Life" walkthrough showing the transformed experience.*

*Example: "Sarah opens the app on her morning commute. Instead of checking three different apps for updates, she sees a unified dashboard showing..."*

---

## MVP Scope (MoSCoW)

### Must Have
*Non-negotiable features. Without these, the product doesn't work.*
- [ ] Feature 1: *Description*
- [ ] Feature 2: *Description*

### Should Have
*Important features, but product works without them. First to cut if timeline slips.*
- [ ] Feature 1: *Description*

### Could Have
*Nice-to-haves. Include only if time permits.*
- [ ] Feature 1: *Description*

### Won't Have
*Explicit exclusions for MVP. Critical for preventing scope creep.*
- Feature 1: *Why excluded*
- Feature 2: *Why excluded*

---

## Business Model & Success Metrics

### Revenue Model
*How does the product capture value? (SaaS subscription, freemium, transactional, etc.)*

### Key Metrics (KPIs)
*3-5 measurable indicators of success.*

| Metric | Definition | Target |
|--------|------------|--------|
| **North Star:** [Metric] | *What this measures* | *Target value* |
| Metric 2 | *What this measures* | *Target value* |
| Metric 3 | *What this measures* | *Target value* |

---

## Risks & Assumptions

### Critical Assumptions
*What must be true for this product to succeed?*
1. *Assumption 1*
2. *Assumption 2*
3. *Assumption 3*

### Riskiest Assumption
*The one belief that, if false, kills the entire project.*

*Example: "Users are willing to pay for a dedicated tool when free alternatives exist."*

### Validation Plan
*How will we test critical assumptions before building?*
- [ ] *Validation method 1 (e.g., landing page smoke test)*
- [ ] *Validation method 2 (e.g., user interviews)*

### Constraints
*Known limitations that affect scope.*
- **Budget:** *$X*
- **Timeline:** *X weeks/months*
- **Team:** *X developers*
- **Technical:** *Must integrate with Y, run on Z*

---

## FAQ

### External (User Questions)
*What would potential users ask?*

**Q: How much does it cost?**
A: *Answer*

**Q: Can I export my data?**
A: *Answer*

### Internal (Stakeholder Questions)
*Tough questions from the team.*

**Q: Why is this a strategic priority?**
A: *Answer*

**Q: What's the path to profitability?**
A: *Answer*

---

*Document created: [Date]*
*Last updated: [Date]*
*Status: Draft / Under Review / Approved*
TEMPLATE
}

# Check if section heading exists (efficient single-pass)
section_exists() {
    local section="$1"
    local content="$2"
    # Look for markdown headings (##, ###) with the section name
    # More specific than substring matching to reduce false positives
    echo "$content" | grep -iE "^#{1,6}\s+.*${section}" > /dev/null 2>&1
    return $?
}

# Validate document function
validate_document() {
    local file="$1"
    local missing_required=()
    local missing_recommended=()
    local content

    if [[ ! -f "$file" ]]; then
        echo -e "${RED}Error: File not found: $file${NC}"
        exit 2
    fi

    # Read file once and cache content (single I/O operation)
    content=$(cat "$file")

    echo -e "${BLUE}Validating Master Concept Document: $file${NC}"
    echo ""

    # Check required sections
    echo -e "${BLUE}Required Sections:${NC}"
    for section in "${REQUIRED_SECTIONS[@]}"; do
        if section_exists "$section" "$content"; then
            echo -e "  ${GREEN}✓${NC} $section"
        else
            echo -e "  ${RED}✗${NC} $section - MISSING"
            missing_required+=("$section")
        fi
    done
    echo ""

    # Check recommended sections
    echo -e "${BLUE}Recommended Sections:${NC}"
    for section in "${RECOMMENDED_SECTIONS[@]}"; do
        if section_exists "$section" "$content"; then
            echo -e "  ${GREEN}✓${NC} $section"
        else
            echo -e "  ${YELLOW}!${NC} $section - Not found (recommended)"
            missing_recommended+=("$section")
        fi
    done
    echo ""
    
    # Summary
    echo -e "${BLUE}Summary:${NC}"
    local total_required=${#REQUIRED_SECTIONS[@]}
    local present_required=$((total_required - ${#missing_required[@]}))
    local total_recommended=${#RECOMMENDED_SECTIONS[@]}
    local present_recommended=$((total_recommended - ${#missing_recommended[@]}))
    
    echo "  Required:    $present_required/$total_required"
    echo "  Recommended: $present_recommended/$total_recommended"
    echo ""
    
    # Quality checks
    echo -e "${BLUE}Quality Checks:${NC}"

    # Check for unfilled template placeholders (be selective - don't flag legitimate text)
    # Only flag obvious unfilled placeholders like [Your text here] or *What this measures*
    local critical_placeholders
    critical_placeholders=$(echo "$content" | grep -cE '\[.*Your.*\]|\[.*TODO.*\]|_____+|FIXME|CHANGEME' || true)
    if [[ $critical_placeholders -gt 0 ]]; then
        echo -e "  ${YELLOW}!${NC} Document contains unfilled placeholders ($critical_placeholders found)"
    else
        echo -e "  ${GREEN}✓${NC} No obvious placeholders detected"
    fi

    # Check word count (lenient - MVP concepts can vary widely)
    local word_count
    word_count=$(echo "$content" | wc -w)
    if [[ $word_count -lt 500 ]]; then
        echo -e "  ${YELLOW}!${NC} Document is brief ($word_count words) - consider adding more depth"
    elif [[ $word_count -gt 5000 ]]; then
        echo -e "  ${YELLOW}!${NC} Document is quite long ($word_count words) - consider condensing"
    else
        echo -e "  ${GREEN}✓${NC} Document length looks reasonable ($word_count words)"
    fi
    
    echo ""
    
    # Final result
    if [[ ${#missing_required[@]} -gt 0 ]]; then
        echo -e "${RED}❌ INCOMPLETE: Missing ${#missing_required[@]} required section(s)${NC}"
        echo "   Missing: ${missing_required[*]}"
        exit 1
    else
        if [[ ${#missing_recommended[@]} -gt 0 ]]; then
            echo -e "${YELLOW}⚠ VALID with warnings: Missing ${#missing_recommended[@]} recommended section(s)${NC}"
        else
            echo -e "${GREEN}✅ COMPLETE: All sections present${NC}"
        fi
        exit 0
    fi
}

# Main
main() {
    if [[ $# -eq 0 ]]; then
        echo "Master Concept Document Validator"
        echo ""
        echo "Usage:"
        echo "  $0 path/to/master-concept.md     # Validate document"
        echo "  $0 --generate-template [path]    # Generate template"
        echo "  $0 --generate-template           # Output template to stdout"
        exit 0
    fi
    
    if [[ "$1" == "--generate-template" ]]; then
        if [[ $# -gt 1 ]]; then
            # Create directory if needed
            local dir
            dir=$(dirname "$2")
            mkdir -p "$dir"
            generate_template > "$2"
            echo -e "${GREEN}Template generated: $2${NC}"
        else
            generate_template
        fi
    else
        validate_document "$1"
    fi
}

main "$@"
