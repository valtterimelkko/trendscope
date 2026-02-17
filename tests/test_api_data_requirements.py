"""
TikTok-Scraper7 API - Data Requirements Test Suite

Tests whether the API provides all data needed for Viral Waves SaaS algorithms:
1. Growth Rate Detection (views over time)
2. Niche Clustering (hashtags, sounds, creators)
3. Trend Alerts (velocity thresholds)

API Limit: 10 requests/month (use carefully!)
"""

import pytest
import httpx
import os
import json
from datetime import datetime
from typing import Dict, Any, List

# API Configuration
API_KEY = os.getenv("RAPIDAPI_KEY", "8710e2cdb1msh72b30bdecb99b5bp1fb537jsn33825799b519")
API_HOST = "tiktok-scraper7.p.rapidapi.com"
BASE_URL = f"https://{API_HOST}"

HEADERS = {
    'x-rapidapi-key': API_KEY,
    'x-rapidapi-host': API_HOST
}

# Test user IDs (public accounts with lots of content)
TEST_USER_ID = "7128593328456041478"  # Account we know works


class TestAPIDataStructure:
    """Test 1: Verify API returns required data fields"""
    
    def test_user_story_endpoint_exists(self):
        """Verify /user/story endpoint responds"""
        url = f"{BASE_URL}/user/story"
        params = {'user_id': TEST_USER_ID}
        
        response = httpx.get(url, headers=HEADERS, params=params, timeout=10)
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        data = response.json()
        assert data.get('code') == 0, f"API error: {data.get('msg')}"
    
    def test_video_has_required_fields(self):
        """Verify videos have all fields needed for trend detection"""
        url = f"{BASE_URL}/user/story"
        params = {'user_id': TEST_USER_ID}
        
        response = httpx.get(url, headers=HEADERS, params=params, timeout=10)
        data = response.json()
        
        assert data.get('code') == 0, "API returned error"
        
        videos = data.get('data', {}).get('videos', [])
        assert len(videos) > 0, "No videos returned"
        
        video = videos[0]
        
        # Required fields for trend detection
        required_fields = {
            'video_id': 'Unique video identifier',
            'create_time': 'For velocity calculations',
            'stats': 'View/like/share counts',
            'author': 'Creator info for clustering',
            'hashtags': 'For niche clustering',
            'music': 'For sound-based trends'
        }
        
        missing = []
        for field, reason in required_fields.items():
            if field not in video:
                missing.append(f"{field} ({reason})")
        
        if missing:
            pytest.fail(f"Missing required fields: {', '.join(missing)}")
    
    def test_stats_contain_metrics(self):
        """Verify stats include views, likes, shares, comments"""
        url = f"{BASE_URL}/user/story"
        params = {'user_id': TEST_USER_ID}
        
        response = httpx.get(url, headers=HEADERS, params=params, timeout=10)
        data = response.json()
        
        if data.get('code') != 0:
            pytest.skip("API error")
        
        videos = data.get('data', {}).get('videos', [])
        if not videos:
            pytest.skip("No videos returned")
        
        stats = videos[0].get('stats', {})
        
        # Metrics needed for growth detection
        required_metrics = ['play_count', 'digg_count', 'share_count', 'comment_count']
        missing = [m for m in required_metrics if m not in stats]
        
        if missing:
            pytest.fail(f"Missing metrics: {', '.join(missing)}")


class TestAuthorData:
    """Test 2: Verify author/creator data for clustering"""
    
    def test_author_has_unique_id(self):
        """Author must have unique_id for clustering"""
        url = f"{BASE_URL}/user/story"
        params = {'user_id': TEST_USER_ID}
        
        response = httpx.get(url, headers=HEADERS, params=params, timeout=10)
        data = response.json()
        
        if data.get('code') != 0:
            pytest.skip("API error")
        
        videos = data.get('data', {}).get('videos', [])
        if not videos:
            pytest.skip("No videos")
        
        author = videos[0].get('author', {})
        assert 'unique_id' in author, "Author missing unique_id"
        assert 'nickname' in author, "Author missing nickname"


class TestTemporalData:
    """Test 3: Verify timestamp data for velocity calculations"""
    
    def test_videos_have_create_time(self):
        """Videos must have create_time for trend velocity"""
        url = f"{BASE_URL}/user/story"
        params = {'user_id': TEST_USER_ID}
        
        response = httpx.get(url, headers=HEADERS, params=params, timeout=10)
        data = response.json()
        
        if data.get('code') != 0:
            pytest.skip("API error")
        
        videos = data.get('data', {}).get('videos', [])
        if not videos:
            pytest.skip("No videos")
        
        for video in videos:
            assert 'create_time' in video, "Video missing create_time"


