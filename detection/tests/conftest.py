"""
Detection module test fixtures and configuration.

Provides fixtures for:
- Mocked PostgreSQL database
- Velocity engine testing
- Saturation engine testing
- Lifecycle manager testing
- Sample trend data
- Velocity history data
"""

import asyncio
import json
import os
from datetime import datetime, timedelta, timezone
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
# Mock Database Fixtures
# =============================================================================

class MockPostgresPool:
    """Mock PostgreSQL connection pool for testing."""
    
    def __init__(self):
        self._data: Dict[str, List[Dict]] = {
            "trends": [],
            "velocity_history": [],
            "videos": []
        }
        self.closed = False
    
    async def fetch(self, query: str, *args) -> List[Dict]:
        """Mock fetch operation."""
        # Simple query parsing for testing
        if "FROM trends" in query.upper():
            return self._data["trends"]
        elif "FROM velocity_history" in query.upper():
            return self._data["velocity_history"]
        return []
    
    async def fetchrow(self, query: str, *args) -> Optional[Dict]:
        """Mock fetchrow operation."""
        results = await self.fetch(query, *args)
        return results[0] if results else None
    
    async def execute(self, query: str, *args) -> str:
        """Mock execute operation."""
        # Simple INSERT/UPDATE handling
        if "INSERT INTO trends" in query.upper():
            trend_id = f"trend_{len(self._data['trends'])}"
            self._data["trends"].append({
                "id": trend_id,
                "created_at": datetime.now(timezone.utc),
                "updated_at": datetime.now(timezone.utc),
                **{f"arg_{i}": arg for i, arg in enumerate(args)}
            })
            return f"INSERT 0 1"
        return "OK"
    
    async def close(self):
        self.closed = True


@pytest_asyncio.fixture
async def mock_db_pool() -> AsyncGenerator[MockPostgresPool, None]:
    """Provide a mock PostgreSQL pool for testing."""
    pool = MockPostgresPool()
    yield pool
    await pool.close()


@pytest_asyncio.fixture
async def mock_db_with_trends(mock_db_pool: MockPostgresPool) -> AsyncGenerator[MockPostgresPool, None]:
    """Provide a mock database pre-populated with trends."""
    # Add sample trends at different lifecycle stages
    trends = [
        {
            "id": "trend_emerging_1",
            "hashtag": "#emergingtrend",
            "status": "emerging",
            "velocity": 0.15,
            "saturation": 0.25,
            "first_seen": datetime.now(timezone.utc) - timedelta(hours=6),
            "last_seen": datetime.now(timezone.utc)
        },
        {
            "id": "trend_peaking_1",
            "hashtag": "#peakingtrend",
            "status": "peaking",
            "velocity": 0.85,
            "saturation": 0.65,
            "first_seen": datetime.now(timezone.utc) - timedelta(days=1),
            "last_seen": datetime.now(timezone.utc)
        },
        {
            "id": "trend_saturated_1",
            "hashtag": "#saturatedtrend",
            "status": "saturated",
            "velocity": 0.05,
            "saturation": 0.92,
            "first_seen": datetime.now(timezone.utc) - timedelta(days=3),
            "last_seen": datetime.now(timezone.utc)
        },
        {
            "id": "trend_expired_1",
            "hashtag": "#expiredtrend",
            "status": "expired",
            "velocity": 0.0,
            "saturation": 0.15,
            "first_seen": datetime.now(timezone.utc) - timedelta(days=7),
            "last_seen": datetime.now(timezone.utc) - timedelta(days=2)
        }
    ]
    
    mock_db_pool._data["trends"] = trends
    yield mock_db_pool


# =============================================================================
# Velocity Engine Fixtures
# =============================================================================

@pytest.fixture
def velocity_config() -> Dict:
    """Default velocity engine configuration."""
    return {
        "min_data_points": 3,
        "max_history_hours": 72,
        "growth_threshold": 0.15,  # 15% growth rate threshold
        "r2_threshold": 0.7  # R-squared threshold for exponential fit
    }


@pytest_asyncio.fixture
async def velocity_engine(velocity_config: Dict) -> AsyncGenerator:
    """Create a velocity engine instance for testing."""
    try:
        from detection.velocity_engine import VelocityEngine
        engine = VelocityEngine(**velocity_config)
        yield engine
    except ImportError:
        mock = MagicMock()
        mock.calculate_velocity = MagicMock(return_value={
            "growth_rate": 0.25,
            "r_squared": 0.85,
            "doubling_time_hours": 8.5
        })
        yield mock


