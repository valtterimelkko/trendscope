#!/usr/bin/env python3
"""
Extract Frontend API Calls

Parses JavaScript/TypeScript files to extract API endpoint calls.
Supports common patterns: fetch, axios, ky, got, ofetch, useSWR, useQuery, and more.
Handles both literal strings and template literals with common base URL patterns.

Usage:
    python3 extract-frontend-calls.py src/
    python3 extract-frontend-calls.py path/to/file.js
    python3 extract-frontend-calls.py --base-url /api/v1 src/

Output:
    JSON array of API call objects
"""

import re
import sys
import json
import argparse
from pathlib import Path
from typing import List, Dict, Optional


# Common base URL variable names used in template literals
BASE_URL_PATTERNS = [
    r'\$\{API_BASE\}',
    r'\$\{API_URL\}',
    r'\$\{BASE_URL\}',
    r'\$\{baseUrl\}',
    r'\$\{apiUrl\}',
    r'\$\{apiBase\}',
    r'\$\{API_BASE_URL\}',
    r'\$\{process\.env\.[A-Z_]+\}',
    r'\$\{import\.meta\.env\.[A-Z_]+\}',
]


def normalize_template_literal(path: str, base_url: Optional[str] = None) -> str:
    """
    Normalize template literal paths by replacing base URL variables.
    
    Args:
        path: The extracted path (may contain template literal variables)
        base_url: Optional base URL to substitute for variables
    
    Returns:
        Normalized path string
    """
    if not base_url:
        base_url = '/api'  # Default substitution
    
    # Replace common base URL patterns
    for pattern in BASE_URL_PATTERNS:
        path = re.sub(pattern, base_url, path)
    
    # Handle remaining ${...} patterns - extract the path portion after the variable
    # e.g., `${baseUrl}/users` -> /users (if we can't resolve the variable)
    path = re.sub(r'\$\{[^}]+\}', '', path)
    
    # Clean up any double slashes from substitution
    path = re.sub(r'/+', '/', path)
    
    # Ensure path starts with /
    if path and not path.startswith('/') and not path.startswith('http'):
        path = '/' + path
    
    return path


