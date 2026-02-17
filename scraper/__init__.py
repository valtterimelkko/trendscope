"""
Trendscope Scraper Service

Self-hosted TikTok data collection using TikTok-Api with IPRoyal proxies.
Implements producer-consumer pattern with Redis queue for video metadata.

Rate Limits (per SELF_HOSTED.md):
- Trending: 10-20 req/min
- Hashtag: 5-10 req/min
- User: 2-5 req/min

Architecture:
- Producer: TikTok-Api (Playwright) -> Redis Queue
- Consumer: Redis Queue -> Trend Detection (Stage 04)
- Hot Cache: 72-hour TTL on all video data
"""

__version__ = "1.0.0"
__author__ = "Trendscope Team"

from .config import settings
from .models import VideoData, VideoStats, VideoAuthor, VideoMusic, ScraperHealth
from .rate_limiter import RateLimiter, RATE_LIMITS
from .circuit_breaker import CircuitBreaker, CircuitState, CircuitOpenError
from .producer import TikTokProducer
from .health import HealthChecker

__all__ = [
    "settings",
    "VideoData",
    "VideoStats",
    "VideoAuthor",
    "VideoMusic",
    "ScraperHealth",
    "RateLimiter",
    "RATE_LIMITS",
    "CircuitBreaker",
    "CircuitState",
    "CircuitOpenError",
    "TikTokProducer",
    "HealthChecker",
]
