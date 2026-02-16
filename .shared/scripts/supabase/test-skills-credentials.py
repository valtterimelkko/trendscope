#!/usr/bin/env python3
"""
Comprehensive test suite for Supabase skills credential loading.

Tests that all skills reference local scripts and those scripts properly
load global Supabase credentials from /etc/supabase/.

Test Categories:
1. Configuration File Paths
2. Credential Loading Mechanism
3. Script Reference Paths
4. Skill Documentation Consistency
"""

import json
import os
import sys
import subprocess
from pathlib import Path

# ============================================================================
# TEST CONFIGURATION
# ============================================================================

PROJECT_ROOT = Path(__file__).parent.parent.parent.parent
LOCAL_SCRIPTS = PROJECT_ROOT / ".shared" / "scripts" / "supabase"
SKILLS_DIR = PROJECT_ROOT / ".shared" / "skills"
GLOBAL_CONFIG_FILE = Path("/etc/supabase/config.conf")
GLOBAL_PROJECTS_FILE = Path("/etc/supabase/projects.json")

SUPABASE_SKILLS = [
    "supabase-project-manage",
    "supabase-database",
    "supabase-auth-setup",
    "supabase-deployer"
]

# ============================================================================
# TEST RESULTS TRACKING
# ============================================================================

class TestResult:
    def __init__(self):
        self.passed = []
        self.failed = []
        self.warnings = []

    def add_pass(self, test_name, details=""):
        self.passed.append({"name": test_name, "details": details})
        print(f"✓ PASS: {test_name}")
        if details:
            print(f"  → {details}")

    def add_fail(self, test_name, reason):
        self.failed.append({"name": test_name, "reason": reason})
        print(f"✗ FAIL: {test_name}")
        print(f"  → {reason}")

    def add_warning(self, test_name, message):
        self.warnings.append({"name": test_name, "message": message})
        print(f"⚠ WARN: {test_name}")
        print(f"  → {message}")

    def summary(self):
        total = len(self.passed) + len(self.failed)
        return {
            "total_tests": total,
            "passed": len(self.passed),
            "failed": len(self.failed),
            "warnings": len(self.warnings),
            "success_rate": f"{(len(self.passed) / total * 100):.1f}%" if total > 0 else "N/A"
        }

# ============================================================================
# TEST 1: CREDENTIAL FILE PATHS
# ============================================================================

def test_credential_file_paths(results):
    """Verify global credential files are accessible."""
    print("\n" + "="*70)
    print("TEST 1: GLOBAL CREDENTIAL FILE PATHS")
    print("="*70)

    # Check if files exist
    if GLOBAL_CONFIG_FILE.exists():
        results.add_pass("Global config file exists", f"Found at {GLOBAL_CONFIG_FILE}")
    else:
        results.add_warning("Global config file missing",
                           f"Not found at {GLOBAL_CONFIG_FILE} - create with: mkdir -p /etc/supabase && echo 'SUPABASE_ACCESS_TOKEN=xxx' | sudo tee /etc/supabase/config.conf")

    if GLOBAL_PROJECTS_FILE.exists():
        results.add_pass("Global projects file exists", f"Found at {GLOBAL_PROJECTS_FILE}")
    else:
        results.add_warning("Global projects file missing",
                           f"Not found at {GLOBAL_PROJECTS_FILE} - will be created on first credential save")

    # Check file permissions
    if GLOBAL_CONFIG_FILE.exists():
        stat_info = GLOBAL_CONFIG_FILE.stat()
        mode = oct(stat_info.st_mode)[-3:]
        if mode == "600" or mode == "644":
            results.add_pass("Global config file permissions", f"Mode {mode} is acceptable")
        else:
            results.add_warning("Global config file permissions",
                               f"Mode {mode} - recommend 600 for security")

# ============================================================================
# TEST 2: LOCAL SCRIPTS EXIST
# ============================================================================