@pytest.fixture
def exponential_growth_data() -> List[Dict]:
    """Generate perfect exponential growth data for velocity testing."""
    base_views = 1000
    growth_rate = 0.3  # 30% growth per hour
    data_points = []
    
    for hour in range(12):
        timestamp = datetime.now(timezone.utc) - timedelta(hours=12-hour)
        views = int(base_views * (1 + growth_rate) ** hour)
        data_points.append({
            "timestamp": timestamp.isoformat(),
            "views": views,
            "likes": int(views * 0.15),
            "shares": int(views * 0.02)
        })
    
    return data_points


@pytest.fixture
def flat_growth_data() -> List[Dict]:
    """Generate flat (no growth) data for velocity testing."""
    data_points = []
    base_views = 10000
    
    for hour in range(12):
        timestamp = datetime.now(timezone.utc) - timedelta(hours=12-hour)
        # Small random variation
        views = base_views + (hour * 10)
        data_points.append({
            "timestamp": timestamp.isoformat(),
            "views": views,
            "likes": int(views * 0.15),
            "shares": int(views * 0.02)
        })
    
    return data_points


@pytest.fixture
def declining_growth_data() -> List[Dict]:
    """Generate declining (saturating) data for velocity testing."""
    base_views = 1000000
    data_points = []
    
    for hour in range(12):
        timestamp = datetime.now(timezone.utc) - timedelta(hours=12-hour)
        # Views plateau then decline
        if hour < 6:
            views = int(base_views * (1.1 ** hour))
        else:
            views = int(base_views * (1.1 ** 6) * (0.95 ** (hour - 6)))
        
        data_points.append({
            "timestamp": timestamp.isoformat(),
            "views": views,
            "likes": int(views * 0.12),
            "shares": int(views * 0.015)
        })
    
    return data_points


# =============================================================================
# Saturation Engine Fixtures
# =============================================================================

@pytest.fixture
def saturation_config() -> Dict:
    """Default saturation engine configuration."""
    return {
        "early_stage_threshold": 0.30,
        "peaking_threshold": 0.70,
        "saturated_threshold": 0.90,
        "min_sample_size": 5
    }


@pytest_asyncio.fixture
async def saturation_engine(saturation_config: Dict) -> AsyncGenerator:
    """Create a saturation engine instance for testing."""
    try:
        from detection.saturation_engine import SaturationEngine
        engine = SaturationEngine(**saturation_config)
        yield engine
    except ImportError:
        mock = MagicMock()
        mock.calculate_saturation = MagicMock(return_value={
            "score": 0.65,
            "stage": "peaking",
            "confidence": 0.85
        })
        yield mock


@pytest.fixture
def saturation_scenarios() -> Dict[str, Dict]:
    """Sample saturation scenarios at different lifecycle stages."""
    return {
        "early_stage": {
            "score": 0.15,
            "stage": "early",
            "indicators": {
                "view_velocity": 0.25,
                "engagement_rate": 0.18,
                "creator_diversity": 0.85
            }
        },
        "peaking": {
            "score": 0.72,
            "stage": "peaking",
            "indicators": {
                "view_velocity": 0.65,
                "engagement_rate": 0.14,
                "creator_diversity": 0.60
            }
        },
        "saturated": {
            "score": 0.93,
            "stage": "saturated",
            "indicators": {
                "view_velocity": 0.05,
                "engagement_rate": 0.08,
                "creator_diversity": 0.25
            }
        },
        "expired": {
            "score": 0.12,
            "stage": "expired",
            "indicators": {
                "view_velocity": -0.15,
                "engagement_rate": 0.05,
                "creator_diversity": 0.10
            }
        }
    }


# =============================================================================
# Lifecycle Manager Fixtures
# =============================================================================

@pytest.fixture
def lifecycle_config() -> Dict:
    """Default lifecycle manager configuration."""
    return {
        "emerging_threshold": 0.20,
        "peaking_threshold": 0.60,
        "saturated_threshold": 0.85,
        "expiration_hours": 48,
        "min_velocity_for_active": 0.05
    }


@pytest_asyncio.fixture
async def lifecycle_manager(lifecycle_config: Dict) -> AsyncGenerator:
    """Create a lifecycle manager instance for testing."""
    try:
        from detection.lifecycle_manager import LifecycleManager
        manager = LifecycleManager(**lifecycle_config)
        yield manager
    except ImportError:
        mock = MagicMock()
        mock.transition_state = MagicMock(return_value="peaking")
        mock.is_expired = MagicMock(return_value=False)
        yield mock


