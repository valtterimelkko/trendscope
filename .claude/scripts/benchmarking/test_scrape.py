#!/usr/bin/env python3
"""
Test script for browserless.io scraping with cookie injection.

Usage:
    # First, export cookies from your browser (use Cookie-Editor extension)
    # Save as JSON file (e.g., linear_cookies.json)

    # Test with Linear dashboard:
    python3 test_scrape.py --url "https://linear.app/YOUR_WORKSPACE/inbox" --cookies linear_cookies.json

    # Test landing page (no cookies needed):
    python3 test_scrape.py --url "https://linear.app" --landing

    # Test public dashboard (no cookies needed):
    python3 test_scrape.py --url "https://rb2b.baremetrics.com/" --landing

Environment variables:
    BROWSERLESS_API_KEY - Your browserless.io API token (required)

    Set in .env file:
        BROWSERLESS_API_KEY=your-token-here
"""

import argparse
import json
import os
import sys
import base64
from pathlib import Path
from datetime import datetime

# Load .env file if it exists
def load_env():
    env_path = Path(__file__).parent.parent.parent.parent / ".env"
    if env_path.exists():
        with open(env_path) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    os.environ.setdefault(key.strip(), value.strip())

load_env()

try:
    import requests
except ImportError:
    print("Error: requests library required. Install with: pip install requests")
    sys.exit(1)


BROWSERLESS_API_URL = "https://production-sfo.browserless.io"


def get_api_key():
    """Get browserless API key from environment."""
    key = os.environ.get("BROWSERLESS_API_KEY")
    if not key:
        print("Error: BROWSERLESS_API_KEY not set.")
        print("Add to .env file: BROWSERLESS_API_KEY=your-token-here")
        sys.exit(1)
    return key


def load_cookies(cookie_file: str) -> list:
    """Load cookies from JSON file exported by browser extension."""
    path = Path(cookie_file)
    if not path.exists():
        print(f"Error: Cookie file not found: {cookie_file}")
        sys.exit(1)

    with open(path) as f:
        cookies = json.load(f)

    # Convert from browser extension format to BrowserQL format
    formatted_cookies = []
    for cookie in cookies:
        formatted = {
            "name": cookie.get("name"),
            "value": cookie.get("value"),
            "domain": cookie.get("domain"),
            "path": cookie.get("path", "/"),
        }
        # Optional fields
        if cookie.get("secure"):
            formatted["secure"] = True
        if cookie.get("httpOnly"):
            formatted["httpOnly"] = True

        formatted_cookies.append(formatted)

    print(f"Loaded {len(formatted_cookies)} cookies from {cookie_file}")
    return formatted_cookies


def build_cookie_graphql(cookies: list, target_url: str) -> str:
    """Build the cookies array for GraphQL query."""
    # Extract base URL for cookie URL field
    from urllib.parse import urlparse
    parsed = urlparse(target_url)
    base_url = f"{parsed.scheme}://{parsed.netloc}"

    cookie_entries = []
    for c in cookies:
        # Use url field instead of domain for better compatibility
        entry_parts = [
            f'name: "{c["name"]}"',
            f'value: "{c["value"]}"',
            f'url: "{base_url}"',
            f'path: "{c["path"]}"',
        ]
        if c.get("secure"):
            entry_parts.append("secure: true")
        if c.get("httpOnly"):
            entry_parts.append("httpOnly: true")
        # Add sameSite if present
        if c.get("sameSite"):
            entry_parts.append(f'sameSite: "{c["sameSite"]}"')

        cookie_entries.append("{ " + ", ".join(entry_parts) + " }")

    return "[\n    " + ",\n    ".join(cookie_entries) + "\n  ]"