def test_local_scripts_exist(results):
    """Verify all required local scripts are present."""
    print("\n" + "="*70)
    print("TEST 2: LOCAL SUPABASE SCRIPTS")
    print("="*70)

    required_scripts = [
        "supabase_api.py",
        "save_project_credentials.py",
        "create_project.py",
        "list_projects.py",
        "get_api_keys.py",
        "execute_sql.py",
        "list_tables.py",
        "query_table.py",
        "mutate_table.py",
        "manage_rls.py",
        "setup_auth.py",
    ]

    if not LOCAL_SCRIPTS.exists():
        results.add_fail("Local scripts directory", f"Directory not found: {LOCAL_SCRIPTS}")
        return

    results.add_pass("Local scripts directory exists", f"Found at {LOCAL_SCRIPTS}")

    # Check each script
    missing = []
    for script in required_scripts:
        script_path = LOCAL_SCRIPTS / script
        if script_path.exists():
            results.add_pass(f"Script found: {script}", str(script_path))
        else:
            missing.append(script)

    if missing:
        results.add_fail("Missing scripts", f"Not found: {', '.join(missing)}")

# ============================================================================
# TEST 3: SCRIPT CREDENTIAL LOADING
# ============================================================================

def test_script_credential_loading(results):
    """Test that local scripts properly reference global credentials."""
    print("\n" + "="*70)
    print("TEST 3: SCRIPT CREDENTIAL LOADING MECHANISM")
    print("="*70)

    # Check supabase_api.py for correct paths
    api_file = LOCAL_SCRIPTS / "supabase_api.py"
    if not api_file.exists():
        results.add_fail("supabase_api.py", "File not found")
        return

    with open(api_file, 'r') as f:
        content = f.read()

    # Check for correct config paths
    if 'CONFIG_FILE = "/etc/supabase/config.conf"' in content:
        results.add_pass("Global config path in supabase_api.py", "/etc/supabase/config.conf")
    else:
        results.add_fail("Global config path", "supabase_api.py does not reference /etc/supabase/config.conf")

    if 'PROJECTS_FILE = "/etc/supabase/projects.json"' in content:
        results.add_pass("Global projects path in supabase_api.py", "/etc/supabase/projects.json")
    else:
        results.add_fail("Global projects path", "supabase_api.py does not reference /etc/supabase/projects.json")

    # Check for load_config function
    if 'def load_config()' in content:
        results.add_pass("load_config() function exists", "Found in supabase_api.py")
    else:
        results.add_fail("load_config() function", "Not found in supabase_api.py")

    # Check for load_projects function
    if 'def load_projects()' in content:
        results.add_pass("load_projects() function exists", "Found in supabase_api.py")
    else:
        results.add_fail("load_projects() function", "Not found in supabase_api.py")

# ============================================================================
# TEST 4: SKILL DOCUMENTATION PATHS
# ============================================================================

def test_skill_documentation_paths(results):
    """Verify skills reference local scripts, not global ones."""
    print("\n" + "="*70)
    print("TEST 4: SKILL DOCUMENTATION SCRIPT REFERENCES")
    print("="*70)

    bad_refs = []
    good_refs = []

    for skill_name in SUPABASE_SKILLS:
        skill_dir = SKILLS_DIR / skill_name
        skill_md = skill_dir / "SKILL.md"

        if not skill_md.exists():
            results.add_fail(f"{skill_name}/SKILL.md", "File not found")
            continue

        with open(skill_md, 'r') as f:
            content = f.read()

        # Check for references to global scripts (bad)
        if "~/.shared/scripts/supabase/" in content:
            count = content.count("~/.shared/scripts/supabase/")
            good_refs.append((skill_name, count))
            results.add_pass(f"{skill_name} references", f"Correctly uses ~/.shared/scripts/supabase/ ({count} times)")

        # Check for absolute /root references (potential bad)
        if "/root/.shared/scripts/supabase/" in content:
            bad_refs.append(skill_name)
            results.add_warning(f"{skill_name} paths", "Contains /root/.shared/scripts - should use ~/.shared/scripts/")

    if not bad_refs:
        results.add_pass("No absolute /root paths", "All skills use relative ~/.shared/scripts/ paths")

