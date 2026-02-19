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

import pytest


def test_import_client():
    """Test 1: Import client"""
    try:
        from scraper.tiktok_scraper7_client import TikTokScraper7Client, Video
        print("✅ Import successful")
        assert True
    except Exception as e:
        pytest.fail(f"Import failed: {e}")


def test_api_key_present():
    """Test 2: Check API key is set"""
    api_key = os.getenv("RAPIDAPI_KEY")
    if not api_key:
        pytest.skip("RAPIDAPI_KEY not set - skipping live API tests")
    print(f"✅ API key found: {api_key[:15]}...")
    assert len(api_key) > 0


def test_create_client():
    """Test 3: Create client (without making request)"""
    from scraper.tiktok_scraper7_client import TikTokScraper7Client
    
    api_key = os.getenv("RAPIDAPI_KEY")
    if not api_key:
        pytest.skip("RAPIDAPI_KEY not set - skipping live API tests")
    
    try:
        client = TikTokScraper7Client(api_key)
        print("✅ Client created")
        assert client is not None
    except Exception as e:
        pytest.fail(f"Client creation failed: {e}")


@pytest.mark.asyncio
async def test_live_api_call():
    """Test 4: Make actual API call (uses 1 request from quota)"""
    from scraper.tiktok_scraper7_client import TikTokScraper7Client
    
    api_key = os.getenv("RAPIDAPI_KEY")
    if not api_key:
        pytest.skip("RAPIDAPI_KEY not set - skipping live API tests")
    
    client = TikTokScraper7Client(api_key)
    
    try:
        async with client:
            # Get trending feed with just 1 item
            videos = await client.get_trending(region="us", count=1)
            print(f"✅ API call successful - got {len(videos)} videos")
            
            assert len(videos) > 0
            assert videos[0].id is not None
            assert videos[0].stats.play_count >= 0
            
    except Exception as e:
        pytest.fail(f"API call failed: {e}")


if __name__ == "__main__":
    print("=" * 70)
    print("SAFE E2E TEST - Checking imports and basic functionality")
    print("=" * 70)
    
    pytest.main([__file__, "-v"])
    
    print("\n" + "=" * 70)
    print("To run full tests with pytest:")
    print("  export RAPIDAPI_KEY=your_key")
    print("  python -m pytest tests/test_e2e_safe.py -v")
    print("\n⚠️  Live API tests use 1 API request from your 300/month quota")
    print("=" * 70)