def extract_api_calls_from_content(content: str, filename: str, base_url: Optional[str] = None) -> List[Dict]:
    """Extract API calls from JavaScript/TypeScript content."""
    calls = []
    
    def add_call(method: str, path: str, source: str, match_start: int):
        """Helper to add a call with consistent structure."""
        normalized_path = normalize_template_literal(path, base_url)
        if normalized_path and (normalized_path.startswith('/') or normalized_path.startswith('http')):
            calls.append({
                "method": method.upper(),
                "path": normalized_path,
                "source": source,
                "file": filename,
                "line": content[:match_start].count('\n') + 1,
                "original_path": path if path != normalized_path else None
            })
    
    # ============================================
    # FETCH PATTERNS
    # ============================================
    
    # Pattern 1a: fetch with literal string - standalone (no options object following)
    # Matches: fetch('/api/users') but not fetch('/api/users', { method: 'POST' })
    fetch_simple_pattern = r'fetch\s*\(\s*[\'"]([^\'"]+)[\'"]\s*\)'
    for match in re.finditer(fetch_simple_pattern, content):
        add_call("GET", match.group(1), "fetch", match.start())
    
    # Pattern 1b: fetch with template literal - standalone
    fetch_template_simple = r'fetch\s*\(\s*`([^`]+)`\s*\)'
    for match in re.finditer(fetch_template_simple, content):
        add_call("GET", match.group(1), "fetch", match.start())
    
    # Pattern 2a: fetch with options including method (literal string URL)
    # Use non-greedy match and limit scope to avoid spanning multiple statements
    fetch_method_pattern = r'fetch\s*\(\s*[\'"]([^\'"]+)[\'"][\s,]*\{[^}]{0,200}method:\s*[\'"](\w+)[\'"]'
    for match in re.finditer(fetch_method_pattern, content):
        add_call(match.group(2), match.group(1), "fetch", match.start())
    
    # Pattern 2b: fetch with template literal URL and method option
    fetch_template_method = r'fetch\s*\(\s*`([^`]+)`[\s,]*\{[^}]{0,200}method:\s*[\'"](\w+)[\'"]'
    for match in re.finditer(fetch_template_method, content):
        add_call(match.group(2), match.group(1), "fetch", match.start())
    
    # ============================================
    # AXIOS PATTERNS
    # ============================================
    
    # Pattern 3a: axios.get/post/put/patch/delete with literal string
    axios_pattern = r'axios\.(get|post|put|patch|delete)\s*\(\s*[\'"]([^\'"]+)[\'"]'
    for match in re.finditer(axios_pattern, content, re.IGNORECASE):
        add_call(match.group(1), match.group(2), "axios", match.start())
    
    # Pattern 3b: axios.get/post/put/patch/delete with template literal
    axios_template_pattern = r'axios\.(get|post|put|patch|delete)\s*\(\s*`([^`]+)`'
    for match in re.finditer(axios_template_pattern, content, re.IGNORECASE):
        add_call(match.group(1), match.group(2), "axios", match.start())
    
    # Pattern 4: axios({ method: 'POST', url: '/api/...' })
    axios_config_pattern = r'axios\s*\(\s*\{[^}]*method:\s*[\'"](\w+)[\'"][^}]*url:\s*[\'"`]([^\'"`,]+)[\'"`]'
    for match in re.finditer(axios_config_pattern, content, re.DOTALL | re.IGNORECASE):
        add_call(match.group(1), match.group(2), "axios", match.start())
    
    # ============================================
    # KY PATTERNS (modern fetch wrapper)
    # ============================================
    
    # Pattern 5a: ky.get/post/put/patch/delete with literal string
    ky_pattern = r'ky\.(get|post|put|patch|delete)\s*\(\s*[\'"]([^\'"]+)[\'"]'
    for match in re.finditer(ky_pattern, content, re.IGNORECASE):
        add_call(match.group(1), match.group(2), "ky", match.start())
    
    # Pattern 5b: ky.get/post/put/patch/delete with template literal
    ky_template_pattern = r'ky\.(get|post|put|patch|delete)\s*\(\s*`([^`]+)`'
    for match in re.finditer(ky_template_pattern, content, re.IGNORECASE):
        add_call(match.group(1), match.group(2), "ky", match.start())
    
    # ============================================
    # GOT PATTERNS (Node.js HTTP client)
    # ============================================
    
    # Pattern 6a: got.get/post/put/patch/delete with literal string
    got_pattern = r'got\.(get|post|put|patch|delete)\s*\(\s*[\'"]([^\'"]+)[\'"]'
    for match in re.finditer(got_pattern, content, re.IGNORECASE):
        add_call(match.group(1), match.group(2), "got", match.start())
    
    # Pattern 6b: got.get/post/put/patch/delete with template literal
    got_template_pattern = r'got\.(get|post|put|patch|delete)\s*\(\s*`([^`]+)`'
    for match in re.finditer(got_template_pattern, content, re.IGNORECASE):
        add_call(match.group(1), match.group(2), "got", match.start())
    
    # ============================================
    # OFETCH / $FETCH PATTERNS (Nuxt)
    # ============================================
    
    # Pattern 7a: $fetch or ofetch with literal string
    ofetch_pattern = r'(?:\$fetch|ofetch)\s*\(\s*[\'"]([^\'"]+)[\'"]'
    for match in re.finditer(ofetch_pattern, content):
        add_call("GET", match.group(1), "ofetch", match.start())
    
    # Pattern 7b: $fetch or ofetch with template literal
    ofetch_template_pattern = r'(?:\$fetch|ofetch)\s*\(\s*`([^`]+)`'
    for match in re.finditer(ofetch_template_pattern, content):
        add_call("GET", match.group(1), "ofetch", match.start())
    
    # Pattern 7c: $fetch with method option
    ofetch_method_pattern = r'(?:\$fetch|ofetch)\s*\(\s*[\'"`]([^\'"`,]+)[\'"`][\s,]*\{[^}]{0,200}method:\s*[\'"](\w+)[\'"]'
    for match in re.finditer(ofetch_method_pattern, content):
        add_call(match.group(2), match.group(1), "ofetch", match.start())
    
    # ============================================
    # ANGULAR $HTTP PATTERNS
    # ============================================
    
    # Pattern 8: $http.get/post/put/delete (Angular style)
    http_pattern = r'\$http\.(get|post|put|patch|delete)\s*\(\s*[\'"`]([^\'"`,]+)[\'"`]'
    for match in re.finditer(http_pattern, content, re.IGNORECASE):
        add_call(match.group(1), match.group(2), "$http", match.start())
    
    # ============================================
    # CUSTOM API CLIENT PATTERNS
    # ============================================
    
    # Pattern 9a: api.get/post/put/delete with literal string
    api_client_pattern = r'\bapi\.(get|post|put|patch|delete)\s*\(\s*[\'"]([^\'"]+)[\'"]'
    for match in re.finditer(api_client_pattern, content, re.IGNORECASE):
        add_call(match.group(1), match.group(2), "api_client", match.start())
    
    # Pattern 9b: api.get/post/put/delete with template literal
    api_client_template = r'\bapi\.(get|post|put|patch|delete)\s*\(\s*`([^`]+)`'
    for match in re.finditer(api_client_template, content, re.IGNORECASE):
        add_call(match.group(1), match.group(2), "api_client", match.start())
    
    # Pattern 9c: client.get/post/put/delete (another common pattern)
    client_pattern = r'\bclient\.(get|post|put|patch|delete)\s*\(\s*[\'"`]([^\'"`,]+)[\'"`]'
    for match in re.finditer(client_pattern, content, re.IGNORECASE):
        add_call(match.group(1), match.group(2), "client", match.start())
    
    # ============================================
    # REACT QUERY / SWR PATTERNS
    # ============================================
    
    # Pattern 10a: useSWR with literal string
    swr_pattern = r'useSWR\s*\(\s*[\'"]([^\'"]+)[\'"]'
    for match in re.finditer(swr_pattern, content):
        add_call("GET", match.group(1), "useSWR", match.start())
    
    # Pattern 10b: useSWR with template literal
    swr_template_pattern = r'useSWR\s*\(\s*`([^`]+)`'
    for match in re.finditer(swr_template_pattern, content):
        add_call("GET", match.group(1), "useSWR", match.start())
    
    # Pattern 11a: useQuery with queryKey containing URL (React Query v4+)
    # useQuery({ queryKey: ['users', '/api/users'], queryFn: ... })
    usequery_key_pattern = r'useQuery\s*\(\s*\{[^}]*queryKey:\s*\[[^\]]*[\'"](/[^\'"]+)[\'"]'
    for match in re.finditer(usequery_key_pattern, content):
        add_call("GET", match.group(1), "useQuery", match.start())
    
    # Pattern 11b: useQuery with URL as first arg (React Query v3)
    usequery_pattern = r'useQuery\s*\(\s*[\'"]([^\'"]+)[\'"]'
    for match in re.finditer(usequery_pattern, content):
        path = match.group(1)
        if path.startswith('/'):
            add_call("GET", path, "useQuery", match.start())
    
    # Pattern 11c: useQuery with template literal
    usequery_template = r'useQuery\s*\(\s*`([^`]+)`'
    for match in re.finditer(usequery_template, content):
        add_call("GET", match.group(1), "useQuery", match.start())
    
    # Pattern 12: useMutation (typically POST/PUT/DELETE)
    usemutation_pattern = r'useMutation\s*\([^)]*[\'"`]([^\'"`,]+)[\'"`]'
    for match in re.finditer(usemutation_pattern, content):
        path = match.group(1)
        if path.startswith('/'):
            add_call("POST", path, "useMutation", match.start())
    
    # Clean up calls - remove None original_path entries
    for call in calls:
        if call.get('original_path') is None:
            del call['original_path']
    
    return calls


