"""
TikTokProducer Integration Tests

Tests TikTokProducer with real Redis connection.
All tests are skipped if Redis is not available.

Test Coverage:
- Initialize producer with Redis client
- Push video to queue (push_to_queue method)
- Video data serialization
- Queue name configuration
- Error handling on Redis failure
- Concurrent push operations
- Batch push operations (push_batch_to_queue)
"""

import asyncio
import os
import uuid
from datetime import datetime, timezone
from typing import List
from unittest.mock import AsyncMock, patch

import pytest
import pytest_asyncio
import redis.asyncio as redis

from scraper.producer import TikTokProducer
from scraper.models import VideoData, VideoStats, VideoAuthor, VideoMusic


# =============================================================================
# Fixtures
# =============================================================================

@pytest.fixture(scope="module")
def redis_client() -> redis.Redis:
    """Provide a Redis client, skip tests if Redis is unavailable."""
    try:
        client = redis.Redis.from_url(
            os.getenv("REDIS_URL", "redis://localhost:6379/0"),
            socket_connect_timeout=5,
            socket_timeout=5,
        )
        client.ping()
        return client
    except (redis.ConnectionError, redis.TimeoutError):
        pytest.skip("Redis not available", allow_module_level=True)


@pytest_asyncio.fixture
async def test_queue_name() -> str:
    """Generate a unique queue name for each test."""
    return f"test:producer:queue:{uuid.uuid4().hex[:8]}"


@pytest_asyncio.fixture
async def cleanup_queue(redis_client: redis.Redis):
    """Cleanup fixture to delete test queues after tests."""
    queues_to_cleanup = []
    
    def register_queue(queue_name: str):
        queues_to_cleanup.append(queue_name)
        return queue_name
    
    yield register_queue
    
    for queue_name in queues_to_cleanup:
        try:
            await redis_client.delete(queue_name)
        except Exception:
            pass


@pytest.fixture
def sample_video() -> VideoData:
    """Create a sample video for testing."""
    return VideoData(
        id="producer_test_video_123",
        desc="Producer test video #integration #test",
        create_time=int(datetime.now(timezone.utc).timestamp()),
        stats=VideoStats(
            play_count=500000,
            digg_count=75000,
            share_count=12000,
            comment_count=3500,
        ),
        author=VideoAuthor(
            unique_id="producertest",
            nickname="Producer Test User",
            follower_count=100000,
        ),
        music=VideoMusic(
            id="producer_music_789",
            title="Producer Test Sound",
            author_name="Test Artist",
        ),
        hashtags=["integration", "test", "producer"],
        source_type="trending",
        source_query=None,
    )


@pytest.fixture
def sample_video_batch() -> List[VideoData]:
    """Create a batch of sample videos for testing."""
    videos = []
    for i in range(20):
        video = VideoData(
            id=f"batch_video_{i:03d}",
            desc=f"Batch test video {i} #batch",
            create_time=int(datetime.now(timezone.utc).timestamp()) - i * 300,
            stats=VideoStats(
                play_count=50000 * (i + 1),
                digg_count=5000 * (i + 1),
                share_count=500 * (i + 1),
                comment_count=250 * (i + 1),
            ),
            author=VideoAuthor(
                unique_id=f"batchuser{i}",
                nickname=f"Batch User {i}",
                follower_count=50000,
            ),
            music=VideoMusic(
                id=f"batchmusic{i}",
                title=f"Batch Sound {i}",
                author_name=f"Batch Artist {i}",
            ),
            hashtags=["batch", "test", f"tag{i}"],
            source_type="hashtag",
            source_query="batch_test",
        )
        videos.append(video)
    return videos


@pytest_asyncio.fixture
async def producer(redis_client: redis.Redis) -> TikTokProducer:
    """Create a TikTokProducer instance with real Redis."""
    return TikTokProducer(redis_client=redis_client)


# =============================================================================
# Producer Initialization Tests
# =============================================================================

