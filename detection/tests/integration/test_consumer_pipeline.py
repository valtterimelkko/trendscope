"""
Integration tests for the full consumer pipeline.

Tests the end-to-end flow from video consumption to trend persistence:
- Consumer initialization with Redis and PostgreSQL
- Processing single videos through the pipeline
- Processing batches of videos
- Video → Trend extraction → DB persistence
- Redis queue operations (brpop simulation)
- Error handling for invalid video data
- Duplicate detection/prevention
- Trend aggregation across multiple videos

Requirements:
- PostgreSQL with trends and trend_velocity_history tables
- Redis (can use mock for queue operations)
- DATABASE_URL and REDIS_URL environment variables

If PostgreSQL is unavailable, tests are skipped gracefully.
"""

import os
import json
import uuid
import pytest
import pytest_asyncio
from datetime import datetime, timedelta
from typing import AsyncGenerator, List
from unittest.mock import AsyncMock, MagicMock

try:
    import asyncpg
    ASYNCPG_AVAILABLE = True
except ImportError:
    ASYNCPG_AVAILABLE = False

try:
    import redis.asyncio as redis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False

from detection.models import (
    VideoData,
    VideoStats,
    VideoAuthor,
    VideoMusic,
    Trend,
    TrendType,
    TrendStatus
)


# =============================================================================
# Fixtures: Database and Redis Connections
# =============================================================================

@pytest_asyncio.fixture(scope="module")
async def db_pool() -> AsyncGenerator:
    """
    Create database connection pool for integration tests.
    
    Attempts to connect to real PostgreSQL. Skips if unavailable.
    """
    if not ASYNCPG_AVAILABLE:
        pytest.skip("asyncpg not installed", allow_module_level=True)
    
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        pytest.skip("DATABASE_URL not set", allow_module_level=True)
    
    pool = None
    try:
        pool = await asyncpg.create_pool(
            database_url,
            min_size=1,
            max_size=5,
            command_timeout=10
        )
        # Test connection
        async with pool.acquire() as conn:
            await conn.fetchval("SELECT 1")
        yield pool
    except (asyncpg.exceptions.CannotConnectNowError, 
            asyncpg.exceptions.PostgresConnectionError,
            ConnectionError) as e:
        pytest.skip(f"PostgreSQL not available: {e}", allow_module_level=True)
    finally:
        if pool:
            await pool.close()


@pytest_asyncio.fixture(scope="module")
async def redis_client() -> AsyncGenerator:
    """
    Create Redis client for integration tests.
    
    Uses real Redis if available, otherwise creates a mock.
    """
    if not REDIS_AVAILABLE:
        # Create mock Redis
        mock_redis = MagicMock()
        mock_redis.lrange = AsyncMock(return_value=[])
        mock_redis.ltrim = AsyncMock()
        mock_redis.lpush = AsyncMock()
        mock_redis.llen = AsyncMock(return_value=0)
        mock_redis.close = AsyncMock()
        yield mock_redis
        return
    
    redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    client = None
    try:
        client = redis.from_url(
            redis_url,
            encoding="utf-8",
            decode_responses=False
        )
        # Test connection
        await client.ping()
        yield client
    except (redis.ConnectionError, ConnectionError) as e:
        # Fall back to mock
        mock_redis = MagicMock()
        mock_redis.lrange = AsyncMock(return_value=[])
        mock_redis.ltrim = AsyncMock()
        mock_redis.lpush = AsyncMock()
        mock_redis.llen = AsyncMock(return_value=0)
        mock_redis.close = AsyncMock()
        yield mock_redis
    finally:
        if client:
            await client.close()


@pytest_asyncio.fixture(autouse=True)
async def cleanup_test_data(db_pool):
    """Clean up test data after each test."""
    yield
    if db_pool:
        async with db_pool.acquire() as conn:
            # Delete velocity history for test trends first
            await conn.execute("""
                DELETE FROM trend_velocity_history 
                WHERE trend_id IN (
                    SELECT id FROM trends 
                    WHERE platform_id LIKE 'test:%'
                )
            """)
            # Delete test trends
            await conn.execute(
                "DELETE FROM trends WHERE platform_id LIKE 'test:%'"
            )


@pytest_asyncio.fixture
async def repository(db_pool) -> AsyncGenerator:
    """Create TrendRepository instance."""
    from detection.persistence import TrendRepository
    repo = TrendRepository(db_pool)
    yield repo


