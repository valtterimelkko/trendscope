#!/usr/bin/env python3
"""
Shared utilities for Supabase API operations.

Provides:
- Configuration loading (PAT, project credentials)
- Management API client (api.supabase.com/v1)
- PostgREST API client ([ref].supabase.co/rest/v1)
- Direct Postgres connection for SQL execution
- Error handling and response formatting
"""

import json
import sys
import os
import subprocess
from typing import Dict, Any, Optional, List, Tuple

# ============================================================================
# CONSTANTS
# ============================================================================

MANAGEMENT_API_URL = "https://api.supabase.com/v1"
CONFIG_FILE = "/etc/supabase/config.conf"
PROJECTS_FILE = "/etc/supabase/projects.json"

# ============================================================================
# OUTPUT HELPERS
# ============================================================================

def output_success(data: Any, message: str = "") -> None:
    """Output success response as JSON."""
    result = {"success": True, "data": data}
    if message:
        result["message"] = message
    print(json.dumps(result, indent=2, default=str))
    sys.exit(0)

def output_error(message: str, code: str = "ERROR") -> None:
    """Output error response as JSON and exit."""
    print(json.dumps({
        "success": False,
        "error": {
            "code": code,
            "message": message
        }
    }, indent=2))
    sys.exit(1)

def output_info(message: str) -> None:
    """Output info message (for streaming/progress)."""
    print(json.dumps({"info": message}))

# ============================================================================
# CONFIGURATION
# ============================================================================

_config_cache: Optional[Dict[str, str]] = None
_projects_cache: Optional[Dict[str, Dict[str, str]]] = None

def load_config() -> Dict[str, str]:
    """Load Supabase configuration from config file."""
    global _config_cache
    if _config_cache is not None:
        return _config_cache

    config = {}

    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, 'r') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#'):
                        if '=' in line:
                            key, value = line.split('=', 1)
                            config[key.strip()] = value.strip()
        except Exception as e:
            output_error(f"Failed to read config file: {str(e)}")

    _config_cache = config
    return config

def load_projects() -> Dict[str, Dict[str, str]]:
    """Load saved project configurations from projects file."""
    global _projects_cache
    if _projects_cache is not None:
        return _projects_cache

    projects = {}
    if os.path.exists(PROJECTS_FILE):
        try:
            with open(PROJECTS_FILE, 'r') as f:
                projects = json.load(f)
        except Exception as e:
            pass  # Return empty dict if file doesn't exist or is invalid

    _projects_cache = projects
    return projects

def save_project(project_ref: str, project_data: Dict[str, str]) -> None:
    """Save project configuration to projects file."""
    global _projects_cache
    projects = load_projects()
    projects[project_ref] = project_data
    _projects_cache = projects

    # Ensure directory exists
    os.makedirs(os.path.dirname(PROJECTS_FILE), exist_ok=True)

    with open(PROJECTS_FILE, 'w') as f:
        json.dump(projects, f, indent=2)

def get_project_config(project_ref: str) -> Dict[str, str]:
    """Get configuration for a specific project."""
    projects = load_projects()
    if project_ref not in projects:
        output_error(
            f"Project '{project_ref}' not found in saved projects. "
            f"Use 'save_project_credentials.py' to save credentials first.",
            "PROJECT_NOT_FOUND"
        )
    return projects[project_ref]

def get_access_token() -> str:
    """Get Supabase Personal Access Token (PAT) for Management API."""
    config = load_config()
    token = config.get('SUPABASE_ACCESS_TOKEN', '')
    if not token:
        output_error(
            f"SUPABASE_ACCESS_TOKEN not found in {CONFIG_FILE}. "
            "Create a PAT at https://supabase.com/dashboard/account/tokens",
            "NO_ACCESS_TOKEN"
        )
    return token

def get_default_org_id() -> str:
    """Get default organization ID."""
    config = load_config()
    return config.get('SUPABASE_ORG_ID', '')

# ============================================================================
# HTTP REQUESTS (using curl for reliability)
# ============================================================================

def management_api_request(
    method: str,
    endpoint: str,
    data: Optional[Dict] = None,
    params: Optional[Dict] = None
) -> Tuple[bool, Any]:
    """
    Make a request to Supabase Management API.
    
    Args:
        method: HTTP method (GET, POST, PATCH, DELETE)
        endpoint: API endpoint (e.g., /projects)
        data: Request body for POST/PATCH
        params: Query parameters
        
    Returns:
        Tuple of (success: bool, response_data: Any)
    """
    token = get_access_token()
    url = f"{MANAGEMENT_API_URL}{endpoint}"
    
    # Build query string
    if params:
        query_parts = [f"{k}={v}" for k, v in params.items() if v is not None]
        if query_parts:
            url += "?" + "&".join(query_parts)
    
    # Build curl command
    cmd = [
        "curl", "-s", "-X", method,
        "-H", f"Authorization: Bearer {token}",
        "-H", "Content-Type: application/json",
        url
    ]
    
    if data and method in ("POST", "PATCH", "PUT"):
        cmd.extend(["-d", json.dumps(data)])
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
        if result.returncode != 0:
            return False, {"error": result.stderr}
        
        if not result.stdout.strip():
            return True, None
            
        response = json.loads(result.stdout)
        
        # Check for API error responses
        if isinstance(response, dict) and "error" in response:
            return False, response
        if isinstance(response, dict) and "message" in response and response.get("statusCode", 200) >= 400:
            return False, response
            
        return True, response
        
    except subprocess.TimeoutExpired:
        return False, {"error": "Request timed out"}
    except json.JSONDecodeError:
        return True, result.stdout  # Some endpoints return plain text
    except Exception as e:
        return False, {"error": str(e)}