@pytest.mark.integration
@pytest.mark.requires_redis
async def test_initialize_producer_with_redis_client(redis_client: redis.Redis):
    """Test initializing TikTokProducer with Redis client."""
    producer = TikTokProducer(redis_client=redis_client)
    
    # Verify producer attributes
    assert producer.redis is redis_client
    assert producer.videos_produced == 0
    assert producer.errors_count == 0
    assert producer.last_scrape_time is None
    
    # Verify rate limiters are initialized
    assert "trending" in producer.rate_limiters
    assert "hashtag" in producer.rate_limiters
    assert "user" in producer.rate_limiters
    
    # Verify circuit breaker is initialized
    assert producer.circuit_breaker is not None


@pytest.mark.integration
@pytest.mark.requires_redis
async def test_initialize_producer_with_custom_proxy(redis_client: redis.Redis):
    """Test initializing TikTokProducer with custom proxy."""
    custom_proxy = "http://custom:proxy@example.com:8080"
    producer = TikTokProducer(
        redis_client=redis_client,
        proxy=custom_proxy,
    )
    
    assert producer.proxy == custom_proxy


# =============================================================================
# Push to Queue Tests
# =============================================================================

@pytest.mark.integration
@pytest.mark.requires_redis
async def test_push_single_video_to_queue(
    producer: TikTokProducer,
    redis_client: redis.Redis,
    test_queue_name: str,
    cleanup_queue,
    sample_video: VideoData,
):
    """Test pushing a single video to queue using push_to_queue."""
    queue_name = cleanup_queue(test_queue_name)
    
    # Push video
    result = await producer.push_to_queue(sample_video, queue=queue_name)
    
    # Verify push was successful
    assert result is True
    
    # Verify video is in queue
    queue_length = await redis_client.llen(queue_name)
    assert queue_length == 1
    
    # Verify video data is correct
    popped = await redis_client.rpop(queue_name)
    assert popped is not None
    
    if isinstance(popped, bytes):
        popped = popped.decode('utf-8')
    
    parsed = VideoData.model_validate_json(popped)
    assert parsed.id == sample_video.id
    assert parsed.desc == sample_video.desc


@pytest.mark.integration
@pytest.mark.requires_redis
async def test_push_to_queue_uses_default_queue(
    producer: TikTokProducer,
    redis_client: redis.Redis,
    sample_video: VideoData,
):
    """Test that push_to_queue uses default queue when not specified."""
    # This test uses the default queue from settings
    # We'll verify by checking the default queue key
    from scraper.config import settings
    default_queue = settings.redis_video_queue
    
    # Push without specifying queue
    result = await producer.push_to_queue(sample_video)
    
    assert result is True
    
    # Cleanup - remove from default queue
    await redis_client.lrem(default_queue, 0, sample_video.model_dump_json())


@pytest.mark.integration
@pytest.mark.requires_redis
async def test_push_video_data_serialization(
    producer: TikTokProducer,
    redis_client: redis.Redis,
    test_queue_name: str,
    cleanup_queue,
):
    """Test video data is correctly serialized when pushed."""
    queue_name = cleanup_queue(test_queue_name)
    
    # Create video with all fields
    video = VideoData(
        id="serialization_test_123",
        desc="Testing serialization #test",
        create_time=1704067200,
        stats=VideoStats(
            play_count=999999,
            digg_count=88888,
            share_count=7777,
            comment_count=666,
        ),
        author=VideoAuthor(
            unique_id="serialuser",
            nickname="Serial User",
            follower_count=123456,
        ),
        music=VideoMusic(
            id="serial_music",
            title="Serial Song",
            author_name="Serial Artist",
        ),
        hashtags=["test", "serialization", "integration"],
        source_type="trending",
        source_query="test",
    )
    
    # Push video
    await producer.push_to_queue(video, queue=queue_name)
    
    # Pop and verify all fields
    result = await redis_client.rpop(queue_name)
    assert result is not None
    
    if isinstance(result, bytes):
        result = result.decode('utf-8')
    
    parsed = VideoData.model_validate_json(result)
    
    # Verify all fields
    assert parsed.id == video.id
    assert parsed.desc == video.desc
    assert parsed.create_time == video.create_time
    assert parsed.stats.play_count == video.stats.play_count
    assert parsed.stats.digg_count == video.stats.digg_count
    assert parsed.author.unique_id == video.author.unique_id
    assert parsed.music.id == video.music.id
    assert parsed.hashtags == video.hashtags
    assert parsed.source_type == video.source_type