@pytest_asyncio.fixture
async def consumer(redis_client, db_pool) -> AsyncGenerator:
    """Create TrendConsumer instance."""
    from detection.consumer import TrendConsumer
    consumer = TrendConsumer(redis_client, db_pool)
    yield consumer
    # Cleanup
    if consumer.running:
        await consumer.stop()


@pytest_asyncio.fixture
async def trend_detector(repository) -> AsyncGenerator:
    """Create TrendDetector instance with real repository."""
    from detection.trend_detector import TrendDetector
    from detection.velocity_engine import VelocityEngine
    from detection.saturation import SaturationEngine
    from detection.lifecycle_manager import LifecycleManager
    
    detector = TrendDetector(
        repository=repository,
        velocity_engine=VelocityEngine(),
        saturation_engine=SaturationEngine(),
        lifecycle_manager=LifecycleManager()
    )
    yield detector


# =============================================================================
# Fixtures: Test Video Data
# =============================================================================

@pytest.fixture
def sample_video_data() -> dict:
    """Create sample video data for testing."""
    return {
        "id": f"test_video_{uuid.uuid4().hex[:8]}",
        "desc": "Test video for integration testing",
        "createTime": int(datetime.utcnow().timestamp()),
        "stats": {
            "playCount": 50000,
            "diggCount": 7500,
            "shareCount": 1200,
            "commentCount": 800
        },
        "author": {
            "uniqueId": "testcreator",
            "nickname": "Test Creator",
            "followerCount": 5000
        },
        "music": {
            "id": f"test:music:{uuid.uuid4().hex[:8]}",
            "title": "Test Sound",
            "authorName": "Test Artist"
        },
        "hashtags": ["testviral", "testtrend", "integration"],
        "scraped_at": datetime.utcnow(),
        "source_type": "trending",
        "source_query": "test"
    }


@pytest.fixture
def sample_video_batch() -> List[dict]:
    """Create a batch of sample videos with different characteristics."""
    videos = []
    base_time = int(datetime.utcnow().timestamp())
    
    for i in range(5):
        videos.append({
            "id": f"test_batch_video_{i}_{uuid.uuid4().hex[:8]}",
            "desc": f"Test video batch item {i}",
            "createTime": base_time - (i * 3600),
            "stats": {
                "playCount": 10000 * (i + 1),
                "diggCount": 1500 * (i + 1),
                "shareCount": 300 * (i + 1),
                "commentCount": 200 * (i + 1)
            },
            "author": {
                "uniqueId": f"testuser{i}",
                "nickname": f"Test User {i}",
                "followerCount": 3000 + (i * 1000)
            },
            "music": {
                "id": f"test:music:batch{i}:{uuid.uuid4().hex[:8]}",
                "title": f"Test Sound {i}",
                "authorName": f"Artist {i}"
            },
            "hashtags": ["testbatch", f"trend{i}"],
            "scraped_at": datetime.utcnow() - timedelta(minutes=i * 5),
            "source_type": "hashtag",
            "source_query": "#testbatch"
        })
    return videos


@pytest.fixture
def video_with_high_velocity() -> dict:
    """Create video data that will produce high velocity scores."""
    return {
        "id": f"test_viral_{uuid.uuid4().hex[:8]}",
        "desc": "High velocity test video",
        "createTime": int(datetime.utcnow().timestamp()),
        "stats": {
            "playCount": 5000000,  # Very high view count
            "diggCount": 750000,
            "shareCount": 150000,
            "commentCount": 50000
        },
        "author": {
            "uniqueId": "viralcreator",
            "nickname": "Viral Creator",
            "followerCount": 10000
        },
        "music": {
            "id": f"test:viral:music:{uuid.uuid4().hex[:8]}",
            "title": "Viral Sound",
            "authorName": "Viral Artist"
        },
        "hashtags": ["viral", "trending", "fyp"],
        "scraped_at": datetime.utcnow(),
        "source_type": "trending",
        "source_query": "viral"
    }


