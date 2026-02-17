#!/usr/bin/env python3
"""
Check template directory structure against requirements.
Usage: python3 check-structure.py <template-path>
"""

import os
import sys
import json

REQUIRED_FILES = [
    "manifest.json",
    "README.md",
    "frontend/package.json",
    "frontend/next.config.js",
    "frontend/tsconfig.json",
    "frontend/tailwind.config.js",
    "frontend/app/layout.tsx",
    "frontend/app/page.tsx",
    "frontend/styles/tokens.css",
    "supabase/config.toml",
    "stripe/products.json",
    "content/slots.json",
]

REQUIRED_DIRS = [
    "frontend/app/(auth)/login",
    "frontend/app/(auth)/signup", 
    "frontend/app/(auth)/callback",
    "frontend/app/(dashboard)",
    "frontend/app/(dashboard)/settings",
    "frontend/app/api/stripe",
    "frontend/components",
    "frontend/components/ui",
    "frontend/components/layout",
    "frontend/components/auth",
    "frontend/components/dashboard",
    "frontend/components/billing",
    "frontend/lib/supabase",
    "frontend/lib/stripe",
    "supabase/migrations",
    "stripe",
    "content",
]

def check_structure(template_path: str) -> tuple[list, list]:
    """Check template structure and return missing files and dirs."""
    missing_files = []
    missing_dirs = []
    
    for file in REQUIRED_FILES:
        full_path = os.path.join(template_path, file)
        if not os.path.isfile(full_path):
            missing_files.append(file)
    
    for dir in REQUIRED_DIRS:
        full_path = os.path.join(template_path, dir)
        if not os.path.isdir(full_path):
            missing_dirs.append(dir)
    
    return missing_files, missing_dirs

def main():
    if len(sys.argv) < 2:
        print("Usage: python3 check-structure.py <template-path>")
        sys.exit(1)
    
    template_path = sys.argv[1]
    
    if not os.path.isdir(template_path):
        print(f"Error: Directory not found: {template_path}")
        sys.exit(1)
    
    missing_files, missing_dirs = check_structure(template_path)
    
    # Output as JSON for programmatic use
    if "--json" in sys.argv:
        result = {
            "status": "pass" if not (missing_files or missing_dirs) else "fail",
            "missing_files": missing_files,
            "missing_dirs": missing_dirs,
        }
        print(json.dumps(result, indent=2))
    else:
        # Human-readable output
        if missing_files:
            print("Missing files:")
            for f in missing_files:
                print(f"  ❌ {f}")
        
        if missing_dirs:
            print("Missing directories:")
            for d in missing_dirs:
                print(f"  ❌ {d}")
        
        if not missing_files and not missing_dirs:
            print("✅ All required files and directories present")
            sys.exit(0)
        else:
            sys.exit(1)

if __name__ == "__main__":
    main()