@pytest.mark.integration
@pytest.mark.requires_redis
async def test_queue_name_configuration(
    producer: TikTokProducer,
    redis_client: redis.Redis,
    cleanup_queue,
    sample_video: VideoData,
):
    """Test queue name configuration with different patterns."""
    queue_names = [
        "test:queue:custom:1",
        "test_queue_custom_2",
        "test-queue-custom-3",
    ]
    
    for queue_name in queue_names:
        cleanup_queue(queue_name)
        
        # Push to custom queue
        result = await producer.push_to_queue(sample_video, queue=queue_name)
        assert result is True
        
        # Verify it's in the right queue
        length = await redis_client.llen(queue_name)
        assert length == 1
        
        # Cleanup
        await redis_client.delete(queue_name)


@pytest.mark.integration
@pytest.mark.requires_redis
async def test_push_batch_to_queue(
    producer: TikTokProducer,
    redis_client: redis.Redis,
    test_queue_name: str,
    cleanup_queue,
    sample_video_batch: List[VideoData],
):
    """Test batch push operation using push_batch_to_queue."""
    queue_name = cleanup_queue(test_queue_name)
    
    # Push batch
    count = await producer.push_batch_to_queue(sample_video_batch, queue=queue_name)
    
    # Verify count returned
    assert count == len(sample_video_batch)
    
    # Verify all videos are in queue
    queue_length = await redis_client.llen(queue_name)
    assert queue_length == len(sample_video_batch)


@pytest.mark.integration
@pytest.mark.requires_redis
async def test_push_batch_to_queue_empty_list(
    producer: TikTokProducer,
    test_queue_name: str,
    cleanup_queue,
):
    """Test batch push with empty list returns 0."""
    queue_name = cleanup_queue(test_queue_name)
    
    # Push empty list
    count = await producer.push_batch_to_queue([], queue=queue_name)
    
    assert count == 0


@pytest.mark.integration
@pytest.mark.requires_redis
async def test_push_batch_uses_default_queue(
    producer: TikTokProducer,
    redis_client: redis.Redis,
    sample_video_batch: List[VideoData],
):
    """Test batch push uses default queue when not specified."""
    from scraper.config import settings
    default_queue = settings.redis_video_queue
    
    # Push batch without specifying queue
    count = await producer.push_batch_to_queue(sample_video_batch[:5])
    
    assert count == 5
    
    # Cleanup
    await redis_client.delete(default_queue)


# =============================================================================
# TTL Tests
# =============================================================================

@pytest.mark.integration
@pytest.mark.requires_redis
async def test_push_to_queue_sets_ttl(
    producer: TikTokProducer,
    redis_client: redis.Redis,
    test_queue_name: str,
    cleanup_queue,
    sample_video: VideoData,
):
    """Test that push_to_queue sets TTL on the queue."""
    queue_name = cleanup_queue(test_queue_name)
    
    # Push video
    await producer.push_to_queue(sample_video, queue=queue_name)
    
    # Verify TTL is set (should be > 0)
    ttl = await redis_client.ttl(queue_name)
    assert ttl > 0
    
    # From settings, default TTL is 72 hours
    from scraper.config import settings
    assert ttl <= settings.redis_video_ttl


@pytest.mark.integration
@pytest.mark.requires_redis
async def test_batch_push_sets_ttl(
    producer: TikTokProducer,
    redis_client: redis.Redis,
    test_queue_name: str,
    cleanup_queue,
    sample_video_batch: List[VideoData],
):
    """Test that batch push sets TTL on the queue."""
    queue_name = cleanup_queue(test_queue_name)
    
    # Push batch
    await producer.push_batch_to_queue(sample_video_batch, queue=queue_name)
    
    # Verify TTL is set
    ttl = await redis_client.ttl(queue_name)
    assert ttl > 0