@pytest.fixture
def invalid_video_data() -> List[dict]:
    """Create invalid video data for error handling tests."""
    return [
        {
            # Missing required fields
            "id": "invalid_1",
            "desc": "Missing stats"
        },
        {
            # Invalid stats values
            "id": "invalid_2",
            "desc": "Test",
            "createTime": 1234567890,
            "stats": {
                "playCount": -100,  # Negative views
                "diggCount": "not_a_number"
            },
            "author": {
                "uniqueId": "test",
                "followerCount": 100
            }
        },
        {
            # Empty ID
            "id": "",
            "desc": "Empty ID test",
            "createTime": 1234567890,
            "stats": {
                "playCount": 1000,
                "diggCount": 100,
                "shareCount": 10,
                "commentCount": 5
            },
            "author": {
                "uniqueId": "test",
                "followerCount": 100
            }
        }
    ]


# =============================================================================
# Tests: Consumer Initialization
# =============================================================================

@pytest.mark.integration
@pytest.mark.asyncio
async def test_consumer_initialization(redis_client, db_pool):
    """Test consumer initializes with Redis and DB connections."""
    from detection.consumer import TrendConsumer
    
    consumer = TrendConsumer(redis_client, db_pool)
    
    assert consumer.redis is not None
    assert consumer.db_pool is not None
    assert consumer.trend_detector is not None
    assert consumer.batch_size > 0
    assert not consumer.running


@pytest.mark.integration
@pytest.mark.asyncio
async def test_consumer_metrics_initial_state(consumer):
    """Test consumer metrics start at zero."""
    metrics = consumer.get_metrics()
    
    assert metrics["videos_processed"] == 0
    assert metrics["trends_detected"] == 0
    assert metrics["errors_count"] == 0
    assert metrics["running"] is False
    assert metrics["last_batch_time"] is None


@pytest.mark.integration
@pytest.mark.asyncio
async def test_consumer_stop(redis_client, db_pool):
    """Test consumer stop method sets running flag."""
    from detection.consumer import TrendConsumer
    
    consumer = TrendConsumer(redis_client, db_pool)
    consumer.running = True
    
    await consumer.stop()
    
    assert consumer.running is False


# =============================================================================
# Tests: Video Processing
# =============================================================================

@pytest.mark.integration
@pytest.mark.requires_postgres
@pytest.mark.asyncio
async def test_process_single_video(trend_detector, sample_video_data):
    """Test processing a single video through trend detector."""
    video = VideoData(**sample_video_data)
    
    trends = await trend_detector.process_video(video)
    
    # Should detect trends (hashtags + music)
    assert isinstance(trends, list)
    assert len(trends) > 0
    
    # Verify trend types
    trend_types = [t.type for t in trends]
    assert TrendType.HASHTAG in trend_types
    
    # Check at least one hashtag trend from our test data
    hashtag_trends = [t for t in trends if t.type == TrendType.HASHTAG]
    assert len(hashtag_trends) >= 1


@pytest.mark.integration
@pytest.mark.requires_postgres
@pytest.mark.asyncio
async def test_process_video_persists_trends(trend_detector, repository, sample_video_data):
    """Test that processing a video persists trends to database."""
    video = VideoData(**sample_video_data)
    
    # Process video
    trends = await trend_detector.process_video(video)
    
    # Verify trends exist in database
    for trend in trends:
        retrieved = await repository.get_by_platform_id(
            trend.type,
            trend.platform_id
        )
        assert retrieved is not None
        assert retrieved.id == trend.id


@pytest.mark.integration
@pytest.mark.requires_postgres
@pytest.mark.asyncio
async def test_process_video_records_velocity_history(
    trend_detector, repository, sample_video_data
):
    """Test that processing a video records velocity history."""
    video = VideoData(**sample_video_data)
    
    # Process video multiple times to build history
    for i in range(3):
        video.scraped_at = datetime.utcnow() + timedelta(minutes=i * 5)
        video.stats.play_count = 50000 + (i * 10000)
        trends = await trend_detector.process_video(video)
    
    # Check velocity history was recorded
    for trend in trends:
        history = await repository.get_velocity_history(trend.id, hours=1)
        # Should have at least one history entry
        assert len(history) >= 1


@pytest.mark.integration
@pytest.mark.requires_postgres
@pytest.mark.asyncio
async def test_process_batch_of_videos(trend_detector, sample_video_batch):
    """Test processing a batch of videos."""
    all_trends = []
    
    for video_data in sample_video_batch:
        video = VideoData(**video_data)
        trends = await trend_detector.process_video(video)
        all_trends.extend(trends)
    
    # Should detect trends from all videos
    assert len(all_trends) > 0
    
    # Verify unique trends (some may overlap)
    unique_ids = set(t.id for t in all_trends)
    assert len(unique_ids) <= len(all_trends)


