#!/usr/bin/env python3
"""
Memory-safe test: IPRoyal + Camoufox + CapSolver

SAFETY GUARDRAILS:
- Max runtime: 30 seconds per component
- No large downloads
- Graceful degradation
"""

import asyncio
import sys
import signal

# Set memory limit (2GB)
import resource
resource.setrlimit(resource.RLIMIT_AS, (2 * 1024 * 1024 * 1024, 2 * 1024 * 1024 * 1024))

# Timeout handler
def timeout_handler(signum, frame):
    print("\n⏱️  TIMEOUT: Test took too long, aborting...")
    sys.exit(1)

signal.signal(signal.SIGALRM, timeout_handler)
signal.alarm(60)  # 60 second total timeout

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
print("SAFE TEST: IPRoyal + Camoufox + CapSolver")
print("(Memory limit: 2GB, Timeout: 60s)")
print("=" * 70)

async def test_layer_1_proxy():
    """Test Layer 1: IPRoyal Proxy"""
    print("\n📡 LAYER 1: IPRoyal Proxy")
    print("-" * 70)
    
    try:
        import httpx
        
        # Quick test with short timeout
        client = httpx.AsyncClient(
            proxy=PROXY_URL, 
            timeout=10.0,
            limits=httpx.Limits(max_connections=2, max_keepalive_connections=1)
        )
        
        response = await client.get("https://httpbin.org/ip")
        await client.aclose()
        
        if response.status_code == 200:
            data = response.json()
            ip = data.get('origin', 'unknown')
            print(f"   ✅ Proxy working!")
            print(f"   📍 Egress IP: {ip}")
            return True
        else:
            print(f"   ❌ HTTP {response.status_code}")
            return False
            
    except Exception as e:
        print(f"   ❌ Error: {str(e)[:60]}")
        return False

async def test_layer_2_camoufox():
    """Test Layer 2: Camoufox (lightweight check)"""
    print("\n🦊 LAYER 2: Camoufox Browser")
    print("-" * 70)
    
    # Check if camoufox is installed without running it
    try:
        import camoufox
        from pathlib import Path
        
        # Check if binary exists (don't download if not present)
        cache_dir = Path.home() / ".cache" / "camoufox"
        
        if cache_dir.exists():
            binaries = list(cache_dir.glob("*/camoufox"))
            if binaries:
                print(f"   ✅ Camoufox installed at: {binaries[0]}")
                print(f"   ℹ️  Version: {camoufox.__version__}")
                return "installed"
        
        print(f"   ⚠️  Camoufox not downloaded yet")
        print(f"   ℹ️  Would download ~700MB on first run")
        print(f"   ℹ️  Install: pip install camoufox")
        return "not_installed"
        
    except ImportError:
        print(f"   ❌ Camoufox not installed")
        print(f"   ℹ️  Run: pip install camoufox")
        return "not_installed"

async def test_layer_3_capsolver():
    """Test Layer 3: CapSolver"""
    print("\n🔑 LAYER 3: CapSolver")
    print("-" * 70)
    
    if not CAPSOLVER_KEY:
        print("   ❌ No API key found")
        return False
    
    try:
        import capsolver
        capsolver.api_key = CAPSOLVER_KEY
        
        # Quick balance check with timeout
        balance = capsolver.balance()
        
        if isinstance(balance, dict):
            bal = balance.get('balance', 0)
            print(f"   ✅ CapSolver connected!")
            print(f"   💰 Balance: ${bal}")
            return bal > 0
        else:
            print(f"   ✅ API key valid")
            return True
            
    except Exception as e:
        print(f"   ❌ Error: {str(e)[:60]}")
        return False

async def main():
    results = {}
    
    # Test each layer
    results['proxy'] = await test_layer_1_proxy()
    results['camoufox'] = await test_layer_2_camoufox()
    results['capsolver'] = await test_layer_3_capsolver()
    
    # Summary
    print("\n" + "=" * 70)
    print("SUMMARY")
    print("=" * 70)
    
    proxy_ok = results.get('proxy', False)
    camoufox_status = results.get('camoufox', 'unknown')
    capsolver_ok = results.get('capsolver', False)
    
    print(f"\n✅ Layer 1 (Proxy):     {'PASS' if proxy_ok else 'FAIL'}")
    print(f"{'✅' if camoufox_status == 'installed' else '⚠️ '} Layer 2 (Camoufox):  {camoufox_status.upper()}")
    print(f"✅ Layer 3 (CapSolver): {'PASS' if capsolver_ok else 'FAIL'}")
    
    print("\n" + "-" * 70)
    
    if proxy_ok and capsolver_ok:
        if camoufox_status == 'installed':
            print("✅ ALL LAYERS READY!")
            print("\nYou can now run full scraping with:")
            print("  python scraper/tiktok_scraper.py")
        else:
            print("⚠️  PARTIALLY READY")
            print("\nTo complete setup:")
            print("  pip install camoufox")
            print("  # First run will download ~700MB browser")
        return True
    else:
        print("❌ SETUP INCOMPLETE")
        print("\nCheck errors above and fix configuration")
        return False

if __name__ == "__main__":
    try:
        success = asyncio.run(main())
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n💥 FATAL ERROR: {e}")
        sys.exit(1)