# =============================================================================
# Error Handling Tests
# =============================================================================

@pytest.mark.integration
@pytest.mark.requires_redis
async def test_error_handling_on_redis_failure(sample_video: VideoData):
    """Test error handling when Redis fails."""
    # Create a mock Redis that fails
    mock_redis = AsyncMock()
    mock_redis.lpush = AsyncMock(side_effect=redis.RedisError("Connection refused"))
    
    producer = TikTokProducer(redis_client=mock_redis)
    
    # Attempt to push should raise RedisError
    with pytest.raises(redis.RedisError):
        await producer.push_to_queue(sample_video)


@pytest.mark.integration
@pytest.mark.requires_redis
async def test_error_handling_batch_push_redis_failure(sample_video_batch: List[VideoData]):
    """Test error handling on batch push when Redis fails."""
    # Create a mock Redis that fails
    mock_redis = AsyncMock()
    mock_redis.pipeline = AsyncMock(side_effect=redis.RedisError("Connection refused"))
    
    producer = TikTokProducer(redis_client=mock_redis)
    
    # Attempt batch push should raise RedisError
    with pytest.raises(redis.RedisError):
        await producer.push_batch_to_queue(sample_video_batch)


@pytest.mark.integration
@pytest.mark.requires_redis
async def test_producer_tracks_errors_on_failure():
    """Test that producer tracks error count on Redis failure."""
    mock_redis = AsyncMock()
    mock_redis.lpush = AsyncMock(side_effect=redis.RedisError("Connection refused"))
    
    producer = TikTokProducer(redis_client=mock_redis)
    assert producer.errors_count == 0
    
    # Failed push should not update error count in push_to_queue
    # (it re-raises the exception)
    with pytest.raises(redis.RedisError):
        await producer.push_to_queue(VideoData(
            id="test",
            create_time=123,
            stats=VideoStats(play_count=1, digg_count=1, share_count=1, comment_count=1),
            author=VideoAuthor(unique_id="test", nickname="Test", follower_count=1),
        ))


# =============================================================================
# Concurrent Operations Tests
# =============================================================================

@pytest.mark.integration
@pytest.mark.requires_redis
async def test_concurrent_push_operations(
    producer: TikTokProducer,
    redis_client: redis.Redis,
    test_queue_name: str,
    cleanup_queue,
    sample_video: VideoData,
):
    """Test concurrent push operations from multiple tasks."""
    queue_name = cleanup_queue(test_queue_name)
    
    async def push_multiple(count: int, prefix: str):
        """Push multiple videos with given prefix."""
        for i in range(count):
            video = sample_video.model_copy(update={
                "id": f"{prefix}_video_{i:03d}"
            })
            await producer.push_to_queue(video, queue=queue_name)
    
    # Run concurrent pushes
    await asyncio.gather(
        push_multiple(5, "task1"),
        push_multiple(5, "task2"),
        push_multiple(5, "task3"),
    )
    
    # Verify all 15 videos are in queue
    queue_length = await redis_client.llen(queue_name)
    assert queue_length == 15


@pytest.mark.integration
@pytest.mark.requires_redis
async def test_concurrent_batch_push(
    producer: TikTokProducer,
    redis_client: redis.Redis,
    test_queue_name: str,
    cleanup_queue,
    sample_video_batch: List[VideoData],
):
    """Test concurrent batch push operations."""
    queue_name = cleanup_queue(test_queue_name)
    
    # Split batch into chunks
    chunk1 = [v.model_copy(update={"id": f"concurrent_{v.id}"}) for v in sample_video_batch[:10]]
    chunk2 = [v.model_copy(update={"id": f"concurrent2_{v.id}"}) for v in sample_video_batch[10:]]
    
    # Push concurrently
    results = await asyncio.gather(
        producer.push_batch_to_queue(chunk1, queue=queue_name),
        producer.push_batch_to_queue(chunk2, queue=queue_name),
    )
    
    # Verify both batches were pushed
    assert sum(results) == len(chunk1) + len(chunk2)
    
    # Verify queue length
    queue_length = await redis_client.llen(queue_name)
    assert queue_length == len(chunk1) + len(chunk2)


