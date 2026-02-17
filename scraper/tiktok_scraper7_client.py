"""
TikTok-Scraper7 API Client for Viral Waves

Production-ready client for RapidAPI's TikTok-Scraper7 API.
Provides all endpoints needed for trend detection and analysis.

API Documentation: https://rapidapi.com/tiktok-scraper7
Cost: $59/month (Pro tier)
"""

import httpx
import os
import asyncio
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


@dataclass
class Video:
    """TikTok video data model"""
    video_id: str
    aweme_id: str
    create_time: int
    duration: int
    play_count: int
    digg_count: int
    share_count: int
    comment_count: int
    collect_count: int
    author_id: str
    author_unique_id: str
    author_nickname: str
    music_id: str
    music_title: str
    music_author: str
    desc: str
    region: str
    cover_url: str
    video_url: str
    is_ad: bool
    
    @property
    def created_at(self) -> datetime:
        """Convert Unix timestamp to datetime"""
        return datetime.fromtimestamp(self.create_time)
    
    @property
    def engagement_rate(self) -> float:
        """Calculate engagement rate (likes + shares + comments) / views"""
        if self.play_count == 0:
            return 0.0
        return (self.digg_count + self.share_count + self.comment_count) / self.play_count


@dataclass
class Challenge:
    """TikTok hashtag/challenge data model"""
    challenge_id: str
    name: str
    description: str
    video_count: int
    view_count: int
    

@dataclass
class User:
    """TikTok user data model"""
    user_id: str
    unique_id: str
    nickname: str
    avatar_url: str
    follower_count: Optional[int] = None
    following_count: Optional[int] = None
    heart_count: Optional[int] = None
    video_count: Optional[int] = None


