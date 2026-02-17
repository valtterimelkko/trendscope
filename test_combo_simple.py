#!/usr/bin/env python3
"""
Quick test: IPRoyal + Camoufox + CapSolver
Simple version with shorter timeouts
"""

import asyncio
import os

# Load credentials
def load_from_bashrc(var_name: str):
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

PROXY_URL = load_from_bashrc('PROXY_URL') or "http://***REMOVED***:***REMOVED***@geo.iproyal.com:12321"
CAPSOLVER_KEY = load_from_bashrc('CAPSOLVER_API_KEY')

print("=" * 70)
print("QUICK TEST: IPRoyal + Camoufox + CapSolver")
print("=" * 70)

async def quick_test():
    # Step 1: Check CapSolver
    print("\n1. Checking CapSolver...")
    try:
        import capsolver
        capsolver.api_key = CAPSOLVER_KEY
        balance = capsolver.balance()
        print(f"   ✅ Balance: ${balance.get('balance', 0) if isinstance(balance, dict) else balance}")
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    # Step 2: Test Camoufox + Proxy
    print("\n2. Testing Camoufox + IPRoyal Proxy...")
    try:
        from camoufox import AsyncCamoufox
        from urllib.parse import urlparse
        
        parsed = urlparse(PROXY_URL)
        proxy_config = {
            "server": f"{parsed.scheme}://{parsed.hostname}:{parsed.port}",
            "username": parsed.username,
            "password": parsed.password
        }
        
        print(f"   Proxy: {proxy_config['server']}")
        print(f"   🔄 Launching Camoufox...")
        
        async with AsyncCamoufox(
            proxy=proxy_config,
            headless=True,
            geoip=True  # Recommended when using proxy
        ) as browser:
            print("   ✅ Camoufox launched!")
            
            page = await browser.new_page()
            
            # Quick IP check
            print("   🔄 Checking IP...")
            await page.goto("https://httpbin.org/ip", timeout=15000)
            content = await page.content()
            
            if "origin" in content:
                import re
                ip_match = re.search(r'"origin":\s*"([^"]+)"', content)
                if ip_match:
                    print(f"   ✅ Egress IP: {ip_match.group(1)}")
            
            # Quick TikTok test
            print("   🔄 Loading TikTok...")
            await page.goto("https://www.tiktok.com/explore", timeout=30000)
            
            title = await page.title()
            url = page.url
            print(f"   ✅ Loaded!")
            print(f"      URL: {url}")
            print(f"      Title: {title}")
            
            # Check for captcha
            content = await page.content()
            has_captcha = "captcha" in content.lower()
            
            if has_captcha:
                print("   ⚠️  Captcha detected")
                return "captcha"
            else:
                print("   ✅ No captcha - clean load!")
                return "success"
                
    except Exception as e:
        print(f"   ❌ Error: {str(e)[:80]}")
        return "error"

result = asyncio.run(quick_test())

print("\n" + "=" * 70)
if result == "success":
    print("✅ TEST PASSED: Combo works!")
    print("   All 3 layers functioning:")
    print("   - IPRoyal proxy: Connected")
    print("   - Camoufox: Evading detection")
    print("   - No captcha: Clean access")
elif result == "captcha":
    print("⚠️  CAPTCHA DETECTED")
    print("   Layers 1-2 work, need CapSolver for layer 3")
else:
    print("❌ TEST FAILED")
print("=" * 70)