# ============================================================================
# TEST 5: CREDENTIAL LOADING TEST
# ============================================================================

def test_credential_loading_execution(results):
    """Test that scripts can actually load credentials."""
    print("\n" + "="*70)
    print("TEST 5: CREDENTIAL LOADING EXECUTION")
    print("="*70)

    test_script = LOCAL_SCRIPTS / "save_project_credentials.py"
    if not test_script.exists():
        results.add_fail("Test script path", f"Not found: {test_script}")
        return

    # Test --list flag (should work even without credentials)
    try:
        result = subprocess.run(
            ["python3", str(test_script), "--list"],
            capture_output=True,
            text=True,
            timeout=10,
            cwd=str(PROJECT_ROOT)
        )

        if result.returncode == 0:
            try:
                output = json.loads(result.stdout)
                if output.get("success"):
                    results.add_pass("Credential list command", "Successfully executed --list")
                else:
                    results.add_fail("Credential list command", f"Got error: {output.get('error', {}).get('message')}")
            except json.JSONDecodeError:
                results.add_fail("Credential list output", "Output is not valid JSON")
        else:
            results.add_fail("Credential list execution", result.stderr[:200])

    except subprocess.TimeoutExpired:
        results.add_fail("Credential list timeout", "Script took too long to execute")
    except Exception as e:
        results.add_fail("Credential list exception", str(e))

# ============================================================================
# TEST 6: CONFIG FILE READING
# ============================================================================

def test_config_file_reading(results):
    """Test that we can read the global config file."""
    print("\n" + "="*70)
    print("TEST 6: CONFIG FILE READING")
    print("="*70)

    if not GLOBAL_CONFIG_FILE.exists():
        results.add_warning("Config file reading", f"Skipped - file doesn't exist at {GLOBAL_CONFIG_FILE}")
        return

    try:
        with open(GLOBAL_CONFIG_FILE, 'r') as f:
            content = f.read()

        lines = [l.strip() for l in content.split('\n') if l.strip() and not l.startswith('#')]

        if lines:
            results.add_pass("Config file readable", f"Found {len(lines)} configuration entries")

            # Check for required keys
            has_pat = any('SUPABASE_ACCESS_TOKEN' in l for l in lines)
            has_org = any('SUPABASE_ORG_ID' in l for l in lines)

            if has_pat:
                results.add_pass("SUPABASE_ACCESS_TOKEN present", "Found in config")
            else:
                results.add_warning("SUPABASE_ACCESS_TOKEN", "Not found in config - needed for Management API")

            if has_org:
                results.add_pass("SUPABASE_ORG_ID present", "Found in config")
            else:
                results.add_warning("SUPABASE_ORG_ID", "Not found in config - optional for some operations")
        else:
            results.add_warning("Config file content", "File is empty or only contains comments")

    except PermissionError:
        results.add_fail("Config file permissions", f"Cannot read {GLOBAL_CONFIG_FILE} - check permissions")
    except Exception as e:
        results.add_fail("Config file reading", str(e))

# ============================================================================
# TEST 7: PROJECTS FILE STRUCTURE
# ============================================================================

def test_projects_file_structure(results):
    """Test that projects file has correct structure."""
    print("\n" + "="*70)
    print("TEST 7: PROJECTS FILE STRUCTURE")
    print("="*70)

    if not GLOBAL_PROJECTS_FILE.exists():
        results.add_warning("Projects file", f"File doesn't exist - will be created on first save at {GLOBAL_PROJECTS_FILE}")
        return

    try:
        with open(GLOBAL_PROJECTS_FILE, 'r') as f:
            projects = json.load(f)

        if isinstance(projects, dict):
            results.add_pass("Projects file structure", f"Valid JSON object with {len(projects)} projects")

            # Validate each project structure
            for ref, proj_data in projects.items():
                required_keys = ["name", "anon_key", "service_role_key", "database_url"]
                if isinstance(proj_data, dict):
                    has_keys = [k for k in required_keys if k in proj_data]
                    results.add_pass(f"Project {ref[:10]}... structure", f"Has {len(has_keys)}/{len(required_keys)} credential fields")
        else:
            results.add_fail("Projects file structure", "Not a JSON object")

    except json.JSONDecodeError as e:
        results.add_fail("Projects file JSON", f"Invalid JSON: {str(e)[:100]}")
    except Exception as e:
        results.add_fail("Projects file reading", str(e))

