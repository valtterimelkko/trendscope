#!/usr/bin/env python3
"""
Validate API Contracts

Compares API endpoints defined in PRD/architecture documents against
actual frontend API calls to identify discrepancies.

Usage:
    python3 validate-api-contracts.py --prd path/to/prd.md --frontend src/
    python3 validate-api-contracts.py --prd docs/Project-Technical-Architecture.md --frontend src/
    python3 validate-api-contracts.py --prd docs/PRD.md --frontend src/ --fuzzy

Options:
    --fuzzy     Enable fuzzy matching (e.g., /tasks/123 matches /tasks/{id})
    --strict    Strict matching - paths must match exactly (default)
    --format    Output format: json (default) or markdown

Output:
    JSON report with discrepancies categorized by severity
"""

import argparse
import json
import re
import sys
import subprocess
from pathlib import Path
from typing import Dict, List
from urllib.parse import urlparse


def run_extractor(script: str, target: str) -> Dict:
    """Run an extraction script and return parsed JSON output."""
    script_dir = Path(__file__).parent
    script_path = script_dir / script
    
    try:
        result = subprocess.run(
            ['python3', str(script_path), target],
            capture_output=True,
            text=True,
            check=True
        )
        return json.loads(result.stdout)
    except subprocess.CalledProcessError as e:
        return {"error": f"Script failed: {e.stderr}"}
    except json.JSONDecodeError as e:
        return {"error": f"Invalid JSON output: {e}"}


def normalize_path(path: str, fuzzy: bool = False) -> str:
    """
    Normalize API path for comparison.
    
    Args:
        path: The API path to normalize
        fuzzy: If True, convert concrete IDs to parameter placeholders
    
    Returns:
        Normalized path string
    """
    # Remove trailing slashes
    path = path.rstrip('/')
    
    # Remove query strings
    if '?' in path:
        path = path.split('?')[0]
    
    # Normalize :param style to {param} style
    path = re.sub(r':(\w+)', r'{\1}', path)
    
    if fuzzy:
        # Convert concrete IDs to parameter placeholders
        # UUID pattern: 8-4-4-4-12 hex chars
        uuid_pattern = (
            r'/[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-'
            r'[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}'
        )
        path = re.sub(uuid_pattern, '/{id}', path)
        # Numeric IDs: one or more digits as a path segment
        path = re.sub(r'/\d+(?=/|$)', '/{id}', path)
        # Short alphanumeric IDs (common in many systems): 6-24 chars
        path = re.sub(r'/[a-zA-Z0-9]{6,24}(?=/|$)', '/{id}', path)
    
    return path


def path_matches(prd_path: str, frontend_path: str, fuzzy: bool = False) -> bool:
    """
    Check if a frontend path matches a PRD path.
    
    Args:
        prd_path: The path from PRD (may contain {param} placeholders)
        frontend_path: The path from frontend code (may have concrete values)
        fuzzy: If True, use fuzzy matching for parameters
    
    Returns:
        True if paths match
    """
    # Normalize both paths
    prd_normalized = normalize_path(prd_path)
    frontend_normalized = normalize_path(frontend_path, fuzzy=fuzzy)
    
    # Direct match after normalization
    if prd_normalized == frontend_normalized:
        return True
    
    if fuzzy:
        # Convert PRD path with {param} to regex pattern
        # {id}, {userId}, etc. should match any path segment
        pattern = prd_normalized
        pattern = re.sub(r'\{[^}]+\}', r'[^/]+', pattern)
        pattern = f'^{pattern}$'
        
        if re.match(pattern, frontend_path.rstrip('/')):
            return True
    
    return False