def process_file(file_path: Path, base_url: Optional[str] = None) -> List[Dict]:
    """Process a single file and extract API calls."""
    try:
        content = file_path.read_text(encoding='utf-8')
        return extract_api_calls_from_content(content, str(file_path), base_url)
    except Exception as e:
        return [{
            "error": f"Failed to process {file_path}: {str(e)}",
            "file": str(file_path)
        }]


def process_directory(dir_path: Path, base_url: Optional[str] = None) -> List[Dict]:
    """Recursively process a directory for JS/TS files."""
    all_calls = []
    
    # File extensions to process
    extensions = {'.js', '.jsx', '.ts', '.tsx', '.vue', '.svelte'}
    
    # Directories to skip
    skip_dirs = {'node_modules', 'dist', 'build', '.next', 'coverage', '.git'}
    
    for file_path in dir_path.rglob('*'):
        if file_path.is_file() and file_path.suffix in extensions:
            # Skip if in excluded directory
            if any(skip_dir in file_path.parts for skip_dir in skip_dirs):
                continue
            calls = process_file(file_path, base_url)
            all_calls.extend(calls)
    
    return all_calls


def main():
    parser = argparse.ArgumentParser(
        description='Extract API calls from frontend JavaScript/TypeScript files'
    )
    parser.add_argument(
        'path',
        help='Path to file or directory to scan'
    )
    parser.add_argument(
        '--base-url',
        default=None,
        help='Base URL to substitute for template literal variables (e.g., /api/v1)'
    )
    parser.add_argument(
        '--format',
        choices=['json', 'simple'],
        default='json',
        help='Output format (default: json)'
    )
    
    args = parser.parse_args()
    target_path = Path(args.path)
    
    if not target_path.exists():
        print(json.dumps({"error": f"Path not found: {target_path}"}))
        sys.exit(1)
    
    if target_path.is_file():
        calls = process_file(target_path, args.base_url)
    else:
        calls = process_directory(target_path, args.base_url)
    
    # Deduplicate by method+path (keep first occurrence)
    seen = set()
    unique_calls = []
    for call in calls:
        if 'error' in call:
            unique_calls.append(call)
            continue
        key = f"{call['method']}:{call['path']}"
        if key not in seen:
            seen.add(key)
            unique_calls.append(call)
    
    if args.format == 'simple':
        # Simple format: one endpoint per line
        for call in unique_calls:
            if 'error' not in call:
                print(f"{call['method']} {call['path']}")
    else:
        result = {
            "path": str(target_path),
            "call_count": len([c for c in unique_calls if 'error' not in c]),
            "calls": unique_calls
        }
        print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
