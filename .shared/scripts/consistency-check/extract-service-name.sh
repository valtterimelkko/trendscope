#!/bin/bash
#
# Extract Service Name
# Extracts the service/product name from different document types
#
# Usage:
#   ./extract-service-name.sh path/to/document.md
#
# Output:
#   The extracted service name, or empty if not found

set -euo pipefail

if [[ $# -eq 0 ]]; then
    echo "Usage: $0 path/to/document.md"
    exit 1
fi

FILE="$1"

if [[ ! -f "$FILE" ]]; then
    echo ""
    exit 0
fi

# Try to extract from H1 title
TITLE=$(grep -m1 "^# " "$FILE" 2>/dev/null | sed 's/^# //' || echo "")

if [[ -z "$TITLE" ]]; then
    echo ""
    exit 0
fi

# Remove common suffixes
TITLE=$(echo "$TITLE" | sed 's/ Master Concept.*//')
TITLE=$(echo "$TITLE" | sed 's/ Technical PRD.*//')
TITLE=$(echo "$TITLE" | sed 's/ Brand Kit.*//')
TITLE=$(echo "$TITLE" | sed 's/ Brand Guide.*//')
TITLE=$(echo "$TITLE" | sed 's/ MVP User Experience.*//')
TITLE=$(echo "$TITLE" | sed 's/ UX Design.*//')

# Handle [Product Name] placeholder
if [[ "$TITLE" == *"[Product Name]"* ]]; then
    TITLE=$(echo "$TITLE" | sed 's/\[Product Name\]//')
fi

# Handle brackets
if [[ "$TITLE" == "["*"]"* ]]; then
    TITLE=$(echo "$TITLE" | sed 's/\[//' | sed 's/\].*//')
fi

# Trim whitespace
TITLE=$(echo "$TITLE" | sed 's/^[[:space:]]*//' | sed 's/[[:space:]]*$//')

echo "$TITLE"