def compare_endpoints(
    prd_endpoints: List[Dict], 
    frontend_calls: List[Dict],
    fuzzy: bool = False
) -> Dict:
    """Compare PRD endpoints with frontend calls."""
    
    # Build list of PRD endpoints with normalized paths
    prd_list = []
    for ep in prd_endpoints:
        if 'method' in ep and 'path' in ep:
            prd_list.append({
                'method': ep['method'].upper(),
                'path': ep['path'],
                'normalized': normalize_path(ep['path'])
            })
    
    # Build list of frontend calls
    frontend_list = []
    for call in frontend_calls:
        if 'error' in call:
            continue
        if 'method' in call and 'path' in call:
            # Only consider API paths (skip external URLs)
            path = call['path']
            if path.startswith('http') and 'api' not in path.lower():
                continue
            if path.startswith('http'):
                # Extract path from full URL
                parsed = urlparse(path)
                path = parsed.path
            
            frontend_list.append({
                'method': call['method'].upper(),
                'path': path,
                'normalized': normalize_path(path, fuzzy=fuzzy),
                'file': call.get('file', 'unknown')
            })
    
    # Match endpoints
    matched = []
    prd_matched_indices = set()
    frontend_matched_indices = set()
    
    for fi, frontend in enumerate(frontend_list):
        for pi, prd in enumerate(prd_list):
            if frontend['method'] == prd['method']:
                if path_matches(prd['path'], frontend['path'], fuzzy=fuzzy):
                    if pi not in prd_matched_indices:
                        matched.append({
                            "method": prd['method'],
                            "path": prd['normalized']
                        })
                        prd_matched_indices.add(pi)
                    frontend_matched_indices.add(fi)
    
    # Find unmatched
    missing_in_frontend = []
    for pi, prd in enumerate(prd_list):
        if pi not in prd_matched_indices:
            missing_in_frontend.append({
                "method": prd['method'],
                "path": prd['normalized'],
                "severity": "warning"
            })
    
    missing_in_prd = []
    for fi, frontend in enumerate(frontend_list):
        if fi not in frontend_matched_indices:
            missing_in_prd.append({
                "method": frontend['method'],
                "path": frontend['path'],
                "severity": "blocker",
                "found_in": frontend['file']
            })
    
    return {
        "matched": sorted(matched, key=lambda x: (x['method'], x['path'])),
        "missing_in_frontend": sorted(
            missing_in_frontend, key=lambda x: (x['method'], x['path'])
        ),
        "missing_in_prd": sorted(
            missing_in_prd, key=lambda x: (x['method'], x['path'])
        )
    }


def generate_report(
    prd_result: Dict, 
    frontend_result: Dict, 
    comparison: Dict
) -> Dict:
    """Generate a comprehensive validation report."""
    
    blockers = comparison['missing_in_prd']
    warnings = comparison['missing_in_frontend']
    
    # Determine overall status
    if blockers:
        status = "BLOCKERS"
    elif warnings:
        status = "WARNINGS"
    else:
        status = "PASS"
    
    report = {
        "status": status,
        "summary": {
            "prd_endpoints": prd_result.get('endpoint_count', 0),
            "frontend_calls": frontend_result.get('call_count', 0),
            "matched": len(comparison['matched']),
            "blockers": len(blockers),
            "warnings": len(warnings)
        },
        "blockers": blockers,
        "warnings": warnings,
        "matched": comparison['matched'],
        "details": {
            "prd_file": prd_result.get('file', 'unknown'),
            "frontend_path": frontend_result.get('path', 'unknown')
        }
    }
    
    return report