class TikTokScraper7Client:
    """
    Client for TikTok-Scraper7 API (RapidAPI)
    
    Provides methods to fetch TikTok data for trend detection:
    - Trending videos
    - Hashtag videos
    - User videos
    - Search functionality
    """
    
    BASE_URL = "https://tiktok-scraper7.p.rapidapi.com"
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize client
        
        Args:
            api_key: RapidAPI key (defaults to RAPIDAPI_KEY env var)
        """
        self.api_key = api_key or os.getenv("RAPIDAPI_KEY")
        if not self.api_key:
            raise ValueError("API key required. Set RAPIDAPI_KEY env var or pass to constructor.")
        
        self.headers = {
            'x-rapidapi-key': self.api_key,
            'x-rapidapi-host': 'tiktok-scraper7.p.rapidapi.com'
        }
        
        self._client: Optional[httpx.AsyncClient] = None
        
    async def __aenter__(self):
        """Async context manager entry"""
        self._client = httpx.AsyncClient(headers=self.headers, timeout=30.0)
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        if self._client:
            await self._client.aclose()
            self._client = None
    
    async def _request(self, endpoint: str, params: Dict[str, Any]) -> Dict:
        """
        Make API request with error handling
        
        Args:
            endpoint: API endpoint path
            params: Query parameters
            
        Returns:
            JSON response data
            
        Raises:
            httpx.HTTPError: On HTTP errors
            ValueError: On API errors
        """
        if not self._client:
            self._client = httpx.AsyncClient(headers=self.headers, timeout=30.0)
        
        url = f"{self.BASE_URL}{endpoint}"
        
        try:
            response = await self._client.get(url, params=params)
            response.raise_for_status()
            
            data = response.json()
            
            # Check API error code
            if data.get('code') != 0:
                error_msg = data.get('msg', 'Unknown API error')
                logger.warning(f"API error: {error_msg}")
                raise ValueError(f"API error: {error_msg}")
            
            return data
            
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error {e.response.status_code}: {e.response.text[:200]}")
            raise
        except httpx.RequestError as e:
            logger.error(f"Request error: {e}")
            raise
    
    def _parse_video(self, video_data: Dict) -> Video:
        """Parse video data from API response"""
        author = video_data.get('author', {})
        music = video_data.get('music_info', {})
        
        return Video(
            video_id=video_data.get('video_id', ''),
            aweme_id=video_data.get('aweme_id', ''),
            create_time=video_data.get('create_time', 0),
            duration=video_data.get('duration', 0),
            play_count=video_data.get('play_count', 0),
            digg_count=video_data.get('digg_count', 0),
            share_count=video_data.get('share_count', 0),
            comment_count=video_data.get('comment_count', 0),
            collect_count=video_data.get('collect_count', 0),
            author_id=author.get('id', ''),
            author_unique_id=author.get('unique_id', ''),
            author_nickname=author.get('nickname', ''),
            music_id=music.get('id', ''),
            music_title=music.get('title', ''),
            music_author=music.get('author', ''),
            desc=video_data.get('desc', '') or video_data.get('title', ''),
            region=video_data.get('region', ''),
            cover_url=video_data.get('cover', ''),
            video_url=video_data.get('play', ''),
            is_ad=bool(video_data.get('is_ad', 0))
        )
    
    async def get_trending(self, region: str = "us", count: int = 20) -> List[Video]:
        """
        Get trending videos
        
        Args:
            region: Region code (e.g., "us", "eu", "asia")
            count: Number of videos to fetch
            
        Returns:
            List of Video objects
        """
        data = await self._request("/feed/list", {
            "region": region,
            "count": count
        })
        
        videos_data = data.get('data', {}).get('videos', [])
        return [self._parse_video(v) for v in videos_data]
    
    async def search_hashtags(self, keyword: str, count: int = 10) -> List[Challenge]:
        """
        Search for hashtags/challenges
        
        Args:
            keyword: Search term
            count: Number of results
            
        Returns:
            List of Challenge objects
        """
        data = await self._request("/challenge/search", {
            "keywords": keyword,
            "count": count,
            "cursor": 0
        })
        
        challenges_data = data.get('data', {}).get('challenges', [])
        challenges = []
        
        for ch in challenges_data:
            challenges.append(Challenge(
                challenge_id=ch.get('cid', ''),
                name=ch.get('cha_name', ''),
                description=ch.get('desc', ''),
                video_count=ch.get('user_count', 0),
                view_count=ch.get('view_count', 0)
            ))
        
        return challenges
    
    async def get_hashtag_videos(self, challenge_id: str, count: int = 20) -> List[Video]:
        """
        Get videos for a specific hashtag
        
        Args:
            challenge_id: Hashtag ID from search_hashtags
            count: Number of videos to fetch
            
        Returns:
            List of Video objects
        """
        data = await self._request("/challenge/posts", {
            "challenge_id": challenge_id,
            "count": count
        })
        
        videos_data = data.get('data', {}).get('videos', [])
        return [self._parse_video(v) for v in videos_data]
    
    async def get_user_videos(self, user_id: str, count: int = 20) -> List[Video]:
        """
        Get videos for a specific user
        
        Args:
            user_id: TikTok user ID
            count: Number of videos to fetch
            
        Returns:
            List of Video objects
        """
        data = await self._request("/user/story", {
            "user_id": user_id,
            "count": count
        })
        
        videos_data = data.get('data', {}).get('videos', [])
        return [self._parse_video(v) for v in videos_data]
    
    async def search_users(self, keyword: str, count: int = 10) -> List[User]:
        """
        Search for users
        
        Args:
            keyword: Search term
            count: Number of results
            
        Returns:
            List of User objects
        """
        data = await self._request("/user/search", {
            "keywords": keyword,
            "count": count,
            "cursor": 0
        })
        
        users_data = data.get('data', {}).get('users', [])
        users = []
        
        for u in users_data:
            users.append(User(
                user_id=u.get('uid', ''),
                unique_id=u.get('unique_id', ''),
                nickname=u.get('nickname', ''),
                avatar_url=u.get('avatar', ''),
                follower_count=u.get('follower_count'),
                following_count=u.get('following_count'),
                heart_count=u.get('heart_count'),
                video_count=u.get('video_count')
            ))
        
        return users
    
    async def search_videos(self, keyword: str, count: int = 10) -> List[Video]:
        """
        Search for videos by keyword
        
        Args:
            keyword: Search term
            count: Number of results
            
        Returns:
            List of Video objects
        """
        data = await self._request("/photo/search", {
            "keywords": keyword,
            "count": count
        })
        
        videos_data = data.get('data', {}).get('videos', [])
        return [self._parse_video(v) for v in videos_data]


# Convenience functions for simple usage
async def get_trending_videos(region: str = "us", count: int = 20) -> List[Video]:
    """Quick fetch trending videos"""
    async with TikTokScraper7Client() as client:
        return await client.get_trending(region, count)


async def get_hashtag_videos_by_name(hashtag: str, count: int = 20) -> List[Video]:
    """Quick fetch videos by hashtag name"""
    async with TikTokScraper7Client() as client:
        challenges = await client.search_hashtags(hashtag, count=1)
        if not challenges:
            return []
        return await client.get_hashtag_videos(challenges[0].challenge_id, count)


async def get_user_videos_by_username(username: str, count: int = 20) -> List[Video]:
    """Quick fetch user videos by username"""
    async with TikTokScraper7Client() as client:
        users = await client.search_users(username, count=1)
        if not users:
            return []
        return await client.get_user_videos(users[0].user_id, count)