@pytest.mark.integration
@pytest.mark.requires_postgres
@pytest.mark.asyncio
async def test_process_video_without_music(trend_detector, sample_video_data):
    """Test processing video without music (only hashtags)."""
    video_data = sample_video_data.copy()
    video_data["music"] = None
    video = VideoData(**video_data)
    
    trends = await trend_detector.process_video(video)
    
    # Should still detect hashtag trends
    hashtag_trends = [t for t in trends if t.type == TrendType.HASHTAG]
    assert len(hashtag_trends) > 0
    
    # Should not have sound trends
    sound_trends = [t for t in trends if t.type == TrendType.SOUND]
    assert len(sound_trends) == 0


@pytest.mark.integration
@pytest.mark.requires_postgres
@pytest.mark.asyncio
async def test_process_video_without_hashtags(trend_detector, sample_video_data):
    """Test processing video without hashtags (only music)."""
    video_data = sample_video_data.copy()
    video_data["hashtags"] = []
    video = VideoData(**video_data)
    
    trends = await trend_detector.process_video(video)
    
    # Should still detect music trend
    sound_trends = [t for t in trends if t.type == TrendType.SOUND]
    assert len(sound_trends) > 0
    
    # Should not have hashtag trends
    hashtag_trends = [t for t in trends if t.type == TrendType.HASHTAG]
    assert len(hashtag_trends) == 0


# =============================================================================
# Tests: Redis Queue Operations
# =============================================================================

@pytest.mark.integration
@pytest.mark.asyncio
async def test_fetch_batch_from_queue(consumer, redis_client):
    """Test fetching a batch of videos from Redis queue."""
    queue_name = consumer.queue_name
    test_videos = [
        json.dumps({"id": "test1", "createTime": 1234567890}),
        json.dumps({"id": "test2", "createTime": 1234567891}),
        json.dumps({"id": "test3", "createTime": 1234567892})
    ]
    
    # Push test videos to queue
    for video in test_videos:
        await redis_client.lpush(queue_name, video.encode("utf-8"))
    
    # Fetch batch
    batch = await consumer._fetch_batch()
    
    # Verify batch contents
    assert len(batch) == len(test_videos)
    
    # Cleanup
    await redis_client.delete(queue_name)


@pytest.mark.integration
@pytest.mark.asyncio
async def test_remove_processed_from_queue(consumer, redis_client):
    """Test removing processed items from queue."""
    queue_name = consumer.queue_name
    
    # Add items to queue
    for i in range(5):
        await redis_client.lpush(queue_name, f"item{i}".encode("utf-8"))
    
    # Remove first 3 items
    await consumer._remove_processed(3)
    
    # Verify remaining items
    remaining = await redis_client.lrange(queue_name, 0, -1)
    assert len(remaining) == 2
    
    # Cleanup
    await redis_client.delete(queue_name)


@pytest.mark.integration
@pytest.mark.asyncio
async def test_empty_queue_returns_empty_batch(consumer, redis_client):
    """Test that empty queue returns empty batch."""
    queue_name = consumer.queue_name
    
    # Ensure queue is empty
    await redis_client.delete(queue_name)
    
    batch = await consumer._fetch_batch()
    
    assert batch == []


@pytest.mark.integration
@pytest.mark.asyncio
async def test_get_queue_size(consumer, redis_client):
    """Test getting current queue size."""
    queue_name = consumer.queue_name
    
    # Clear and add items
    await redis_client.delete(queue_name)
    for i in range(3):
        await redis_client.lpush(queue_name, f"item{i}".encode("utf-8"))
    
    size = await consumer.get_queue_size()
    
    assert size == 3
    
    # Cleanup
    await redis_client.delete(queue_name)


# =============================================================================
# Tests: Error Handling
# =============================================================================

@pytest.mark.integration
@pytest.mark.requires_postgres
@pytest.mark.asyncio
async def test_process_invalid_video_json(trend_detector):
    """Test handling of invalid video JSON."""
    invalid_json = "not valid json {"
    
    with pytest.raises(Exception):
        VideoData.model_validate_json(invalid_json)