def postgrest_request(
    project_ref: str,
    method: str,
    table: str,
    data: Optional[Dict] = None,
    params: Optional[Dict] = None,
    select: Optional[str] = None,
    filters: Optional[List[str]] = None
) -> Tuple[bool, Any]:
    """
    Make a request to Supabase PostgREST API.
    
    Args:
        project_ref: Project reference ID
        method: HTTP method
        table: Table name
        data: Request body
        params: Query parameters
        select: Select columns
        filters: PostgREST filters (e.g., ["id=eq.1", "status=eq.active"])
        
    Returns:
        Tuple of (success: bool, response_data: Any)
    """
    project = get_project_config(project_ref)
    service_key = project.get('service_role_key', '')
    
    if not service_key:
        output_error(
            f"service_role_key not found for project '{project_ref}'",
            "NO_SERVICE_KEY"
        )
    
    url = f"https://{project_ref}.supabase.co/rest/v1/{table}"
    
    # Build query string
    query_parts = []
    if select:
        query_parts.append(f"select={select}")
    if filters:
        query_parts.extend(filters)
    if params:
        query_parts.extend([f"{k}={v}" for k, v in params.items()])
    
    if query_parts:
        url += "?" + "&".join(query_parts)
    
    # Build curl command
    cmd = [
        "curl", "-s", "-X", method,
        "-H", f"apikey: {service_key}",
        "-H", f"Authorization: Bearer {service_key}",
        "-H", "Content-Type: application/json",
        "-H", "Prefer: return=representation",
        url
    ]
    
    if data and method in ("POST", "PATCH", "PUT"):
        cmd.extend(["-d", json.dumps(data)])
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        if result.returncode != 0:
            return False, {"error": result.stderr}
        
        if not result.stdout.strip():
            return True, []
            
        response = json.loads(result.stdout)
        
        if isinstance(response, dict) and ("error" in response or "message" in response):
            return False, response
            
        return True, response
        
    except json.JSONDecodeError:
        return True, result.stdout
    except Exception as e:
        return False, {"error": str(e)}

# ============================================================================
# POSTGRES DIRECT CONNECTION
# ============================================================================

def execute_sql(
    project_ref: str,
    sql: str,
    fetch_results: bool = True
) -> Tuple[bool, Any]:
    """
    Execute SQL directly on the Postgres database.
    
    Uses psql via connection string for reliability.
    
    Args:
        project_ref: Project reference ID
        sql: SQL statement to execute
        fetch_results: Whether to fetch and return results
        
    Returns:
        Tuple of (success: bool, result: Any)
    """
    project = get_project_config(project_ref)
    db_url = project.get('database_url', '')
    
    if not db_url:
        output_error(
            f"database_url not found for project '{project_ref}'. "
            "Save it using save_project_credentials.py",
            "NO_DATABASE_URL"
        )
    
    # Use psql to execute SQL
    cmd = ["psql", db_url, "-c", sql]
    
    if fetch_results:
        # Output in JSON-like format
        cmd = ["psql", db_url, "-t", "-A", "-F", ",", "-c", sql]
    
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=60,
            env={**os.environ, "PGCONNECT_TIMEOUT": "10"}
        )
        
        if result.returncode != 0:
            error_msg = result.stderr.strip()
            return False, {"error": error_msg}
        
        output = result.stdout.strip()
        return True, {"output": output, "rows_affected": output.count('\n') + 1 if output else 0}
        
    except subprocess.TimeoutExpired:
        return False, {"error": "Query timed out after 60 seconds"}
    except FileNotFoundError:
        return False, {"error": "psql not found. Install postgresql-client."}
    except Exception as e:
        return False, {"error": str(e)}

def execute_sql_file(
    project_ref: str,
    sql_file: str
) -> Tuple[bool, Any]:
    """
    Execute a SQL file on the Postgres database.
    
    Args:
        project_ref: Project reference ID
        sql_file: Path to SQL file
        
    Returns:
        Tuple of (success: bool, result: Any)
    """
    project = get_project_config(project_ref)
    db_url = project.get('database_url', '')
    
    if not db_url:
        output_error(
            f"database_url not found for project '{project_ref}'",
            "NO_DATABASE_URL"
        )
    
    if not os.path.exists(sql_file):
        output_error(f"SQL file not found: {sql_file}", "FILE_NOT_FOUND")
    
    cmd = ["psql", db_url, "-f", sql_file]
    
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=120,
            env={**os.environ, "PGCONNECT_TIMEOUT": "10"}
        )
        
        if result.returncode != 0:
            return False, {"error": result.stderr.strip(), "output": result.stdout}
        
        return True, {"output": result.stdout.strip()}
        
    except subprocess.TimeoutExpired:
        return False, {"error": "SQL file execution timed out"}
    except Exception as e:
        return False, {"error": str(e)}

# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

def validate_project_ref(ref: str) -> bool:
    """Validate project reference format."""
    import re
    return bool(re.match(r'^[a-z]{20}$', ref))

def format_table(headers: List[str], rows: List[List[Any]]) -> str:
    """Format data as a simple ASCII table."""
    if not rows:
        return "No data"
    
    # Calculate column widths
    widths = [len(h) for h in headers]
    for row in rows:
        for i, cell in enumerate(row):
            widths[i] = max(widths[i], len(str(cell)))
    
    # Build table
    lines = []
    header_line = " | ".join(h.ljust(widths[i]) for i, h in enumerate(headers))
    lines.append(header_line)
    lines.append("-+-".join("-" * w for w in widths))
    
    for row in rows:
        line = " | ".join(str(cell).ljust(widths[i]) for i, cell in enumerate(row))
        lines.append(line)
    
    return "\n".join(lines)
