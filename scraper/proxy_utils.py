"""
Proxy utilities for TikTok scraping with IPRoyal.

Handles:
- Proxy URL validation
- Credential diagnostics
- Automatic URL encoding
- Connection testing
"""

import os
import asyncio
from typing import Optional, Dict, Any
from urllib.parse import urlparse, quote


def validate_proxy_url(proxy_url: str) -> Dict[str, Any]:
    """
    Validate proxy URL and return diagnostics.
    
    Args:
        proxy_url: The proxy URL to validate
        
    Returns:
        Dictionary with validation results and diagnostics
    """
    result = {
        "valid": False,
        "url": proxy_url[:60] + "..." if len(proxy_url) > 60 else proxy_url,
        "issues": [],
        "warnings": [],
        "components": {},
    }
    
    if not proxy_url:
        result["issues"].append("Proxy URL is empty")
        return result
    
    try:
        parsed = urlparse(proxy_url)
        
        # Check scheme
        if not parsed.scheme:
            result["issues"].append("Missing scheme (http:// or https://)")
        elif parsed.scheme not in ("http", "https", "socks5"):
            result["issues"].append(f"Invalid scheme: {parsed.scheme}")
        
        # Check host
        if not parsed.hostname:
            result["issues"].append("Missing hostname")
        else:
            result["components"]["host"] = parsed.hostname
        
        # Check port
        if not parsed.port:
            result["issues"].append("Missing port")
        else:
            result["components"]["port"] = parsed.port
        
        # Check credentials
        if not parsed.username:
            result["issues"].append("Missing username")
        else:
            result["components"]["username"] = parsed.username[:10] + "..."
        
        if not parsed.password:
            result["issues"].append("Missing password")
        else:
            result["components"]["password_length"] = len(parsed.password)
            
            # Check for session lifetime indicator
            if "lifetime-" in parsed.password:
                result["warnings"].append(
                    "Password contains 'lifetime-' - these may be temporary session "
                    "credentials that expire (e.g., lifetime-30m = 30 minutes)"
                )
            
            # Check for session ID
            if "_session-" in parsed.password:
                result["warnings"].append(
                    "Password contains session ID - session may have expired"
                )
        
        # Mark as valid if no critical issues
        if not result["issues"]:
            result["valid"] = True
            
    except Exception as e:
        result["issues"].append(f"Failed to parse URL: {e}")
    
    return result


def encode_proxy_credentials(proxy_url: str) -> str:
    """
    URL-encode proxy credentials to handle special characters.
    
    Args:
        proxy_url: Raw proxy URL
        
    Returns:
        Proxy URL with encoded credentials
    """
    try:
        parsed = urlparse(proxy_url)
        
        # Encode username and password
        encoded_username = quote(parsed.username or "", safe='')
        encoded_password = quote(parsed.password or "", safe='')
        
        # Reconstruct URL
        return (
            f"{parsed.scheme}://"
            f"{encoded_username}:{encoded_password}@"
            f"{parsed.hostname}:{parsed.port}"
        )
    except Exception:
        return proxy_url


async def test_proxy_connection(
    proxy_url: str,
    test_url: str = "https://httpbin.org/ip",
    timeout: float = 15.0
) -> Dict[str, Any]:
    """
    Test proxy connection and return results.
    
    Args:
        proxy_url: Proxy URL to test
        test_url: URL to fetch for testing
        timeout: Request timeout in seconds
        
    Returns:
        Dictionary with test results
    """
    result = {
        "success": False,
        "proxy_url": proxy_url[:60] + "..." if len(proxy_url) > 60 else proxy_url,
        "test_url": test_url,
        "error": None,
        "response": None,
        "egress_ip": None,
    }
    
    try:
        import httpx
        
        client = httpx.AsyncClient(proxy=proxy_url, timeout=timeout)
        try:
            response = await client.get(test_url)
            result["response"] = {
                "status_code": response.status_code,
                "headers": dict(response.headers),
            }
            
            if response.status_code == 200:
                result["success"] = True
                try:
                    data = response.json()
                    result["egress_ip"] = data.get("origin")
                except:
                    pass
            elif response.status_code == 407:
                result["error"] = (
                    "Proxy authentication failed (407). "
                    "Credentials may be expired or invalid."
                )
            else:
                result["error"] = f"Unexpected status code: {response.status_code}"
                
        finally:
            await client.aclose()
            
    except ImportError:
        result["error"] = "httpx not installed (pip install httpx)"
    except Exception as e:
        result["error"] = str(e)
    
    return result