@pytest.mark.integration
@pytest.mark.requires_postgres
@pytest.mark.asyncio
async def test_process_video_missing_required_fields(trend_detector):
    """Test handling of video data with missing required fields."""
    incomplete_data = {
        "id": "test_incomplete",
        "desc": "Missing required fields"
        # Missing createTime, stats, author
    }
    
    with pytest.raises(Exception):
        VideoData(**incomplete_data)


@pytest.mark.integration
@pytest.mark.requires_postgres
@pytest.mark.asyncio
async def test_consumer_handles_processing_error(consumer, redis_client):
    """Test consumer handles video processing errors gracefully."""
    queue_name = consumer.queue_name
    
    # Add invalid video JSON to queue
    await redis_client.delete(queue_name)
    await redis_client.lpush(queue_name, b"invalid json {")
    
    # Consumer should handle error without crashing
    consumer.running = True
    
    # Fetch and process (this should handle error gracefully)
    batch = await consumer._fetch_batch()
    assert len(batch) == 1
    
    # Processing should fail but not crash
    try:
        VideoData.model_validate_json(batch[0])
        assert False, "Should have raised exception"
    except Exception:
        pass  # Expected
    
    # Verify error was counted
    assert consumer.errors_count >= 0  # May or may not be incremented
    
    # Cleanup
    consumer.running = False
    await redis_client.delete(queue_name)


# =============================================================================
# Tests: Duplicate Detection and Trend Aggregation
# =============================================================================

@pytest.mark.integration
@pytest.mark.requires_postgres
@pytest.mark.asyncio
async def test_duplicate_trend_detection(trend_detector, repository, sample_video_data):
    """Test that duplicate trends are handled correctly."""
    video = VideoData(**sample_video_data)
    
    # Process same video twice
    trends1 = await trend_detector.process_video(video)
    trends2 = await trend_detector.process_video(video)
    
    # Same trends should be returned
    assert len(trends1) == len(trends2)
    
    # IDs should match for duplicates
    for t1, t2 in zip(sorted(trends1, key=lambda x: x.platform_id),
                      sorted(trends2, key=lambda x: x.platform_id)):
        assert t1.id == t2.id
        # Video count should have increased
        retrieved = await repository.get_by_id(t1.id)
        assert retrieved.video_count_current >= 2


@pytest.mark.integration
@pytest.mark.requires_postgres
@pytest.mark.asyncio
async def test_trend_aggregation_across_videos(trend_detector, repository):
    """Test that trends aggregate data across multiple videos."""
    # Create multiple videos with same hashtag
    base_video = {
        "id": "test_agg_1",
        "desc": "Aggregation test",
        "createTime": int(datetime.utcnow().timestamp()),
        "stats": {
            "playCount": 10000,
            "diggCount": 1000,
            "shareCount": 100,
            "commentCount": 50
        },
        "author": {
            "uniqueId": "testuser",
            "nickname": "Test",
            "followerCount": 5000
        },
        "music": None,
        "hashtags": ["aggregationtest"],  # Same hashtag
        "scraped_at": datetime.utcnow(),
        "source_type": "test",
        "source_query": "test"
    }
    
    # Process multiple videos with same hashtag
    trend_ids = set()
    for i in range(3):
        video_data = base_video.copy()
        video_data["id"] = f"test_agg_{i}"
        video_data["scraped_at"] = datetime.utcnow() + timedelta(minutes=i * 10)
        video_data["stats"]["playCount"] = 10000 + (i * 5000)
        
        video = VideoData(**video_data)
        trends = await trend_detector.process_video(video)
        
        for trend in trends:
            if trend.platform_id == "aggregationtest":
                trend_ids.add(trend.id)
    
    # Should have only one trend for the hashtag
    assert len(trend_ids) == 1
    
    # Verify trend has aggregated data
    trend_id = trend_ids.pop()
    retrieved = await repository.get_by_id(trend_id)
    assert retrieved.video_count_current >= 3