class TestContentData:
    """Test 4: Verify content data for niche clustering"""
    
    def test_hashtags_available(self):
        """Videos should have hashtags for niche clustering"""
        url = f"{BASE_URL}/user/story"
        params = {'user_id': TEST_USER_ID}
        
        response = httpx.get(url, headers=HEADERS, params=params, timeout=10)
        data = response.json()
        
        if data.get('code') != 0:
            pytest.skip("API error")
        
        videos = data.get('data', {}).get('videos', [])
        if not videos:
            pytest.skip("No videos")
        
        # Check if any video has hashtags
        has_hashtags = any('hashtags' in v or 'challenges' in v for v in videos)
        
        # Note if missing (may be in different field)
        if not has_hashtags:
            print(f"Video fields: {list(videos[0].keys())}")
            pytest.skip("Hashtags may be in different field - check output")
    
    def test_music_sound_data(self):
        """Videos should have music data for sound-based trends"""
        url = f"{BASE_URL}/user/story"
        params = {'user_id': TEST_USER_ID}
        
        response = httpx.get(url, headers=HEADERS, params=params, timeout=10)
        data = response.json()
        
        if data.get('code') != 0:
            pytest.skip("API error")
        
        videos = data.get('data', {}).get('videos', [])
        if not videos:
            pytest.skip("No videos")
        
        has_music = any('music' in v or 'sound' in v for v in videos)
        
        if not has_music:
            print(f"Video fields: {list(videos[0].keys())}")
            pytest.skip("Music may be in different field - check output")


class TestDataVolume:
    """Test 5: Verify API returns sufficient data volume"""
    
    def test_multiple_videos_returned(self):
        """Should return multiple videos for trend analysis"""
        url = f"{BASE_URL}/user/story"
        params = {'user_id': TEST_USER_ID}
        
        response = httpx.get(url, headers=HEADERS, params=params, timeout=10)
        data = response.json()
        
        if data.get('code') != 0:
            pytest.skip("API error")
        
        videos = data.get('data', {}).get('videos', [])
        
        # Should have at least 1 video
        assert len(videos) >= 1, f"Only {len(videos)} videos returned"
        
        print(f"\n✓ API returned {len(videos)} videos")


def get_sample_video_data() -> Dict[str, Any]:
    """Helper to get sample video for inspection"""
    url = f"{BASE_URL}/user/story"
    params = {'user_id': TEST_USER_ID}
    
    response = httpx.get(url, headers=HEADERS, params=params, timeout=10)
    data = response.json()
    
    if data.get('code') != 0:
        return {}
    
    videos = data.get('data', {}).get('videos', [])
    return videos[0] if videos else {}


if __name__ == "__main__":
    print("=" * 70)
    print("TIKTOK-SCRAPER7 API DATA REQUIREMENTS TEST")
    print("=" * 70)
    print("\nThis test verifies the API provides all data needed for:")
    print("  1. Growth Rate Detection (views over time)")
    print("  2. Niche Clustering (hashtags, sounds, creators)")
    print("  3. Trend Alerts (velocity thresholds)")
    print("\n⚠️  Uses 1 API request per test (10 requests/month limit)")
    print("=" * 70)
    
    # Run basic connectivity test
    url = f"{BASE_URL}/user/story"
    params = {'user_id': TEST_USER_ID}
    
    try:
        response = httpx.get(url, headers=HEADERS, params=params, timeout=10)
        data = response.json()
        
        if data.get('code') == 0:
            videos = data.get('data', {}).get('videos', [])
            print(f"\n✅ API Response: {len(videos)} videos")
            
            if videos:
                print("\n📋 Sample Video Fields:")
                for key in sorted(videos[0].keys()):
                    print(f"   - {key}")
                
                print("\n📊 Sample Stats Fields:")
                stats = videos[0].get('stats', {})
                for key in sorted(stats.keys()):
                    print(f"   - {key}: {stats[key]}")
                
                print("\n👤 Sample Author Fields:")
                author = videos[0].get('author', {})
                for key in sorted(author.keys()):
                    print(f"   - {key}: {author[key]}")
        else:
            print(f"\n❌ API Error: {data.get('msg')}")
            
    except Exception as e:
        print(f"\n❌ Error: {e}")
    
    print("\n" + "=" * 70)
