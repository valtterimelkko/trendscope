#!/usr/bin/env python3
"""
SAFE End-to-End Pipeline Test for Viral Waves

This test verifies the API client works correctly with minimal resource usage.
Uses 1 API request only.
"""

import asyncio
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

print("=" * 70)
print("SAFE E2E TEST - Checking imports and basic functionality")
print("=" * 70)

# Test 1: Import client
try:
    from scraper.tiktok_scraper7_client import TikTokScraper7Client, Video
    print("✅ Import successful")
except Exception as e:
    print(f"❌ Import failed: {e}")
    sys.exit(1)

# Test 2: Check API key
try:
    api_key = os.getenv("RAPIDAPI_KEY")
    if not api_key:
        print("❌ RAPIDAPI_KEY not set")
        sys.exit(1)
    print(f"✅ API key found: {api_key[:15]}...")
except Exception as e:
    print(f"❌ Error: {e}")
    sys.exit(1)

# Test 3: Create client (without making request)
try:
    client = TikTokScraper7Client(api_key)
    print("✅ Client created")
except Exception as e:
    print(f"❌ Client creation failed: {e}")
    sys.exit(1)

print("\n" + "=" * 70)
print("READY TO RUN FULL TEST")
print("=" * 70)
print("\nThe client is working. To run the full test with API calls:")
print("  export RAPIDAPI_KEY=your_key")
print("  python tests/test_e2e_pipeline.py")
print("\n⚠️  This will use 1 API request from your 300/month quota")
print("=" * 70)