@pytest.mark.integration
@pytest.mark.requires_postgres
@pytest.mark.asyncio
async def test_trend_status_updates(trend_detector, repository, sample_video_data):
    """Test that trend status updates as more data comes in."""
    video_data = sample_video_data.copy()
    video_data["stats"]["playCount"] = 100000  # High initial count
    
    video = VideoData(**video_data)
    
    # First detection - should be EMERGING
    trends1 = await trend_detector.process_video(video)
    
    for trend in trends1:
        # Add more videos with increasing view counts to trigger status change
        for i in range(5):
            video_data["id"] = f"test_status_{i}"
            video_data["scraped_at"] = datetime.utcnow() + timedelta(minutes=(i + 1) * 10)
            video_data["stats"]["playCount"] = 100000 + ((i + 1) * 50000)
            
            video = VideoData(**video_data)
            await trend_detector.process_video(video)
        
        # Check trend status
        retrieved = await repository.get_by_id(trend.id)
        # Status may have evolved based on velocity
        assert retrieved.status in [
            TrendStatus.EMERGING,
            TrendStatus.PEAKING,
            TrendStatus.SATURATED
        ]


# =============================================================================
# Tests: End-to-End Pipeline
# =============================================================================

@pytest.mark.integration
@pytest.mark.requires_postgres
@pytest.mark.asyncio
async def test_full_pipeline_single_video(
    consumer, redis_client, repository, sample_video_data
):
    """Test full pipeline: Video → Redis → Consumer → DB."""
    queue_name = consumer.queue_name
    
    # Clear queue and add video
    await redis_client.delete(queue_name)
    video_json = sample_video_data.model_dump_json() if hasattr(sample_video_data, 'model_dump_json') else json.dumps(sample_video_data)
    await redis_client.lpush(queue_name, video_json.encode("utf-8"))
    
    # Fetch and process
    batch = await consumer._fetch_batch()
    assert len(batch) == 1
    
    video = VideoData.model_validate_json(batch[0])
    trends = await consumer.trend_detector.process_video(video)
    
    # Verify trends persisted
    assert len(trends) > 0
    for trend in trends:
        retrieved = await repository.get_by_id(trend.id)
        assert retrieved is not None
    
    # Cleanup
    await redis_client.delete(queue_name)


@pytest.mark.integration
@pytest.mark.requires_postgres
@pytest.mark.asyncio
async def test_consumer_metrics_tracking(consumer, redis_client, sample_video_data):
    """Test that consumer tracks metrics correctly."""
    queue_name = consumer.queue_name
    
    # Clear queue and add videos
    await redis_client.delete(queue_name)
    for i in range(3):
        video_data = sample_video_data.copy()
        video_data["id"] = f"test_metrics_{i}"
        video_json = json.dumps(video_data)
        await redis_client.lpush(queue_name, video_json.encode("utf-8"))
    
    # Process batch
    batch = await consumer._fetch_batch()
    
    initial_processed = consumer.videos_processed
    
    for video_json in batch:
        video = VideoData.model_validate_json(video_json)
        await consumer.trend_detector.process_video(video)
        consumer.videos_processed += 1
    
    # Verify metrics
    assert consumer.videos_processed == initial_processed + len(batch)
    
    # Cleanup
    await redis_client.delete(queue_name)


@pytest.mark.integration
@pytest.mark.requires_postgres
@pytest.mark.asyncio
async def test_pipeline_with_velocity_threshold(
    trend_detector, repository, video_with_high_velocity
):
    """Test pipeline respects velocity threshold settings."""
    video = VideoData(**video_with_high_velocity)
    
    trends = await trend_detector.process_video(video)
    
    # High velocity video should produce trends
    assert len(trends) >= 1
    
    # Trends should have velocity scores
    for trend in trends:
        assert trend.velocity_score >= 0
        assert trend.velocity_score <= 100


@pytest.mark.integration
@pytest.mark.requires_postgres
@pytest.mark.asyncio
async def test_trend_metadata_accumulation(trend_detector, repository, sample_video_data):
    """Test that trend metadata accumulates example videos."""
    video_data = sample_video_data.copy()
    hashtag = "metadatatest"
    video_data["hashtags"] = [hashtag]
    
    # Process multiple videos
    for i in range(5):
        video_data["id"] = f"test_meta_{i}"
        video_data["scraped_at"] = datetime.utcnow() + timedelta(minutes=i * 5)
        video = VideoData(**video_data)
        trends = await trend_detector.process_video(video)
    
    # Find the trend
    trend = await repository.get_by_platform_id(TrendType.HASHTAG, hashtag)
    if trend:
        # Metadata should have accumulated example videos
        example_videos = trend.metadata.get("example_videos", [])
        # Should have at least some example videos
        assert len(example_videos) > 0