def format_markdown_report(report: Dict) -> str:
    """Format report as markdown for human reading."""
    lines = []
    lines.append("# API Contract Validation Report")
    lines.append("")
    lines.append(f"**Status:** {'✅ ' if report['status'] == 'PASS' else '⚠️ ' if report['status'] == 'WARNINGS' else '❌ '}{report['status']}")
    lines.append("")
    lines.append("## Summary")
    lines.append("")
    lines.append(f"- PRD Endpoints: {report['summary']['prd_endpoints']}")
    lines.append(f"- Frontend Calls: {report['summary']['frontend_calls']}")
    lines.append(f"- Matched: {report['summary']['matched']}")
    lines.append(f"- Blockers: {report['summary']['blockers']}")
    lines.append(f"- Warnings: {report['summary']['warnings']}")
    lines.append("")
    
    if report['blockers']:
        lines.append("## ❌ Blockers (Frontend calls not in PRD)")
        lines.append("")
        lines.append("These endpoints are called by frontend but not documented in PRD:")
        lines.append("")
        for item in report['blockers']:
            lines.append(f"- `{item['method']} {item['path']}` (found in: {item.get('found_in', 'unknown')})")
        lines.append("")
    
    if report['warnings']:
        lines.append("## ⚠️ Warnings (PRD endpoints not used)")
        lines.append("")
        lines.append("These endpoints are documented in PRD but not used by frontend:")
        lines.append("")
        for item in report['warnings']:
            lines.append(f"- `{item['method']} {item['path']}`")
        lines.append("")
    
    if report['matched']:
        lines.append("## ✅ Matched Endpoints")
        lines.append("")
        for item in report['matched']:
            lines.append(f"- `{item['method']} {item['path']}`")
        lines.append("")
    
    return '\n'.join(lines)


def main():
    parser = argparse.ArgumentParser(
        description='Validate API contracts between PRD and frontend code'
    )
    parser.add_argument(
        '--prd',
        required=True,
        help='Path to PRD or Technical Architecture markdown file'
    )
    parser.add_argument(
        '--frontend',
        required=True,
        help='Path to frontend source directory or file'
    )
    parser.add_argument(
        '--format',
        choices=['json', 'markdown'],
        default='json',
        help='Output format (default: json)'
    )
    parser.add_argument(
        '--fuzzy',
        action='store_true',
        help='Enable fuzzy matching for path parameters (e.g., /tasks/123 matches /tasks/{id})'
    )
    parser.add_argument(
        '--strict',
        action='store_true',
        help='Strict matching - paths must match exactly (default behavior)'
    )
    
    args = parser.parse_args()
    
    # Determine matching mode
    fuzzy_mode = args.fuzzy and not args.strict
    
    # Validate inputs
    prd_path = Path(args.prd)
    frontend_path = Path(args.frontend)
    
    if not prd_path.exists():
        print(json.dumps({"error": f"PRD file not found: {prd_path}"}))
        sys.exit(1)
    
    if not frontend_path.exists():
        print(json.dumps({"error": f"Frontend path not found: {frontend_path}"}))
        sys.exit(1)
    
    # Extract endpoints from PRD
    prd_result = run_extractor('extract-prd-endpoints.py', str(prd_path))
    if 'error' in prd_result:
        print(json.dumps({"error": f"PRD extraction failed: {prd_result['error']}"}))
        sys.exit(1)
    
    # Extract calls from frontend
    frontend_result = run_extractor('extract-frontend-calls.py', str(frontend_path))
    if 'error' in frontend_result:
        err = frontend_result['error']
        print(json.dumps({"error": f"Frontend extraction failed: {err}"}))
        sys.exit(1)
    
    # Compare and generate report
    comparison = compare_endpoints(
        prd_result.get('endpoints', []),
        frontend_result.get('calls', []),
        fuzzy=fuzzy_mode
    )
    
    report = generate_report(prd_result, frontend_result, comparison)
    
    # Add matching mode to report
    report['matching_mode'] = 'fuzzy' if fuzzy_mode else 'strict'
    
    # Output
    if args.format == 'markdown':
        print(format_markdown_report(report))
    else:
        print(json.dumps(report, indent=2))
    
    # Exit code based on status
    if report['status'] == 'BLOCKERS':
        sys.exit(1)
    elif report['status'] == 'WARNINGS':
        sys.exit(0)  # Warnings don't fail
    else:
        sys.exit(0)


if __name__ == "__main__":
    main()
