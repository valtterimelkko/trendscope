#!/usr/bin/env python3
"""
Run Supabase Migrations from Template

Executes database migrations from template's supabase/migrations/ directory.
Verifies RLS policies are enabled after deployment.

Usage:
    python3 run-migrations.py --migrations templates/analytics-dashboard/supabase/migrations/ --dry-run
    python3 run-migrations.py --migrations templates/analytics-dashboard/supabase/migrations/ --execute
    python3 run-migrations.py --verify
"""

import argparse
import os
import subprocess
import sys
from pathlib import Path


def get_migration_files(migrations_path: str) -> list:
    """Get all migration files sorted by number."""
    path = Path(migrations_path)
    if not path.exists():
        print(f"ERROR: Migrations path not found: {migrations_path}")
        return []
    
    files = sorted(path.glob("*.sql"))
    return files


def validate_migration(file_path: Path) -> dict:
    """Validate a migration file structure."""
    result = {
        "file": file_path.name,
        "valid": True,
        "issues": [],
        "tables": [],
        "policies": []
    }
    
    with open(file_path, 'r') as f:
        content = f.read().upper()
    
    # Check for CREATE TABLE
    import re
    tables = re.findall(r'CREATE TABLE.*?(\w+\.?\w+)', content)
    result["tables"] = [t.lower() for t in tables]
    
    # Check for RLS policies
    policies = re.findall(r'CREATE POLICY.*?"([^"]+)"', content, re.IGNORECASE)
    result["policies"] = policies
    
    # Check for ENABLE ROW LEVEL SECURITY
    if 'CREATE TABLE' in content and 'ENABLE ROW LEVEL SECURITY' not in content:
        result["issues"].append("Creates tables but may not enable RLS")
    
    return result


def run_migration_dry_run(file_path: Path) -> bool:
    """Simulate running a migration (dry run)."""
    validation = validate_migration(file_path)
    
    print(f"\n  File: {file_path.name}")
    print(f"  Tables: {', '.join(validation['tables']) or 'None'}")
    print(f"  Policies: {len(validation['policies'])}")
    
    if validation['issues']:
        print(f"  ⚠ Issues: {', '.join(validation['issues'])}")
    else:
        print("  ✓ Validation passed")
    
    return validation['valid']


def run_migration(file_path: Path) -> bool:
    """Execute a migration file via Supabase CLI."""
    print(f"\n  Running: {file_path.name}")
    
    try:
        # Use Supabase CLI to run migration
        result = subprocess.run(
            ["npx", "supabase", "db", "push"],
            capture_output=True,
            text=True,
            cwd=file_path.parent.parent.parent  # Go to template root
        )
        
        if result.returncode == 0:
            print(f"  ✓ Applied: {file_path.name}")
            return True
        else:
            print(f"  ✗ Failed: {file_path.name}")
            print(f"    Error: {result.stderr}")
            return False
            
    except FileNotFoundError:
        # Supabase CLI not installed, try direct SQL
        print("  Supabase CLI not found, attempting direct SQL...")
        return run_migration_direct_sql(file_path)


def run_migration_direct_sql(file_path: Path) -> bool:
    """Run migration via direct psql command."""
    database_url = os.environ.get('DATABASE_URL')
    
    if not database_url:
        print("  ERROR: DATABASE_URL not set")
        return False
    
    try:
        result = subprocess.run(
            ["psql", database_url, "-f", str(file_path)],
            capture_output=True,
            text=True
        )
        
        if result.returncode == 0:
            print(f"  ✓ Applied via psql: {file_path.name}")
            return True
        else:
            print(f"  ✗ Failed: {result.stderr}")
            return False
            
    except FileNotFoundError:
        print("  ERROR: psql not found. Install PostgreSQL client.")
        return False


def verify_rls_status() -> dict:
    """Verify RLS is enabled on all public tables."""
    print("\nVerifying RLS status...")
    
    query = """
    SELECT 
        tablename,
        CASE WHEN rowsecurity THEN 'enabled' ELSE 'DISABLED' END as rls_status
    FROM pg_tables 
    WHERE schemaname = 'public'
    ORDER BY tablename;
    """
    
    try:
        result = subprocess.run(
            ["npx", "supabase", "db", "remote", "query", query],
            capture_output=True,
            text=True
        )
        
        if result.returncode == 0:
            print(result.stdout)
            return {"success": True, "output": result.stdout}
        else:
            print(f"ERROR: {result.stderr}")
            return {"success": False, "error": result.stderr}
            
    except FileNotFoundError:
        print("ERROR: Supabase CLI not found")
        return {"success": False, "error": "Supabase CLI not found"}


def verify_policies() -> dict:
    """List all RLS policies in public schema."""
    print("\nListing RLS policies...")
    
    query = """
    SELECT 
        tablename,
        policyname,
        cmd as operation
    FROM pg_policies 
    WHERE schemaname = 'public'
    ORDER BY tablename, policyname;
    """
    
    try:
        result = subprocess.run(
            ["npx", "supabase", "db", "remote", "query", query],
            capture_output=True,
            text=True
        )
        
        if result.returncode == 0:
            print(result.stdout)
            return {"success": True, "output": result.stdout}
        else:
            print(f"ERROR: {result.stderr}")
            return {"success": False, "error": result.stderr}
            
    except FileNotFoundError:
        print("ERROR: Supabase CLI not found")
        return {"success": False, "error": "Supabase CLI not found"}


def main():
    parser = argparse.ArgumentParser(
        description='Run Supabase migrations from template'
    )
    parser.add_argument(
        '--migrations',
        help='Path to migrations directory'
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Validate migrations without executing'
    )
    parser.add_argument(
        '--execute',
        action='store_true',
        help='Execute migrations'
    )
    parser.add_argument(
        '--verify',
        action='store_true',
        help='Verify RLS status on remote database'
    )
    
    args = parser.parse_args()
    
    if args.verify:
        verify_rls_status()
        verify_policies()
        return
    
    if not args.migrations:
        print("ERROR: --migrations path required")
        sys.exit(1)
    
    if not args.dry_run and not args.execute:
        print("ERROR: Specify --dry-run or --execute")
        sys.exit(1)
    
    # Get migration files
    files = get_migration_files(args.migrations)
    
    if not files:
        print("No migration files found")
        sys.exit(1)
    
    print(f"Found {len(files)} migration file(s)")
    print("=" * 50)
    
    success_count = 0
    failure_count = 0
    
    for file_path in files:
        if args.dry_run:
            if run_migration_dry_run(file_path):
                success_count += 1
            else:
                failure_count += 1
        else:
            if run_migration(file_path):
                success_count += 1
            else:
                failure_count += 1
    
    print("\n" + "=" * 50)
    print("MIGRATION SUMMARY")
    print("=" * 50)
    print(f"Total: {len(files)}")
    print(f"Success: {success_count}")
    print(f"Failed: {failure_count}")
    
    if args.dry_run:
        print("\n[DRY RUN - No changes made]")
    else:
        print("\nVerifying deployment...")
        verify_rls_status()
    
    if failure_count > 0:
        sys.exit(1)


if __name__ == '__main__':
    main()
