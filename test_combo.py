#!/usr/bin/env python3
"""
Minimal test: IPRoyal Residential + Camoufox + CapSolver

This tests the three-layer approach:
1. IPRoyal residential proxy (IP reputation)
2. Camoufox (browser fingerprint evasion)
3. CapSolver (captcha solving fallback)
"""

import asyncio
import os
import time
from typing import Optional, Dict, Any

# Load credentials from .bashrc
def load_from_bashrc(var_name: str) -> Optional[str]:
    try:
        with open('/root/.bashrc', 'r') as f:
            for line in f:
                line = line.strip()
                if f'{var_name}=' in line:
                    parts = line.split('=', 1)
                    if len(parts) == 2:
                        return parts[1].strip('"\'')
    except:
        pass
    return None

# Load proxy and API key
PROXY_URL = load_from_bashrc('PROXY_URL') or "http://***REMOVED***:***REMOVED***@geo.iproyal.com:12321"
CAPSOLVER_KEY = load_from_bashrc('CAPSOLVER_API_KEY')

print("=" * 70)
print("MINIMAL TEST: IPRoyal + Camoufox + CapSolver")
print("=" * 70)
print(f"\n1. Proxy: {PROXY_URL[:60]}...")
print(f"2. CapSolver Key: {CAPSOLVER_KEY[:20] if CAPSOLVER_KEY else 'NOT FOUND'}...")
print(f"3. Testing: TikTok scraping with all three layers")

async def test_combo():
    """Test the three-layer combo."""
    
    # Step 1: Check CapSolver balance
    print("\n" + "-" * 70)
    print("STEP 1: Checking CapSolver balance...")
    print("-" * 70)
    
    try:
        import capsolver
        capsolver.api_key = CAPSOLVER_KEY
        balance = capsolver.balance()
        print(f"✅ CapSolver balance: {balance}")
    except Exception as e:
        print(f"❌ CapSolver error: {e}")
        balance = 0
    
    # Step 2: Test with Camoufox + Proxy
    print("\n" + "-" * 70)
    print("STEP 2: Testing Camoufox + IPRoyal Proxy...")
    print("-" * 70)
    
    try:
        from camoufox import AsyncCamoufox
        from urllib.parse import urlparse
        
        # Parse proxy
        parsed = urlparse(PROXY_URL)
        proxy_config = {
            "server": f"{parsed.scheme}://{parsed.hostname}:{parsed.port}",
            "username": parsed.username,
            "password": parsed.password
        }
        
        print(f"🔄 Launching Camoufox with proxy...")
        print(f"   Proxy server: {proxy_config['server']}")
        
        # Camoufox handles fingerprinting automatically
        # Don't pass custom fingerprint - it generates Firefox ones internally
        
        config = {
            'proxy': proxy_config,
            'headless': True,
            'humanize': True,  # Enable human-like behavior
        }
        
        async with AsyncCamoufox(**config) as browser:
            print("✅ Camoufox launched with proxy!")
            
            page = await browser.new_page()
            
            # Test 1: Check IP
            print("\n🔄 Checking IP through proxy...")
            await page.goto("https://httpbin.org/ip")
            content = await page.content()
            if "origin" in content:
                # Extract IP
                start = content.find('"origin"') + 10
                end = content.find('"', start)
                ip = content[start:end]
                print(f"✅ Egress IP: {ip}")
            
            # Test 2: Navigate to TikTok
            print("\n🔄 Navigating to TikTok...")
            await page.goto("https://www.tiktok.com", timeout=60000)
            
            print(f"✅ Loaded! URL: {page.url}")
            print(f"   Title: {await page.title()}")
            
            # Wait for content to load
            await page.wait_for_timeout(5000)
            
            # Check for captcha
            content = await page.content()
            has_captcha = "captcha" in content.lower() or "verify" in content.lower()
            
            if has_captcha:
                print("\n⚠️  Captcha detected!")
                
                # Step 3: Try CapSolver
                if balance and (isinstance(balance, dict) and balance.get('balance', 0) > 0.5 or 
                               (isinstance(balance, (int, float)) and balance > 0.5)):
                    print("\n" + "-" * 70)
                    print("STEP 3: Attempting CapSolver...")
                    print("-" * 70)
                    
                    # Take screenshot of captcha
                    screenshot_path = "/tmp/tiktok_captcha.png"
                    await page.screenshot(path=screenshot_path)
                    print(f"📸 Screenshot saved: {screenshot_path}")
                    
                    # Note: TikTok captcha is complex (often reCaptcha v3 or custom)
                    # This is a simplified demonstration
                    print("⚠️  TikTok captcha is complex - requires specific implementation")
                    print("   Would need to identify captcha type and send to CapSolver")
                    
                else:
                    print("\n❌ Insufficient CapSolver balance")
            else:
                print("\n✅ No captcha! Page loaded successfully")
                
                # Try to find video content
                print("\n🔄 Looking for video content...")
                
                # Common TikTok selectors
                selectors = [
                    '[data-e2e="recommend-list-item"]',
                    '[data-e2e="card-item"]',
                    'a[href*="/video/"]',
                ]
                
                for selector in selectors:
                    elements = await page.query_selector_all(selector)
                    if len(elements) > 0:
                        print(f"✅ Found {len(elements)} video elements with: {selector}")
                        
                        # Get first video info
                        if len(elements) > 0:
                            el = elements[0]
                            href = await el.get_attribute('href')
                            if href:
                                print(f"   Video link: {href}")
                        break
                else:
                    print("⚠️  No video elements found (may need to scroll)")
                
                return True
                
    except ImportError as e:
        print(f"\n❌ Import error: {e}")
        print("   Run: pip install camoufox capsolver")
        return False
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return False

# Run test
if __name__ == "__main__":
    success = asyncio.run(test_combo())
    
    print("\n" + "=" * 70)
    if success:
        print("✅ TEST PASSED: Combo works!")
        print("   - IPRoyal proxy: Connected")
        print("   - Camoufox: Evading detection")
        print("   - No captcha: Clean page load")
    else:
        print("⚠️  TEST INCOMPLETE")
        print("   Check errors above")
    print("=" * 70)