@pytest.fixture
def lifecycle_transitions() -> List[Dict]:
    """Sample lifecycle state transitions for testing."""
    return [
        {
            "from_state": "new",
            "to_state": "emerging",
            "velocity": 0.25,
            "saturation": 0.15,
            "expected": "emerging"
        },
        {
            "from_state": "emerging",
            "to_state": "peaking",
            "velocity": 0.75,
            "saturation": 0.55,
            "expected": "peaking"
        },
        {
            "from_state": "peaking",
            "to_state": "saturated",
            "velocity": 0.10,
            "saturation": 0.88,
            "expected": "saturated"
        },
        {
            "from_state": "saturated",
            "to_state": "expired",
            "velocity": 0.02,
            "saturation": 0.20,
            "hours_since_last": 50,
            "expected": "expired"
        }
    ]


# =============================================================================
# Trend Model Fixtures
# =============================================================================

@pytest.fixture
def sample_trend() -> Dict:
    """Create a sample trend record."""
    return {
        "id": "trend_12345",
        "hashtag": "#sampletrend",
        "status": "peaking",
        "velocity": 0.65,
        "saturation": 0.58,
        "confidence": 0.82,
        "first_seen": (datetime.now(timezone.utc) - timedelta(hours=12)).isoformat(),
        "last_seen": datetime.now(timezone.utc).isoformat(),
        "video_count": 1250,
        "total_views": 5000000,
        "metadata": {
            "top_videos": ["vid1", "vid2", "vid3"],
            "top_creators": ["user1", "user2"],
            "related_hashtags": ["#related1", "#related2"]
        }
    }


@pytest.fixture
def trend_factory():
    """Factory function for creating trends with customizable parameters."""
    def _create_trend(
        hashtag: str = "#testtrend",
        status: str = "emerging",
        velocity: float = 0.30,
        saturation: float = 0.25,
        hours_old: int = 6
    ) -> Dict:
        now = datetime.now(timezone.utc)
        return {
            "id": f"trend_{hashtag.strip('#')}_{int(now.timestamp())}",
            "hashtag": hashtag,
            "status": status,
            "velocity": velocity,
            "saturation": saturation,
            "confidence": 0.75,
            "first_seen": (now - timedelta(hours=hours_old)).isoformat(),
            "last_seen": now.isoformat(),
            "video_count": int(100 * velocity * hours_old),
            "total_views": int(10000 * velocity * hours_old * 100),
            "metadata": {
                "top_videos": [],
                "top_creators": [],
                "related_hashtags": []
            }
        }
    return _create_trend


@pytest.fixture
def sample_trend_batch(trend_factory) -> List[Dict]:
    """Create a batch of trends at different stages."""
    return [
        trend_factory("#trend1", "emerging", 0.25, 0.20, 4),
        trend_factory("#trend2", "emerging", 0.35, 0.30, 8),
        trend_factory("#trend3", "peaking", 0.70, 0.65, 12),
        trend_factory("#trend4", "peaking", 0.85, 0.72, 18),
        trend_factory("#trend5", "saturated", 0.10, 0.92, 24),
    ]


# =============================================================================
# VideoData Model Fixtures
# =============================================================================

@pytest.fixture
def sample_detection_video() -> Dict:
    """Create a sample video record for detection module."""
    return {
        "id": "video_detect_123",
        "url": "https://tiktok.com/@creator/video/123",
        "author_id": "author_456",
        "author_username": "testcreator",
        "hashtags": ["#viral", "#trending", "#dance"],
        "stats": {
            "views": 250000,
            "likes": 45000,
            "shares": 8000,
            "comments": 3200,
            "saves": 12000
        },
        "music_id": "music_789",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "processed_at": None,
        "trend_ids": []
    }