def scrape_with_bql(
    url: str,
    cookies: list = None,
    take_screenshot: bool = True,
    use_stealth: bool = True
) -> dict:
    """
    Scrape a URL using BrowserQL (GraphQL API) with cookie injection.

    This is the proper way to inject cookies before navigation.
    """
    api_key = get_api_key()
    # Use stealth endpoint for better anti-detection
    if use_stealth:
        endpoint = f"{BROWSERLESS_API_URL}/chromium/bql?token={api_key}&stealth"
    else:
        endpoint = f"{BROWSERLESS_API_URL}/chromium/bql?token={api_key}"

    # Build the GraphQL mutation
    if cookies:
        cookies_gql = build_cookie_graphql(cookies, url)
        query = f"""
mutation ScrapeWithAuth {{
  setCookies: cookies(cookies: {cookies_gql}) {{
    cookies {{
      name
      value
    }}
  }}

  goto(url: "{url}", waitUntil: networkIdle) {{
    status
  }}

  waitForTimeout(time: 3000) {{
    time
  }}

  html {{
    html
  }}

  {"screenshot { base64 }" if take_screenshot else ""}
}}
"""
    else:
        query = f"""
mutation ScrapePublic {{
  goto(url: "{url}", waitUntil: networkIdle) {{
    status
  }}

  waitForTimeout(time: 2000) {{
    time
  }}

  html {{
    html
  }}

  {"screenshot { base64 }" if take_screenshot else ""}
}}
"""

    print(f"Scraping: {url}")
    print(f"Using BrowserQL endpoint")
    if cookies:
        print(f"Injecting {len(cookies)} cookies...")

    try:
        response = requests.post(
            endpoint,
            headers={"Content-Type": "application/json"},
            json={"query": query},
            timeout=120
        )

        if response.status_code != 200:
            print(f"Error: HTTP {response.status_code}")
            print(f"Response: {response.text[:1000]}")
            return None

        result = response.json()

        # Check for GraphQL errors
        if "errors" in result:
            print(f"GraphQL Errors: {json.dumps(result['errors'], indent=2)}")
            return None

        # Extract data from GraphQL response
        data = result.get("data", {})

        return {
            "content": data.get("html", {}).get("html"),
            "screenshot": data.get("screenshot", {}).get("base64") if take_screenshot else None,
            "status": data.get("goto", {}).get("status"),
            "cookies_set": data.get("setCookies", {}).get("cookies") if cookies else None,
        }

    except requests.exceptions.Timeout:
        print("Error: Request timed out (browserless free tier has 1 min limit)")
        return None
    except Exception as e:
        print(f"Error: {e}")
        return None


def scrape_with_unblock(url: str) -> dict:
    """
    Scrape a URL using the /unblock API for Cloudflare bypass.

    This endpoint is specifically designed to bypass bot protection.
    """
    api_key = get_api_key()
    endpoint = f"{BROWSERLESS_API_URL}/unblock?token={api_key}"

    payload = {
        "url": url,
        "browserWSEndpoint": False,
        "cookies": False,
        "content": True,
        "screenshot": True
    }

    print(f"Scraping with /unblock (Cloudflare bypass): {url}")

    try:
        response = requests.post(
            endpoint,
            headers={"Content-Type": "application/json"},
            json=payload,
            timeout=90
        )

        if response.status_code != 200:
            print(f"Error: HTTP {response.status_code}")
            print(f"Response: {response.text[:500]}")
            return None

        result = response.json()
        return {
            "content": result.get("content"),
            "screenshot": result.get("screenshot"),
            "status": 200,
        }

    except Exception as e:
        print(f"Error: {e}")
        return None


def scrape_screenshot_simple(url: str) -> dict:
    """
    Get just a screenshot using the simpler /screenshot API.

    Useful for landing pages where we don't need cookies.
    """
    api_key = get_api_key()
    endpoint = f"{BROWSERLESS_API_URL}/screenshot?token={api_key}"

    payload = {
        "url": url,
        "options": {
            "fullPage": True,
            "type": "png"
        },
        "gotoOptions": {
            "waitUntil": "networkidle0"
        }
    }

    print(f"Taking screenshot: {url}")

    try:
        response = requests.post(
            endpoint,
            headers={"Content-Type": "application/json"},
            json=payload,
            timeout=60
        )

        if response.status_code != 200:
            print(f"Error: HTTP {response.status_code}")
            print(f"Response: {response.text[:500]}")
            return None

        # Response is binary PNG data
        return {"screenshot_binary": response.content}

    except Exception as e:
        print(f"Error: {e}")
        return None


