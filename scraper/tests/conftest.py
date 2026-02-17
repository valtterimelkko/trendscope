"""
Scraper module test fixtures and configuration.

Provides fixtures for:
- Mocked Redis client
- Rate limiter testing
- Circuit breaker testing
- Sample video data
- Temporary directories
"""

import asyncio
import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import AsyncGenerator, Dict, List, Optional
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
import pytest_asyncio


# =============================================================================
# Event Loop Fixture
# =============================================================================

@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


# =============================================================================
# Mock Redis Fixtures
# =============================================================================

class FakeRedis:
    """In-memory Redis mock for testing."""
    
    def __init__(self):
        self._data: Dict[str, any] = {}
        self._expiry: Dict[str, datetime] = {}
    
    async def ping(self) -> bool:
        return True
    
    async def get(self, key: str) -> Optional[bytes]:
        self._cleanup_expired()
        value = self._data.get(key)
        return value.encode() if isinstance(value, str) else value
    
    async def set(self, key: str, value: str, ex: Optional[int] = None) -> bool:
        self._data[key] = value
        if ex:
            self._expiry[key] = datetime.now(timezone.utc).timestamp() + ex
        return True
    
    async def delete(self, key: str) -> int:
        if key in self._data:
            del self._data[key]
            self._expiry.pop(key, None)
            return 1
        return 0
    
    async def lpush(self, key: str, value: str) -> int:
        if key not in self._data:
            self._data[key] = []
        if not isinstance(self._data[key], list):
            self._data[key] = []
        self._data[key].insert(0, value)
        return len(self._data[key])
    
    async def rpop(self, key: str) -> Optional[bytes]:
        self._cleanup_expired()
        if key in self._data and isinstance(self._data[key], list):
            if self._data[key]:
                value = self._data[key].pop()
                return value.encode() if isinstance(value, str) else value
        return None
    
    async def llen(self, key: str) -> int:
        if key in self._data and isinstance(self._data[key], list):
            return len(self._data[key])
        return 0
    
    async def exists(self, key: str) -> int:
        self._cleanup_expired()
        return 1 if key in self._data else 0
    
    async def keys(self, pattern: str) -> List[bytes]:
        """Simple pattern matching (supports * wildcard only)."""
        self._cleanup_expired()
        import fnmatch
        matching = [k.encode() for k in self._data.keys() if fnmatch.fnmatch(k, pattern)]
        return matching
    
    async def lrange(self, key: str, start: int, end: int) -> List[bytes]:
        if key in self._data and isinstance(self._data[key], list):
            items = self._data[key][start:end+1 if end >= 0 else None]
            return [item.encode() if isinstance(item, str) else item for item in items]
        return []
    
    async def expire(self, key: str, seconds: int) -> bool:
        if key in self._data:
            self._expiry[key] = datetime.now(timezone.utc).timestamp() + seconds
            return True
        return False
    
    async def ttl(self, key: str) -> int:
        if key in self._expiry:
            remaining = int(self._expiry[key] - datetime.now(timezone.utc).timestamp())
            return max(remaining, 0)
        return -1
    
    def _cleanup_expired(self):
        now = datetime.now(timezone.utc).timestamp()
        expired = [k for k, exp in self._expiry.items() if exp <= now]
        for k in expired:
            self._data.pop(k, None)
            self._expiry.pop(k, None)
    
    async def close(self):
        pass


@pytest_asyncio.fixture
async def mock_redis() -> AsyncGenerator[FakeRedis, None]:
    """Provide a fresh FakeRedis instance for each test."""
    redis = FakeRedis()
    yield redis
    await redis.close()