def load_proxy_from_env() -> Optional[str]:
    """
    Load proxy URL from environment variables.
    
    Checks (in order):
    1. PROXY_URL environment variable
    2. .env file in current directory
    3. REDDIT_PROXY_URL (for compatibility with other skills)
    
    Returns:
        Proxy URL or None if not found
    """
    # Check environment variable
    proxy = os.environ.get("PROXY_URL")
    if proxy:
        return proxy
    
    # Check .env file
    try:
        env_path = os.path.join(os.getcwd(), ".env")
        if os.path.exists(env_path):
            with open(env_path) as f:
                for line in f:
                    if line.startswith("PROXY_URL="):
                        return line.strip().split("=", 1)[1]
    except:
        pass
    
    # Check for Reddit proxy (compatibility)
    proxy = os.environ.get("REDDIT_PROXY_URL")
    if proxy:
        return proxy
    
    return None


def get_proxy_status() -> Dict[str, Any]:
    """
    Get complete proxy status and diagnostics.
    
    Returns:
        Dictionary with proxy configuration status
    """
    proxy_url = load_proxy_from_env()
    
    status = {
        "configured": proxy_url is not None,
        "proxy_url": None,
        "validation": None,
        "connection_test": None,
    }
    
    if proxy_url:
        status["proxy_url"] = proxy_url[:60] + "..." if len(proxy_url) > 60 else proxy_url
        status["validation"] = validate_proxy_url(proxy_url)
        
        # Try to run connection test
        try:
            loop = asyncio.get_event_loop()
            status["connection_test"] = loop.run_until_complete(
                test_proxy_connection(proxy_url)
            )
        except Exception as e:
            status["connection_test"] = {"error": str(e)}
    
    return status


def print_proxy_diagnostics():
    """Print human-readable proxy diagnostics."""
    print("=" * 70)
    print("PROXY CONFIGURATION DIAGNOSTICS")
    print("=" * 70)
    
    proxy_url = load_proxy_from_env()
    
    if not proxy_url:
        print("\n❌ PROXY NOT CONFIGURED")
        print("\n   No proxy URL found in:")
        print("   - PROXY_URL environment variable")
        print("   - .env file")
        print("   - REDDIT_PROXY_URL environment variable")
        print("\n   To configure, add to .env:")
        print("   PROXY_URL=http://user:pass@host:port")
        return
    
    print(f"\n📋 Proxy URL: {proxy_url[:70]}...")
    
    # Validate
    validation = validate_proxy_url(proxy_url)
    
    print("\n📊 Validation Results:")
    if validation["valid"]:
        print("   ✅ URL structure is valid")
    else:
        print("   ❌ URL has issues:")
        for issue in validation["issues"]:
            print(f"      - {issue}")
    
    if validation["warnings"]:
        print("\n⚠️  Warnings:")
        for warning in validation["warnings"]:
            print(f"      - {warning}")
    
    if validation["components"]:
        print("\n📎 Components:")
        for key, value in validation["components"].items():
            print(f"      {key}: {value}")
    
    # Test connection
    print("\n🧪 Testing connection...")
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        test_result = loop.run_until_complete(test_proxy_connection(proxy_url))
        loop.close()
        
        if test_result["success"]:
            print("   ✅ Connection successful!")
            print(f"   📡 Egress IP: {test_result.get('egress_ip', 'unknown')}")
        else:
            print("   ❌ Connection failed")
            print(f"   Error: {test_result.get('error', 'Unknown error')}")
            
            if "407" in str(test_result.get("error", "")):
                print("\n   🔴 AUTHENTICATION FAILED (407)")
                print("   ")
                print("   This means your proxy credentials are invalid or expired.")
                print("   ")
                print("   If using IPRoyal:")
                print("   1. Log into your IPRoyal dashboard")
                print("   2. Generate new residential proxy credentials")
                print("   3. Update your .env file with the new PROXY_URL")
                print("   ")
                print("   Note: Session-based credentials (with _session-XXX) expire")
                print("   after their lifetime period (e.g., 30m, 1h, etc.)")
                
    except Exception as e:
        print(f"   ❌ Test failed: {e}")
    
    print("\n" + "=" * 70)


if __name__ == "__main__":
    print_proxy_diagnostics()