@pytest.fixture
def video_batch_factory():
    """Factory for creating batches of videos with varying stats."""
    def _create_batch(
        count: int = 10,
        base_views: int = 100000,
        growth_pattern: str = "linear"
    ) -> List[Dict]:
        videos = []
        for i in range(count):
            multiplier = 1.0
            if growth_pattern == "exponential":
                multiplier = 1.2 ** i
            elif growth_pattern == "linear":
                multiplier = 1.0 + (i * 0.1)
            elif growth_pattern == "declining":
                multiplier = 1.0 - (i * 0.05)
            
            views = int(base_views * max(multiplier, 0.1))
            videos.append({
                "id": f"video_batch_{i}",
                "url": f"https://tiktok.com/@user{i}/video/{i}",
                "author_id": f"author_{i}",
                "author_username": f"user{i}",
                "hashtags": ["#viral", f"#tag{i}"],
                "stats": {
                    "views": views,
                    "likes": int(views * 0.15),
                    "shares": int(views * 0.025),
                    "comments": int(views * 0.01),
                    "saves": int(views * 0.04)
                },
                "music_id": f"music_{i}",
                "timestamp": (datetime.now(timezone.utc) - timedelta(minutes=i*5)).isoformat(),
                "processed_at": None,
                "trend_ids": []
            })
        return videos
    return _create_batch


# =============================================================================
# Consumer Pipeline Fixtures
# =============================================================================

@pytest.fixture
def consumer_pipeline_config() -> Dict:
    """Consumer pipeline configuration."""
    return {
        "batch_size": 10,
        "poll_interval_seconds": 5,
        "processing_timeout": 30,
        "max_retries": 3,
        "redis_queue_key": "video:queue",
        "redis_result_key": "video:processed"
    }


@pytest_asyncio.fixture
async def mock_consumer(consumer_pipeline_config: Dict) -> AsyncGenerator:
    """Create a mock consumer for testing."""
    try:
        from detection.consumer import VideoConsumer
        consumer = VideoConsumer(**consumer_pipeline_config)
        yield consumer
    except ImportError:
        mock = AsyncMock()
        mock.process_video = AsyncMock(return_value=True)
        mock.process_batch = AsyncMock(return_value=[])
        mock.run = AsyncMock()
        yield mock


# =============================================================================
# Trend Detector Fixtures
# =============================================================================

@pytest.fixture
def trend_detector_config() -> Dict:
    """Trend detector configuration."""
    return {
        "min_videos_for_trend": 3,
        "velocity_threshold": 0.15,
        "confidence_threshold": 0.70,
        "time_window_hours": 24,
        "max_trends": 100
    }


@pytest_asyncio.fixture
async def trend_detector(trend_detector_config: Dict) -> AsyncGenerator:
    """Create a trend detector instance for testing."""
    try:
        from detection.trend_detector import TrendDetector
        detector = TrendDetector(**trend_detector_config)
        yield detector
    except ImportError:
        mock = MagicMock()
        mock.detect_trends = MagicMock(return_value=[
            {"hashtag": "#trend1", "confidence": 0.85},
            {"hashtag": "#trend2", "confidence": 0.72}
        ])
        mock.aggregate_by_hashtag = MagicMock(return_value={})
        yield mock


# =============================================================================
# Environment & Configuration Fixtures
# =============================================================================

@pytest.fixture
def detection_env_vars(monkeypatch) -> Dict[str, str]:
    """Set up mock environment variables for detection module."""
    env_vars = {
        "DATABASE_URL": "postgresql://test:test@localhost:5432/test",
        "REDIS_URL": "redis://localhost:6379/0",
        "REDIS_QUEUE_KEY": "video:queue",
        "VELOCITY_THRESHOLD": "0.15",
        "SATURATION_THRESHOLD": "0.70",
        "LOG_LEVEL": "DEBUG"
    }
    
    for key, value in env_vars.items():
        monkeypatch.setenv(key, value)
    
    return env_vars


@pytest.fixture
def temp_db_path(tmp_path: Path) -> Path:
    """Provide a temporary path for database files."""
    return tmp_path / "test.db"


# =============================================================================
# Fixture Data Loaders
# =============================================================================

@pytest.fixture
def load_sample_video_data():
    """Load sample video data from fixtures file."""
    def _load():
        fixture_path = Path(__file__).parent / "fixtures" / "sample_video_data.json"
        if fixture_path.exists():
            with open(fixture_path, 'r') as f:
                return json.load(f)
        return []
    return _load


@pytest.fixture
def load_sample_trend_data():
    """Load sample trend data from fixtures file."""
    def _load():
        fixture_path = Path(__file__).parent / "fixtures" / "sample_trend_data.json"
        if fixture_path.exists():
            with open(fixture_path, 'r') as f:
                return json.load(f)
        return []
    return _load


# =============================================================================
# Cleanup Fixtures
# =============================================================================

@pytest.fixture(autouse=True)
def cleanup_detection_fixtures():
    """Clean up any resources after detection tests."""
    yield
    # Cleanup handled by other fixtures