@pytest_asyncio.fixture
async def mock_redis_with_data(mock_redis: FakeRedis) -> AsyncGenerator[FakeRedis, None]:
    """Provide a FakeRedis instance pre-populated with sample data."""
    # Add sample video data to queue
    for i in range(5):
        video_data = {
            "id": f"video_{i}",
            "url": f"https://tiktok.com/@user/video/{i}",
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        await mock_redis.lpush("video:queue", json.dumps(video_data))
    yield mock_redis


# =============================================================================
# Rate Limiter Fixtures
# =============================================================================

@pytest.fixture
def rate_limit_config() -> Dict:
    """Default rate limiter configuration for testing."""
    return {
        "requests_per_second": 10.0,
        "burst_size": 5,
        "max_wait_seconds": 5.0
    }


@pytest_asyncio.fixture
async def rate_limiter(rate_limit_config: Dict) -> AsyncGenerator:
    """Create a rate limiter instance for testing."""
    # Import here to avoid issues if module doesn't exist yet
    try:
        from scraper.rate_limiter import RateLimiter
        limiter = RateLimiter(**rate_limit_config)
        yield limiter
    except ImportError:
        # Return a mock if module doesn't exist yet
        mock = AsyncMock()
        mock.acquire = AsyncMock(return_value=None)
        mock.release = AsyncMock(return_value=None)
        yield mock


# =============================================================================
# Circuit Breaker Fixtures
# =============================================================================

@pytest.fixture
def circuit_breaker_config() -> Dict:
    """Default circuit breaker configuration for testing."""
    return {
        "failure_threshold": 5,
        "recovery_timeout": 30.0,
        "half_open_max_calls": 3
    }


@pytest_asyncio.fixture
async def circuit_breaker(circuit_breaker_config: Dict) -> AsyncGenerator:
    """Create a circuit breaker instance for testing."""
    try:
        from scraper.circuit_breaker import CircuitBreaker
        cb = CircuitBreaker(**circuit_breaker_config)
        yield cb
    except ImportError:
        # Return a mock if module doesn't exist yet
        mock = MagicMock()
        mock.state = "CLOSED"
        mock.call = lambda f: f
        mock.record_success = MagicMock()
        mock.record_failure = MagicMock()
        yield mock


@pytest.fixture
def circuit_states() -> Dict[str, str]:
    """Circuit breaker state constants."""
    return {
        "CLOSED": "CLOSED",
        "OPEN": "OPEN", 
        "HALF_OPEN": "HALF_OPEN"
    }


# =============================================================================
# Sample Data Fixtures
# =============================================================================

@pytest.fixture
def sample_video_data() -> Dict:
    """Create a single sample video data record."""
    return {
        "id": "1234567890",
        "url": "https://www.tiktok.com/@testuser/video/1234567890",
        "author": {
            "id": "user123",
            "username": "testuser",
            "display_name": "Test User"
        },
        "stats": {
            "views": 100000,
            "likes": 15000,
            "shares": 2500,
            "comments": 800,
            "saves": 1200
        },
        "content": {
            "description": "Testing the trend detection #viral #trending",
            "hashtags": ["viral", "trending", "test"],
            "music": {
                "id": "music456",
                "title": "Test Sound",
                "author": "Music Artist"
            }
        },
        "timestamp": datetime.now(timezone.utc).isoformat()
    }


@pytest.fixture
def sample_video_batch() -> List[Dict]:
    """Create a batch of sample video data with varying stats."""
    videos = []
    growth_patterns = [
        # Viral video - high engagement
        {"views": 5000000, "likes": 800000, "shares": 150000, "comments": 50000},
        # Trending video - good growth
        {"views": 500000, "likes": 75000, "shares": 12000, "comments": 3500},
        # Steady video - moderate engagement
        {"views": 50000, "likes": 8000, "shares": 1500, "comments": 400},
        # Flat video - low engagement
        {"views": 5000, "likes": 500, "shares": 50, "comments": 20},
        # New video - minimal stats
        {"views": 500, "likes": 50, "shares": 5, "comments": 2},
    ]
    
    for i, stats in enumerate(growth_patterns):
        video = {
            "id": f"video_{i}_{datetime.now(timezone.utc).timestamp()}",
            "url": f"https://tiktok.com/@user{i}/video/{i}",
            "author": {
                "id": f"user{i}",
                "username": f"testuser{i}",
                "display_name": f"Test User {i}"
            },
            "stats": stats,
            "content": {
                "description": f"Test video {i} content #viral",
                "hashtags": ["viral", f"tag{i}"],
                "music": {
                    "id": f"music{i}",
                    "title": f"Sound {i}",
                    "author": f"Artist {i}"
                }
            },
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        videos.append(video)
    
    return videos


@pytest.fixture
def mock_tiktok_response() -> Dict:
    """Mock TikTok API response."""
    return {
        "status": "success",
        "data": {
            "videos": [
                {
                    "id": "mock_video_1",
                    "desc": "Mock video description",
                    "createTime": str(int(datetime.now(timezone.utc).timestamp())),
                    "author": {
                        "uid": "mock_user_1",
                        "nickname": "MockUser",
                        "uniqueId": "mockuser123"
                    },
                    "stats": {
                        "diggCount": 10000,
                        "shareCount": 1500,
                        "commentCount": 500,
                        "playCount": 100000
                    }
                }
            ]
        }
    }


# =============================================================================
# Environment & Configuration Fixtures
# =============================================================================

@pytest.fixture
def temp_data_dir(tmp_path: Path) -> Path:
    """Provide a temporary directory for test data."""
    data_dir = tmp_path / "data"
    data_dir.mkdir()
    return data_dir


@pytest.fixture
def mock_env_vars(monkeypatch) -> Dict[str, str]:
    """Set up mock environment variables for testing."""
    env_vars = {
        "REDIS_URL": "redis://localhost:6379/0",
        "REDIS_QUEUE_KEY": "test:video:queue",
        "TIKTOK_RATE_LIMIT": "10",
        "IPROYAL_USERNAME": "test_user",
        "IPROYAL_PASSWORD": "test_pass",
        "IPROYAL_HOST": "proxy.iproyal.com",
        "IPROYAL_PORT": "7777",
        "LOG_LEVEL": "DEBUG"
    }
    
    for key, value in env_vars.items():
        monkeypatch.setenv(key, value)
    
    return env_vars


@pytest.fixture
def proxy_config() -> Dict:
    """IPRoyal proxy configuration for testing."""
    return {
        "host": "proxy.iproyal.com",
        "port": 7777,
        "username": os.getenv("IPROYAL_USERNAME", "test_user"),
        "password": os.getenv("IPROYAL_PASSWORD", "test_pass"),
        "session_time": 1800  # 30 minutes in seconds
    }


# =============================================================================
# Health Check Fixtures
# =============================================================================

@pytest.fixture
def health_check_response() -> Dict:
    """Sample health check response."""
    return {
        "status": "healthy",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "version": "1.0.0",
        "components": {
            "redis": {"status": "up", "latency_ms": 5},
            "tiktok_api": {"status": "up", "latency_ms": 250},
            "rate_limiter": {"status": "up", "current_tokens": 10}
        }
    }


# =============================================================================
# Async HTTP Client Fixtures
# =============================================================================

@pytest_asyncio.fixture
async def mock_http_client() -> AsyncGenerator[AsyncMock, None]:
    """Provide a mocked async HTTP client."""
    client = AsyncMock()
    client.get = AsyncMock()
    client.post = AsyncMock()
    client.close = AsyncMock()
    yield client


# =============================================================================
# Producer/Consumer Fixtures
# =============================================================================

@pytest.fixture
def producer_config() -> Dict:
    """Scraper producer configuration."""
    return {
        "batch_size": 10,
        "fetch_interval_seconds": 60,
        "max_retries": 3,
        "queue_key": "video:queue"
    }


@pytest.fixture
def consumer_config() -> Dict:
    """Scraper consumer configuration."""
    return {
        "poll_interval_seconds": 5,
        "batch_size": 5,
        "max_processing_time": 30
    }


# =============================================================================
# Cleanup Fixtures
# =============================================================================

@pytest.fixture(autouse=True)
def cleanup_temp_files(tmp_path: Path):
    """Automatically clean up temporary files after each test."""
    yield
    # Cleanup is handled by pytest's tmp_path fixture