def save_results(result: dict, url: str, output_dir: str = "scrape_results"):
    """Save scraping results to files."""
    out_path = Path(output_dir)
    out_path.mkdir(exist_ok=True)

    # Generate filename from URL
    from urllib.parse import urlparse
    parsed = urlparse(url)
    site_name = parsed.netloc.replace(".", "_")
    path_slug = parsed.path.replace("/", "_")[:30] if parsed.path else ""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    base_name = f"{site_name}{path_slug}_{timestamp}"

    saved_files = []

    # Save HTML content
    if result.get("content"):
        html_file = out_path / f"{base_name}.html"
        with open(html_file, "w", encoding="utf-8") as f:
            f.write(result["content"])
        saved_files.append(str(html_file))
        print(f"Saved HTML: {html_file} ({len(result['content'])} chars)")

    # Save screenshot (base64 encoded in response)
    if result.get("screenshot"):
        screenshot_file = out_path / f"{base_name}.png"
        screenshot_data = base64.b64decode(result["screenshot"])
        with open(screenshot_file, "wb") as f:
            f.write(screenshot_data)
        saved_files.append(str(screenshot_file))
        print(f"Saved screenshot: {screenshot_file} ({len(screenshot_data)} bytes)")

    # Save binary screenshot (from /screenshot endpoint)
    if result.get("screenshot_binary"):
        screenshot_file = out_path / f"{base_name}.png"
        with open(screenshot_file, "wb") as f:
            f.write(result["screenshot_binary"])
        saved_files.append(str(screenshot_file))
        print(f"Saved screenshot: {screenshot_file}")

    # Save metadata
    meta_file = out_path / f"{base_name}_meta.json"
    meta = {
        "url": url,
        "timestamp": timestamp,
        "has_content": bool(result.get("content")),
        "has_screenshot": bool(result.get("screenshot") or result.get("screenshot_binary")),
        "http_status": result.get("status"),
        "cookies_injected": len(result.get("cookies_set", [])) if result.get("cookies_set") else 0,
    }
    with open(meta_file, "w") as f:
        json.dump(meta, f, indent=2)
    saved_files.append(str(meta_file))

    return saved_files


def main():
    parser = argparse.ArgumentParser(
        description="Test browserless.io scraping with cookie injection",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )
    parser.add_argument("--url", required=True, help="URL to scrape")
    parser.add_argument("--cookies", help="Path to cookies JSON file")
    parser.add_argument("--landing", action="store_true", help="Simple screenshot mode")
    parser.add_argument("--unblock", action="store_true", help="Use /unblock API for Cloudflare bypass")
    parser.add_argument("--output", default="scrape_results", help="Output directory")
    parser.add_argument("--no-screenshot", action="store_true", help="Skip screenshot")

    args = parser.parse_args()

    print("=" * 60)
    print("Browserless.io Scraping Test")
    print("=" * 60)

    # Check API key
    api_key = get_api_key()
    print(f"API Key: {api_key[:10]}...{api_key[-4:]}")

    cookies = None
    if args.cookies:
        cookies = load_cookies(args.cookies)
    elif not args.landing:
        print("Warning: No cookies provided. Use --cookies for authenticated pages or --landing for public pages.")

    # Scrape
    if args.unblock:
        # Use /unblock for Cloudflare bypass
        result = scrape_with_unblock(args.url)
    elif args.landing:
        # Simple screenshot for landing pages
        result = scrape_screenshot_simple(args.url)
    else:
        # Full scrape with BrowserQL (supports cookie injection)
        result = scrape_with_bql(
            args.url,
            cookies=cookies,
            take_screenshot=not args.no_screenshot
        )

    if result:
        print("\n✓ Scraping successful!")
        if result.get("cookies_set"):
            print(f"  Cookies injected: {len(result['cookies_set'])}")
        if result.get("status"):
            print(f"  HTTP Status: {result['status']}")
        saved = save_results(result, args.url, args.output)
        print(f"\nSaved {len(saved)} files to {args.output}/")
    else:
        print("\n✗ Scraping failed")
        sys.exit(1)


if __name__ == "__main__":
    main()
