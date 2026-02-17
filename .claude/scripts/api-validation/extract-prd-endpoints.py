#!/usr/bin/env python3
"""
Extract API Endpoints from PRD/Technical Architecture Markdown

Parses Technical PRD or Architecture files to extract API endpoint definitions.

Usage:
    python3 extract-prd-endpoints.py path/to/prd.md

Output:
    JSON array of endpoint objects
"""

import re
import sys
import json
from pathlib import Path


def extract_endpoints(content: str) -> list:
    """Extract API endpoints from markdown content."""
    endpoints = []
    
    # Pattern 1: ### [METHOD] /path or #### [METHOD] /path
    # Matches: ### POST /api/v1/users, #### GET /api/v1/users/{id}
    heading_pattern = r'^#{2,4}\s+(GET|POST|PUT|PATCH|DELETE)\s+(/[^\s]+)'
    
    for match in re.finditer(heading_pattern, content, re.MULTILINE):
        method = match.group(1).upper()
        path = match.group(2)
        endpoints.append({
            "method": method,
            "path": path,
            "source": "heading",
            "line": content[:match.start()].count('\n') + 1
        })
    
    # Pattern 2: | METHOD | /path | or METHOD /path in tables
    # Matches table rows with endpoints
    table_pattern = r'\|\s*(GET|POST|PUT|PATCH|DELETE)\s*\|\s*(/[^\s|]+)'
    
    for match in re.finditer(table_pattern, content, re.IGNORECASE):
        method = match.group(1).upper()
        path = match.group(2).strip()
        endpoints.append({
            "method": method,
            "path": path,
            "source": "table",
            "line": content[:match.start()].count('\n') + 1
        })
    
    # Pattern 3: Inline `METHOD /path` in backticks
    # Matches: `POST /api/v1/auth/login`
    inline_pattern = r'`(GET|POST|PUT|PATCH|DELETE)\s+(/[^`]+)`'
    
    for match in re.finditer(inline_pattern, content, re.IGNORECASE):
        method = match.group(1).upper()
        path = match.group(2).strip()
        endpoints.append({
            "method": method,
            "path": path,
            "source": "inline",
            "line": content[:match.start()].count('\n') + 1
        })
    
    # Pattern 4: "Endpoint:" or "URL:" followed by method and path
    # Matches: Endpoint: POST /api/users
    endpoint_label_pattern = r'(?:Endpoint|URL|Route):\s*(GET|POST|PUT|PATCH|DELETE)?\s*(/[^\s\n]+)'
    
    for match in re.finditer(endpoint_label_pattern, content, re.IGNORECASE):
        method = (match.group(1) or "GET").upper()
        path = match.group(2).strip()
        endpoints.append({
            "method": method,
            "path": path,
            "source": "label",
            "line": content[:match.start()].count('\n') + 1
        })
    
    # Deduplicate by method+path
    seen = set()
    unique_endpoints = []
    for ep in endpoints:
        key = f"{ep['method']}:{ep['path']}"
        if key not in seen:
            seen.add(key)
            unique_endpoints.append(ep)
    
    return unique_endpoints


def main():
    if len(sys.argv) < 2:
        print("Usage: python3 extract-prd-endpoints.py path/to/prd.md", file=sys.stderr)
        sys.exit(1)
    
    prd_path = Path(sys.argv[1])
    
    if not prd_path.exists():
        print(json.dumps({"error": f"File not found: {prd_path}"}))
        sys.exit(1)
    
    content = prd_path.read_text(encoding='utf-8')
    endpoints = extract_endpoints(content)
    
    result = {
        "file": str(prd_path),
        "endpoint_count": len(endpoints),
        "endpoints": endpoints
    }
    
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
