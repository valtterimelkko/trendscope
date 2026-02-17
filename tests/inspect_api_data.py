#!/usr/bin/env python3
"""
TikTok-Scraper7 API Data Inspector

Safely inspects API response structure to verify it contains
data needed for Viral Waves SaaS algorithms.

Uses only 1 API request to examine data structure.
"""

import httpx
import json
import sys
from typing import Dict, Any

# API Configuration
API_KEY = "8710e2cdb1msh72b30bdecb99b5bp1fb537jsn33825799b519"
API_HOST = "tiktok-scraper7.p.rapidapi.com"
BASE_URL = f"https://{API_HOST}"

HEADERS = {
    'x-rapidapi-key': API_KEY,
    'x-rapidapi-host': API_HOST
}

# Known working user ID
TEST_USER_ID = "7128593328456041478"


def inspect_value(value: Any, indent: int = 0) -> str:
    """Safely inspect a value"""
    prefix = "  " * indent
    
    if isinstance(value, dict):
        return f"{prefix}{{...}} ({len(value)} fields)"
    elif isinstance(value, list):
        if len(value) == 0:
            return f"{prefix}[] (empty)"
        return f"{prefix}[...] ({len(value)} items)"
    elif isinstance(value, str):
        if len(value) > 50:
            return f'{prefix}"{value[:50]}..."'
        return f'{prefix}"{value}"'
    elif isinstance(value, int):
        return f"{prefix}{value:,}"
    elif isinstance(value, bool):
        return f"{prefix}{value}"
    else:
        return f"{prefix}{value}"


def check_required_fields(video: Dict) -> Dict[str, bool]:
    """Check if video has all fields needed for Viral Waves"""
    
    checks = {
        # Core identification
        "video_id": "video_id" in video or "id" in video or "aweme_id" in video,
        "create_time": "create_time" in video,
        "desc": "desc" in video or "title" in video,
        
        # Statistics (for growth detection)
        "stats": "stats" in video,
        "play_count": False,  # Will check inside stats
        "digg_count": False,
        "share_count": False,
        "comment_count": False,
        
        # Author (for clustering)
        "author": "author" in video,
        "author_unique_id": False,
        
        # Content (for niche clustering)
        "hashtags": "hashtags" in video or "challenges" in video,
        "music": "music" in video or "sound" in video,
    }
    
    # Check inside stats
    if "stats" in video:
        stats = video["stats"]
        checks["play_count"] = "play_count" in stats or "view_count" in stats
        checks["digg_count"] = "digg_count" in stats or "like_count" in stats
        checks["share_count"] = "share_count" in stats
        checks["comment_count"] = "comment_count" in stats
    
    # Check author fields
    if "author" in video:
        author = video["author"]
        checks["author_unique_id"] = "unique_id" in author or "id" in author
    
    return checks


def main():
    print("=" * 70)
    print("TIKTOK-SCRAPER7 API - DATA STRUCTURE INSPECTION")
    print("=" * 70)
    print(f"\nAPI: {API_HOST}")
    print(f"Endpoint: /user/story")
    print(f"User ID: {TEST_USER_ID}")
    print("\n⚠️  This will use 1 API request (check your monthly limit!)")
    print("=" * 70)
    
    input("\nPress Enter to continue (Ctrl+C to cancel)...")
    
    print("\n🌐 Fetching data...")
    
    try:
        url = f"{BASE_URL}/user/story"
        params = {'user_id': TEST_USER_ID}
        
        response = httpx.get(url, headers=HEADERS, params=params, timeout=10)
        
        print(f"✅ Response: {response.status_code}")
        print(f"   Size: {len(response.text)} bytes")
        
        data = response.json()
        
        if data.get('code') != 0:
            print(f"\n❌ API Error: {data.get('msg')}")
            return 1
        
        videos = data.get('data', {}).get('videos', [])
        
        print(f"\n📊 Found {len(videos)} videos")
        
        if not videos:
            print("❌ No videos to analyze")
            return 1
        
        # Inspect first video
        video = videos[0]
        
        print("\n" + "=" * 70)
        print("VIDEO STRUCTURE")
        print("=" * 70)
        
        for key, value in sorted(video.items()):
            print(f"\n{key}:")
            if isinstance(value, dict):
                for subkey in sorted(value.keys()):
                    subval = value[subkey]
                    print(f"  {subkey}: {inspect_value(subval, 1).strip()}")
            elif isinstance(value, list) and len(value) > 0:
                print(f"  [{len(value)} items]")
                if isinstance(value[0], dict):
                    print(f"  First item has: {list(value[0].keys())[:5]}...")
            else:
                print(f"  {inspect_value(value, 1).strip()}")
        
        # Check requirements
        print("\n" + "=" * 70)
        print("VIRAL WAVES REQUIREMENTS CHECK")
        print("=" * 70)
        
        checks = check_required_fields(video)
        
        print("\n✅ Required for Growth Detection:")
        print(f"   video_id: {'✅' if checks['video_id'] else '❌'}")
        print(f"   create_time: {'✅' if checks['create_time'] else '❌'}")
        print(f"   stats: {'✅' if checks['stats'] else '❌'}")
        print(f"     └─ play_count: {'✅' if checks['play_count'] else '❌'}")
        print(f"     └─ digg_count: {'✅' if checks['digg_count'] else '❌'}")
        print(f"     └─ share_count: {'✅' if checks['share_count'] else '❌'}")
        print(f"     └─ comment_count: {'✅' if checks['comment_count'] else '❌'}")
        
        print("\n✅ Required for Niche Clustering:")
        print(f"   author: {'✅' if checks['author'] else '❌'}")
        print(f"     └─ unique_id: {'✅' if checks['author_unique_id'] else '❌'}")
        print(f"   hashtags: {'✅' if checks['hashtags'] else '❌'}")
        print(f"   music/sound: {'✅' if checks['music'] else '❌'}")
        print(f"   desc: {'✅' if checks['desc'] else '❌'}")
        
        # Summary
        all_required = all([
            checks['video_id'],
            checks['create_time'],
            checks['stats'],
            checks['author']
        ])
        
        print("\n" + "=" * 70)
        if all_required:
            print("✅✅✅ API HAS ALL REQUIRED DATA FOR VIRAL WAVES!")
        else:
            print("⚠️  API MISSING SOME REQUIRED FIELDS")
            print("   Check details above to see what's missing")
        print("=" * 70)
        
        # Sample data
        print("\n📋 Sample Data:")
        if 'video_id' in video:
            print(f"   Video ID: {video['video_id']}")
        if 'create_time' in video:
            print(f"   Created: {video['create_time']}")
        if 'stats' in video:
            stats = video['stats']
            print(f"   Views: {stats.get('play_count', 'N/A'):,}" if isinstance(stats.get('play_count'), int) else f"   Views: {stats.get('play_count', 'N/A')}")
            print(f"   Likes: {stats.get('digg_count', 'N/A'):,}" if isinstance(stats.get('digg_count'), int) else f"   Likes: {stats.get('digg_count', 'N/A')}")
        
        return 0
        
    except KeyboardInterrupt:
        print("\n\n⚠️  Cancelled by user")
        return 1
    except Exception as e:
        print(f"\n❌ Error: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
