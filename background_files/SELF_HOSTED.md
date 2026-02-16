# Self-Hosted TikTok Scraping - Implementation Guide

## Executive Summary

This guide provides a complete technical reference for implementing a self-hosted TikTok scraping infrastructure using **TikTok-Api** by David Teather. This is the recommended approach for Viral Waves due to its **~10-50x cost advantage** over managed APIs.

**Target Cost:** $7-45/month (with existing VPS + IPRoyal proxies)

---

## Table of Contents

1. [Overview](#1-overview)
2. [Prerequisites](#2-prerequisites)
3. [Installation](#3-installation)
4. [Core Functionality](#4-core-functionality)
5. [Architecture Patterns](#5-architecture-patterns)
6. [Proxy Configuration](#6-proxy-configuration)
7. [Rate Limiting & Best Practices](#7-rate-limiting--best-practices)
8. [Error Handling & Resilience](#8-error-handling--resilience)
9. [Production Deployment](#9-production-deployment)
10. [Troubleshooting](#10-troubleshooting)
11. [Cost Analysis](#11-cost-analysis)
12. [References](#12-references)

---

## 1. Overview

### What is TikTok-Api?

TikTok-Api is a Python library that provides unofficial access to TikTok's public data through browser automation (Playwright). It extracts data available on TikTok's web interface without requiring official API access.

**GitHub:** https://github.com/davidteather/TikTok-Api  
**Stars:** 6,100+  
**Maintenance:** Active (2024)  
**License:** MIT

### Data Available

| Endpoint | Data Returned |
|----------|---------------|
| `trending.videos()` | Trending videos with metadata |
| `hashtag(name).videos()` | Videos by hashtag |
| `user(username).videos()` | Videos by user |
| `search(query)` | Search results |
| `video(id)` | Specific video metadata |
| `sound(id).videos()` | Videos using specific sound |

### Metadata Extracted

```python
{
    "id": "1234567890",
    "desc": "Video caption",
    "createTime": 1700000000,
    "stats": {
        "diggCount": 15000,      # Likes
        "shareCount": 500,
        "commentCount": 200,
        "playCount": 100000      # Views
    },
    "author": {
        "uniqueId": "username",
        "nickname": "Display Name",
        "followerCount": 50000
    },
    "music": {
        "id": "sound123",
        "title": "Original Sound",
        "authorName": "Creator"
    },
    "hashtags": [
        {"name": "viral"},
        {"name": "trending"}
    ]
}
```

---

## 2. Prerequisites

### System Requirements

| Component | Minimum | Recommended |
|-----------|---------|-------------|
| **Python** | 3.9 | 3.11+ |
| **RAM** | 2GB | 4GB+ |
| **Disk** | 10GB | 20GB+ |
| **CPU** | 2 cores | 4 cores+ |
| **Network** | 10Mbps | 100Mbps+ |

### Software Dependencies

```bash
# System packages (Ubuntu/Debian)
sudo apt-get update
sudo apt-get install -y python3-pip python3-venv git

# For Playwright browsers
sudo apt-get install -y libnss3 libatk-bridge2.0 libxss1 libgtk-3-0
```

### Proxy Requirements

**Required:** Rotating residential proxies

> **✅ Credentials Configured:** IPRoyal credentials are pre-configured in `.env` file at project root.

| Provider | Price | Recommendation |
|----------|-------|----------------|
| **IPRoyal** | $7/GB | ✅ **CONFIGURED** - Credentials in `.env` |
| **Webshare** | $3.50-15/month | Alternative if needed |
| **Bright Data** | Pay-as-you-go | Most reliable, higher cost |
| **Oxylabs** | $99/month | Enterprise option |

---

## 3. Installation

### Step 1: Create Virtual Environment

```bash
# Create project directory
mkdir -p ~/viral-waves/scraper
cd ~/viral-waves/scraper

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Upgrade pip
pip install --upgrade pip
```

### Step 2: Install Dependencies

```bash
# Create requirements.txt
cat > requirements.txt << 'EOF'
TikTok-Api>=6.2.0
playwright>=1.40.0
redis>=5.0.0
psycopg2-binary>=2.9.9
asyncio-mqtt>=0.16.0
python-dotenv>=1.0.0
httpx>=0.25.0
pydantic>=2.5.0
tenacity>=8.2.0
structlog>=23.2.0
prometheus-client>=0.19.0
EOF

# Install Python packages
pip install -r requirements.txt

# Install Playwright browsers
playwright install chromium
```

### Step 3: Verify Installation

```python
# test_installation.py
import asyncio
from TikTokApi import TikTokApi

async def test():
    async with TikTokApi() as api:
        print("✓ TikTok-Api installed successfully")
        print(f"Version: {api.__version__ if hasattr(api, '__version__') else 'unknown'}")

asyncio.run(test())
```

Run: `python test_installation.py`

---

## 4. Core Functionality

### 4.1 Basic Scraping

```python
# basic_scraper.py
import asyncio
from TikTokApi import TikTokApi
from typing import List, Dict, Any
import json

async def get_trending_videos(count: int = 10) -> List[Dict[Any, Any]]:
    """
    Fetch trending videos from TikTok.
    
    Args:
        count: Number of videos to fetch
        
    Returns:
        List of video metadata dictionaries
    """
    videos = []
    
    async with TikTokApi() as api:
        async for video in api.trending.videos(count=count):
            video_data = {
                "id": video.id,
                "desc": video.desc,
                "createTime": video.create_time,
                "stats": {
                    "diggCount": video.stats.digg_count,
                    "shareCount": video.stats.share_count,
                    "commentCount": video.stats.comment_count,
                    "playCount": video.stats.play_count,
                },
                "author": {
                    "uniqueId": video.author.unique_id,
                    "nickname": video.author.nickname,
                    "followerCount": video.author.stats.follower_count,
                },
                "music": {
                    "id": video.sound.id if video.sound else None,
                    "title": video.sound.title if video.sound else None,
                },
                "hashtags": [tag.name for tag in video.hashtags],
            }
            videos.append(video_data)
            
    return videos

# Run
if __name__ == "__main__":
    videos = asyncio.run(get_trending_videos(count=10))
    print(json.dumps(videos, indent=2))
```

### 4.2 Hashtag Scraping

```python
# hashtag_scraper.py
import asyncio
from TikTokApi import TikTokApi
from typing import List, Dict, Any

async def get_hashtag_videos(hashtag: str, count: int = 100) -> List[Dict[Any, Any]]:
    """
    Fetch videos for a specific hashtag.
    
    Args:
        hashtag: Hashtag name (without #)
        count: Number of videos to fetch
        
    Returns:
        List of video metadata
    """
    videos = []
    
    async with TikTokApi() as api:
        tag = api.hashtag(name=hashtag)
        async for video in tag.videos(count=count):
            videos.append({
                "id": video.id,
                "desc": video.desc,
                "createTime": video.create_time,
                "stats": {
                    "playCount": video.stats.play_count,
                    "diggCount": video.stats.digg_count,
                },
                "hashtags": [t.name for t in video.hashtags],
            })
            
    return videos

# Usage
# videos = asyncio.run(get_hashtag_videos("viral", count=50))
```

### 4.3 User Profile Scraping

```python
# user_scraper.py
import asyncio
from TikTokApi import TikTokApi
from typing import Dict, Any, List

async def get_user_videos(username: str, count: int = 50) -> Dict[str, Any]:
    """
    Fetch user profile and their videos.
    
    Args:
        username: TikTok username (without @)
        count: Number of videos to fetch
        
    Returns:
        Dictionary with profile info and videos
    """
    async with TikTokApi() as api:
        user = api.user(username=username)
        
        # Get user info
        user_info = await user.info()
        
        # Get videos
        videos = []
        async for video in user.videos(count=count):
            videos.append({
                "id": video.id,
                "desc": video.desc,
                "createTime": video.create_time,
                "stats": {
                    "playCount": video.stats.play_count,
                    "diggCount": video.stats.digg_count,
                },
            })
        
        return {
            "user": {
                "uniqueId": user_info.user.unique_id,
                "nickname": user_info.user.nickname,
                "followerCount": user_info.stats.follower_count,
                "followingCount": user_info.stats.following_count,
                "heartCount": user_info.stats.heart_count,
                "videoCount": user_info.stats.video_count,
            },
            "videos": videos,
        }

# Usage
# data = asyncio.run(get_user_videos("charlidamelio", count=30))
```

### 4.4 Sound/Music Scraping

```python
# sound_scraper.py
import asyncio
from TikTokApi import TikTokApi
from typing import List, Dict, Any

async def get_sound_videos(sound_id: str, count: int = 100) -> List[Dict[Any, Any]]:
    """
    Fetch videos that use a specific sound.
    
    Args:
        sound_id: TikTok sound/music ID
        count: Number of videos to fetch
        
    Returns:
        List of video metadata
    """
    videos = []
    
    async with TikTokApi() as api:
        sound = api.sound(id=sound_id)
        async for video in sound.videos(count=count):
            videos.append({
                "id": video.id,
                "desc": video.desc,
                "createTime": video.create_time,
                "author": {
                    "uniqueId": video.author.unique_id,
                    "followerCount": video.author.stats.follower_count,
                },
                "stats": {
                    "playCount": video.stats.play_count,
                    "diggCount": video.stats.digg_count,
                },
            })
            
    return videos

# Usage
# videos = asyncio.run(get_sound_videos("1234567890", count=50))
```

---

## 5. Architecture Patterns

### 5.1 Basic Async Pattern

```python
# async_pattern.py
import asyncio
from TikTokApi import TikTokApi
from typing import List
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TikTokScraper:
    def __init__(self, proxy: str = None):
        self.proxy = proxy
        self.api = None
        
    async def __aenter__(self):
        self.api = TikTokApi()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.api:
            await self.api.close()
    
    async def fetch_trending(self, count: int = 100) -> List[dict]:
        """Fetch trending videos."""
        videos = []
        async for video in self.api.trending.videos(count=count):
            videos.append(self._extract_video_data(video))
        return videos
    
    async def fetch_hashtag(self, hashtag: str, count: int = 100) -> List[dict]:
        """Fetch videos by hashtag."""
        videos = []
        tag = self.api.hashtag(name=hashtag)
        async for video in tag.videos(count=count):
            videos.append(self._extract_video_data(video))
        return videos
    
    def _extract_video_data(self, video) -> dict:
        """Extract relevant fields from video object."""
        return {
            "id": video.id,
            "desc": video.desc,
            "createTime": video.create_time,
            "stats": {
                "playCount": video.stats.play_count,
                "diggCount": video.stats.digg_count,
                "shareCount": video.stats.share_count,
                "commentCount": video.stats.comment_count,
            },
            "author": {
                "uniqueId": video.author.unique_id,
                "nickname": video.author.nickname,
                "followerCount": video.author.stats.follower_count,
            },
            "music": {
                "id": video.sound.id if video.sound else None,
                "title": video.sound.title if video.sound else None,
            },
            "hashtags": [t.name for t in video.hashtags],
        }

# Usage
async def main():
    async with TikTokScraper() as scraper:
        trending = await scraper.fetch_trending(count=50)
        logger.info(f"Fetched {len(trending)} trending videos")
        
        viral = await scraper.fetch_hashtag("viral", count=30)
        logger.info(f"Fetched {len(viral)} viral hashtag videos")

if __name__ == "__main__":
    asyncio.run(main())
```

### 5.2 Producer-Consumer Pattern (with Redis)

```python
# producer_consumer.py
import asyncio
import redis.asyncio as redis
from TikTokApi import TikTokApi
import json
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class TikTokProducer:
    """Produces video data to Redis queue."""
    
    def __init__(self, redis_client: redis.Redis, proxy: str = None):
        self.redis = redis_client
        self.proxy = proxy
        
    async def produce_trending(self, count: int = 100, queue: str = "tiktok:videos"):
        """Fetch trending and push to Redis."""
        async with TikTokApi() as api:
            async for video in api.trending.videos(count=count):
                data = {
                    "id": video.id,
                    "desc": video.desc,
                    "createTime": video.create_time,
                    "stats": {
                        "playCount": video.stats.play_count,
                        "diggCount": video.stats.digg_count,
                    },
                    "hashtags": [t.name for t in video.hashtags],
                    "scrapedAt": datetime.utcnow().isoformat(),
                }
                await self.redis.lpush(queue, json.dumps(data))
                logger.info(f"Produced video {video.id} to {queue}")

class TikTokConsumer:
    """Consumes video data from Redis and processes."""
    
    def __init__(self, redis_client: redis.Redis):
        self.redis = redis_client
        
    async def consume(self, queue: str = "tiktok:videos", batch_size: int = 10):
        """Consume and process videos."""
        while True:
            # Fetch batch from Redis
            batch = await self.redis.lrange(queue, 0, batch_size - 1)
            
            if not batch:
                await asyncio.sleep(1)
                continue
            
            # Remove processed items
            await self.redis.ltrim(queue, batch_size, -1)
            
            # Process batch
            for item in batch:
                data = json.loads(item)
                await self.process_video(data)
    
    async def process_video(self, data: dict):
        """Process single video. Override in subclass."""
        logger.info(f"Processing video {data['id']}")
        # Add trend detection logic here

# Usage
async def main():
    redis_client = redis.Redis(host='localhost', port=6379, db=0)
    
    producer = TikTokProducer(redis_client)
    consumer = TikTokConsumer(redis_client)
    
    # Run both
    await asyncio.gather(
        producer.produce_trending(count=100),
        consumer.consume(),
    )

if __name__ == "__main__":
    asyncio.run(main())
```

---

## 6. Proxy Configuration

### 6.1 Basic Proxy Setup

```python
# proxy_config.py
from TikTokApi import TikTokApi
import asyncio
import os
from dotenv import load_dotenv

load_dotenv()  # Load credentials from .env file

async def scrape_with_proxy():
    """Scrape using proxy."""
    
    # Credentials loaded from .env file
    proxy = os.getenv('PROXY_URL')
    # Format: http://user:pass@geo.iproyal.com:12321
    
    async with TikTokApi() as api:
        # Note: TikTok-Api uses Playwright, proxy is set at browser level
        async for video in api.trending.videos(count=10):
            print(f"Video: {video.id}")

# For rotating proxies, create new session per request
```

### 6.2 Rotating Proxy Manager

```python
# rotating_proxy.py
import random
from typing import List
import asyncio
from TikTokApi import TikTokApi

class ProxyManager:
    """Manages rotating proxy pool."""
    
    def __init__(self, proxies: List[str]):
        self.proxies = proxies
        self.failed_proxies = set()
        
    def get_proxy(self) -> str:
        """Get random working proxy."""
        available = [p for p in self.proxies if p not in self.failed_proxies]
        if not available:
            # Reset if all failed
            self.failed_proxies.clear()
            available = self.proxies
        return random.choice(available)
    
    def mark_failed(self, proxy: str):
        """Mark proxy as failed."""
        self.failed_proxies.add(proxy)

# Example IPRoyal rotating proxy URLs
PROXY_LIST = [
    "http://user:pass@us.iproyal.com:12321",
    "http://user:pass@eu.iproyal.com:12321",
]

proxy_manager = ProxyManager(PROXY_LIST)
```

### 6.3 Webshare Proxy Format

```python
# webshare_config.py

# Webshare gives you a list like:
# username:password@p.webshare.io:80

WEBSHARE_PROXIES = [
    "http://username1:password1@p.webshare.io:80",
    "http://username2:password2@p.webshare.io:80",
    # ... up to your plan limit
]

# Rotating endpoint (recommended)
WEBSHARE_ROTATING = "http://username:password@p.webshare.io:80"
```

---

## 7. Rate Limiting & Best Practices

### 7.1 Rate Limiting Strategy

```python
# rate_limiter.py
import asyncio
import time
from typing import Optional

class RateLimiter:
    """Token bucket rate limiter."""
    
    def __init__(self, rate: float, burst: int):
        """
        Args:
            rate: Requests per second
            burst: Maximum burst size
        """
        self.rate = rate
        self.burst = burst
        self.tokens = burst
        self.last_update = time.time()
        self.lock = asyncio.Lock()
    
    async def acquire(self):
        """Acquire a token, waiting if necessary."""
        async with self.lock:
            now = time.time()
            elapsed = now - self.last_update
            self.tokens = min(self.burst, self.tokens + elapsed * self.rate)
            self.last_update = now
            
            if self.tokens < 1:
                wait_time = (1 - self.tokens) / self.rate
                await asyncio.sleep(wait_time)
                self.tokens = 0
            else:
                self.tokens -= 1

# Usage: 2 requests per second with burst of 5
rate_limiter = RateLimiter(rate=2.0, burst=5)

async def fetch_with_limit():
    await rate_limiter.acquire()
    # Make request
```

### 7.2 Recommended Rate Limits

| Source | Requests/Min | Requests/Hour | Notes |
|--------|-------------|---------------|-------|
| **Trending** | 10-20 | 500-1000 | Higher discovery value |
| **Hashtag** | 5-10 | 200-500 | Space out requests |
| **User** | 2-5 | 100-200 | Most restrictive |
| **Search** | 5-10 | 200-500 | Varies by query |

### 7.3 Session Management

```python
# session_manager.py
import asyncio
from TikTokApi import TikTokApi
from contextlib import asynccontextmanager

class SessionManager:
    """Manages TikTok sessions with rotation."""
    
    def __init__(self, max_requests: int = 100):
        self.max_requests = max_requests
        self.request_count = 0
        self._api = None
        
    @asynccontextmanager
    async def session(self):
        """Get a fresh session if needed."""
        if self._api is None or self.request_count >= self.max_requests:
            if self._api:
                await self._api.close()
            self._api = TikTokApi()
            self.request_count = 0
        
        try:
            yield self._api
            self.request_count += 1
        except Exception as e:
            # Reset on error
            await self._api.close()
            self._api = None
            raise

# Usage
session_manager = SessionManager(max_requests=50)

async def fetch():
    async with session_manager.session() as api:
        async for video in api.trending.videos(count=10):
            yield video
```

---

## 8. Error Handling & Resilience

### 8.1 Retry Logic

```python
# retry_handler.py
import asyncio
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
)

class TikTokError(Exception):
    """Base TikTok error."""
    pass

class RateLimitError(TikTokError):
    """Rate limit hit."""
    pass

class BlockedError(TikTokError):
    """IP blocked."""
    pass

@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=4, max=10),
    retry=retry_if_exception_type((RateLimitError, asyncio.TimeoutError)),
)
async def fetch_with_retry(scraper_func):
    """Fetch with retry logic."""
    try:
        return await scraper_func()
    except Exception as e:
        error_msg = str(e).lower()
        if "rate" in error_msg or "limit" in error_msg:
            raise RateLimitError(str(e))
        elif "block" in error_msg or "banned" in error_msg:
            raise BlockedError(str(e))
        raise
```

### 8.2 Circuit Breaker Pattern

```python
# circuit_breaker.py
import asyncio
import time
from enum import Enum

class CircuitState(Enum):
    CLOSED = "closed"      # Normal operation
    OPEN = "open"          # Failing, reject requests
    HALF_OPEN = "half_open"  # Testing if recovered

class CircuitBreaker:
    """Circuit breaker for TikTok API."""
    
    def __init__(self, failure_threshold: int = 5, recovery_timeout: int = 60):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.failure_count = 0
        self.last_failure_time = None
        self.state = CircuitState.CLOSED
        self.lock = asyncio.Lock()
    
    async def call(self, func, *args, **kwargs):
        """Call function with circuit breaker."""
        async with self.lock:
            if self.state == CircuitState.OPEN:
                if time.time() - self.last_failure_time > self.recovery_timeout:
                    self.state = CircuitState.HALF_OPEN
                else:
                    raise Exception("Circuit breaker is OPEN")
        
        try:
            result = await func(*args, **kwargs)
            async with self.lock:
                self.failure_count = 0
                self.state = CircuitState.CLOSED
            return result
        except Exception as e:
            async with self.lock:
                self.failure_count += 1
                self.last_failure_time = time.time()
                if self.failure_count >= self.failure_threshold:
                    self.state = CircuitState.OPEN
            raise

# Usage
circuit_breaker = CircuitBreaker(failure_threshold=3, recovery_timeout=300)

async def safe_fetch():
    return await circuit_breaker.call(fetch_trending)
```

---

## 9. Production Deployment

### 9.1 Systemd Service

```ini
# /etc/systemd/system/viral-waves-scraper.service
[Unit]
Description=Viral Waves TikTok Scraper
After=network.target redis.service postgresql.service

[Service]
Type=simple
User=viralwaves
WorkingDirectory=/home/viralwaves/scraper
Environment=PATH=/home/viralwaves/scraper/venv/bin
EnvironmentFile=/home/viralwaves/scraper/.env
ExecStart=/home/viralwaves/scraper/venv/bin/python main.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Enable: `sudo systemctl enable --now viral-waves-scraper`

### 9.2 Docker Compose

```yaml
# docker-compose.yml
version: '3.8'

services:
  scraper:
    build: .
    environment:
      - REDIS_URL=redis://redis:6379
      - DATABASE_URL=postgresql://postgres:password@db:5432/viralwaves
      - PROXY_URL=${PROXY_URL}
    depends_on:
      - redis
      - db
    restart: unless-stopped
    
  redis:
    image: redis:7-alpine
    volumes:
      - redis_data:/data
    restart: unless-stopped
    
  db:
    image: postgres:15-alpine
    environment:
      - POSTGRES_USER=postgres
      - POSTGRES_PASSWORD=password
      - POSTGRES_DB=viralwaves
    volumes:
      - postgres_data:/var/lib/postgresql/data
    restart: unless-stopped

volumes:
  redis_data:
  postgres_data:
```

### 9.3 Environment Variables

> **Pre-configured:** `.env` file exists at project root with IPRoyal proxy credentials.

```bash
# .env (already configured with IPRoyal credentials)
# Database
DATABASE_URL=postgresql://user:pass@localhost:5432/viralwaves
REDIS_URL=redis://localhost:6379/0

# Proxy (CONFIGURED - read from .env)
PROXY_URL=http://***REMOVED***:...@geo.iproyal.com:12321

# Scraping config
SCRAPE_RATE_LIMIT=10  # requests per minute
SCRAPE_BATCH_SIZE=100
SCRAPE_INTERVAL=300   # seconds between runs

# Monitoring
METRICS_PORT=9090
LOG_LEVEL=INFO
```

**Note:** The scraper should use `python-dotenv` to load credentials from `.env` file.

---

## 10. Troubleshooting

### 10.1 Common Issues

| Issue | Cause | Solution |
|-------|-------|----------|
| **Empty responses** | IP blocked | Rotate proxy, add delays |
| **Timeout errors** | Rate limited | Reduce request frequency |
| **Playwright errors** | Browser not installed | Run `playwright install` |
| **SSL errors** | Proxy issue | Verify proxy supports HTTPS |
| **Captcha/interstitial** | Bot detection | Use better proxies, add delays |

### 10.2 Debug Mode

```python
# debug_scraper.py
import logging
import asyncio
from TikTokApi import TikTokApi

# Enable debug logging
logging.basicConfig(level=logging.DEBUG)

async def debug_fetch():
    async with TikTokApi(logging_level=logging.DEBUG) as api:
        async for video in api.trending.videos(count=1):
            print(f"Video ID: {video.id}")
            print(f"Author: {video.author.unique_id}")
            print(f"Stats: {video.stats}")

asyncio.run(debug_fetch())
```

### 10.3 Health Check

```python
# health_check.py
import asyncio
import sys
from TikTokApi import TikTokApi

async def health_check():
    """Check if scraper is working."""
    try:
        async with TikTokApi() as api:
            count = 0
            async for video in api.trending.videos(count=5):
                count += 1
                print(f"✓ Video {count}: {video.id}")
            
            if count == 0:
                print("✗ No videos returned")
                sys.exit(1)
                
        print("✓ Health check passed")
        sys.exit(0)
        
    except Exception as e:
        print(f"✗ Health check failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(health_check())
```

---

## 11. Cost Analysis

### 11.1 Infrastructure Costs

| Component | Provider | Monthly Cost |
|-----------|----------|--------------|
| **VPS** | Hetzner CX11 (2 vCPU, 4GB) | €5 (~$5.50) |
| **VPS** | DigitalOcean Basic (2 vCPU, 4GB) | $24 |
| **VPS** | AWS t3.medium | ~$30 |
| **Proxy (IPRoyal)** | 5GB residential | $7.50 |
| **Proxy (Webshare)** | Rotating residential | $15 |

### 11.2 Data Usage by Volume

| Videos/Day | Data/Video | Daily Data | Monthly Data | Proxy Cost* |
|-----------|-----------|-----------|-------------|-------------|
| 1,000 | 5KB | 5MB | 150MB | ~$1-2 |
| 10,000 | 5KB | 50MB | 1.5GB | ~$7.50 |
| 50,000 | 5KB | 250MB | 7.5GB | ~$30-40 |
| 100,000 | 5KB | 500MB | 15GB | ~$60-80 |

*Using IPRoyal at $7.50/GB or Webshare unlimited plans

### 11.3 Total Cost Comparison

| Approach | Monthly Cost (10K videos/day) | Monthly Cost (50K videos/day) |
|----------|------------------------------|-------------------------------|
| **Self-hosted (your setup)** | ~$7-15 | ~$35-50 |
| JoTucker RapidAPI | $5 | $20 |
| Apify | ~$90 | ~$450 |
| Exolyt | $330 | $950 |

---

## 12. References

### Official Documentation

- **TikTok-Api GitHub:** https://github.com/davidteather/TikTok-Api
- **TikTok-Api Docs:** https://dteather.com/TikTok-Api/
- **Playwright Docs:** https://playwright.dev/python/

### Proxy Providers

- **IPRoyal:** https://iproyal.com
- **Webshare:** https://webshare.io
- **Bright Data:** https://brightdata.com

### Related Tools

- **pyktok:** https://github.com/dfreelon/pyktok (academic focus)
- **traktok (R):** https://github.com/JBGruber/traktok (R package)

---

## Quick Start Checklist

- [ ] Python 3.9+ installed
- [ ] Virtual environment created
- [ ] TikTok-Api installed (`pip install TikTok-Api`)
- [ ] Playwright browsers installed (`playwright install chromium`)
- [ ] Proxy credentials obtained
- [ ] Basic scraper tested
- [ ] Rate limiting implemented
- [ ] Error handling added
- [ ] Redis installed (for hot cache)
- [ ] PostgreSQL installed (for trend storage)
- [ ] Service configured (systemd/Docker)
- [ ] Health checks set up

---

*Document Version: 1.0*  
*Last Updated: 2026-02-16*