# ============================================================================
# TEST 8: SKILL IMPORTS AND REFERENCES
# ============================================================================

def test_skill_imports(results):
    """Check that skills can import the local scripts module."""
    print("\n" + "="*70)
    print("TEST 8: SKILL SCRIPT IMPORTS")
    print("="*70)

    # Try to import supabase_api from the local location
    sys.path.insert(0, str(LOCAL_SCRIPTS))

    try:
        import supabase_api
        results.add_pass("supabase_api module import", "Successfully imported from local scripts")

        # Check key functions exist
        funcs = ["load_config", "load_projects", "get_access_token", "management_api_request"]
        for func in funcs:
            if hasattr(supabase_api, func):
                results.add_pass(f"Function: {func}", "Available in supabase_api module")
            else:
                results.add_fail(f"Function: {func}", "Not found in supabase_api module")

    except ImportError as e:
        results.add_fail("supabase_api import", str(e))
    except Exception as e:
        results.add_fail("supabase_api inspection", str(e))

# ============================================================================
# MAIN TEST RUNNER
# ============================================================================

def main():
    print("\n")
    print("╔" + "="*68 + "╗")
    print("║" + " "*68 + "║")
    print("║" + "  SUPABASE SKILLS CREDENTIAL LOADING TEST SUITE".center(68) + "║")
    print("║" + " "*68 + "║")
    print("╚" + "="*68 + "╝")
    print(f"\nProject Root: {PROJECT_ROOT}")
    print(f"Local Scripts: {LOCAL_SCRIPTS}")
    print(f"Global Config: {GLOBAL_CONFIG_FILE}")
    print(f"Global Projects: {GLOBAL_PROJECTS_FILE}")

    results = TestResult()

    # Run all tests
    test_credential_file_paths(results)
    test_local_scripts_exist(results)
    test_script_credential_loading(results)
    test_skill_documentation_paths(results)
    test_credential_loading_execution(results)
    test_config_file_reading(results)
    test_projects_file_structure(results)
    test_skill_imports(results)

    # Summary
    print("\n" + "="*70)
    print("TEST SUMMARY")
    print("="*70)
    summary = results.summary()
    print(f"Total Tests: {summary['total_tests']}")
    print(f"Passed: {summary['passed']}")
    print(f"Failed: {summary['failed']}")
    print(f"Warnings: {summary['warnings']}")
    print(f"Success Rate: {summary['success_rate']}")

    if results.failed:
        print("\n❌ FAILED TESTS:")
        for test in results.failed:
            print(f"  - {test['name']}: {test['reason']}")

    if results.warnings:
        print("\n⚠️  WARNINGS:")
        for test in results.warnings:
            print(f"  - {test['name']}: {test['message']}")

    # Exit code based on failures
    exit_code = 0 if not results.failed else 1
    print(f"\nExit Code: {exit_code}")

    # Output JSON report
    report = {
        "test_execution": {
            "timestamp": __import__('datetime').datetime.now().isoformat(),
            "project_root": str(PROJECT_ROOT),
            "local_scripts": str(LOCAL_SCRIPTS)
        },
        "summary": summary,
        "passed_tests": results.passed,
        "failed_tests": results.failed,
        "warnings": results.warnings
    }

    report_file = PROJECT_ROOT / "docs" / "test-results-supabase-skills.json"
    report_file.parent.mkdir(parents=True, exist_ok=True)

    with open(report_file, 'w') as f:
        json.dump(report, f, indent=2)

    print(f"\nDetailed Report: {report_file}")

    sys.exit(exit_code)

if __name__ == "__main__":
    main()