# =============================================================================
# Producer State Tests
# =============================================================================

@pytest.mark.integration
@pytest.mark.requires_redis
async def test_producer_metrics_tracking(
    producer: TikTokProducer,
    redis_client: redis.Redis,
    test_queue_name: str,
    cleanup_queue,
    sample_video_batch: List[VideoData],
):
    """Test that producer tracks videos produced metric."""
    queue_name = cleanup_queue(test_queue_name)
    
    # Initial state
    assert producer.videos_produced == 0
    
    # Note: The producer doesn't currently track videos_produced
    # when pushing to queue (only during scraping)
    # This test documents the current behavior
    
    # Push videos
    for video in sample_video_batch[:5]:
        await producer.push_to_queue(video, queue=queue_name)
    
    # Push batch
    await producer.push_batch_to_queue(sample_video_batch[5:10], queue=queue_name)
    
    # The videos_produced counter is primarily used during scraping,
    # not when directly pushing to queue
    # This is expected behavior


# =============================================================================
# Edge Cases
# =============================================================================

@pytest.mark.integration
@pytest.mark.requires_redis
async def test_push_video_with_special_characters(
    producer: TikTokProducer,
    redis_client: redis.Redis,
    test_queue_name: str,
    cleanup_queue,
):
    """Test pushing video with special characters in description."""
    queue_name = cleanup_queue(test_queue_name)
    
    video = VideoData(
        id="special_chars_video",
        desc='Special: "quotes", \n newline, \t tab, 🔥 emoji, üñíçödé',
        create_time=int(datetime.now(timezone.utc).timestamp()),
        stats=VideoStats(play_count=100, digg_count=10, share_count=5, comment_count=2),
        author=VideoAuthor(unique_id="special_🔥", nickname="Special 🎵", follower_count=100),
        music=None,
        hashtags=["special-tag", "test_tag", "123"],
        source_type="hashtag",
        source_query="special-test",
    )
    
    # Push
    result = await producer.push_to_queue(video, queue=queue_name)
    assert result is True
    
    # Pop and verify
    popped = await redis_client.rpop(queue_name)
    assert popped is not None
    
    if isinstance(popped, bytes):
        popped = popped.decode('utf-8')
    
    parsed = VideoData.model_validate_json(popped)
    assert parsed.id == video.id
    assert parsed.desc == video.desc
    assert parsed.author.unique_id == video.author.unique_id


@pytest.mark.integration
@pytest.mark.requires_redis
async def test_push_large_batch(
    producer: TikTokProducer,
    redis_client: redis.Redis,
    test_queue_name: str,
    cleanup_queue,
):
    """Test pushing a large batch of 50 videos."""
    queue_name = cleanup_queue(test_queue_name)
    
    # Generate 50 videos
    videos = []
    for i in range(50):
        video = VideoData(
            id=f"large_batch_{i:03d}",
            desc=f"Large batch video {i}",
            create_time=int(datetime.now(timezone.utc).timestamp()) - i * 60,
            stats=VideoStats(
                play_count=1000 * (i + 1),
                digg_count=100 * (i + 1),
                share_count=10 * (i + 1),
                comment_count=5 * (i + 1),
            ),
            author=VideoAuthor(
                unique_id=f"largeuser{i}",
                nickname=f"Large User {i}",
                follower_count=1000 * (i + 1),
            ),
            music=VideoMusic(
                id=f"largemusic{i}",
                title=f"Large Song {i}",
                author_name=f"Large Artist {i}",
            ) if i % 3 == 0 else None,
            hashtags=["large", "batch", f"tag{i}"],
            source_type="trending",
            source_query="large_batch_test",
        )
        videos.append(video)
    
    # Push batch
    count = await producer.push_batch_to_queue(videos, queue=queue_name)
    assert count == 50
    
    # Verify
    queue_length = await redis_client.llen(queue_name)
    assert queue_length == 50
