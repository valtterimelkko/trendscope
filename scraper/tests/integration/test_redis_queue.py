"""
Redis Queue Integration Tests

Tests Redis queue operations with a real Redis instance.
All tests are skipped if Redis is not available.

Test Coverage:
- Push single video to queue
- Push multiple videos to queue
- Pop video from queue (RPOP)
- Queue length tracking (LLEN)
- Queue empty handling
- TTL enforcement on queue (EXPIRE)
- Queue persistence across reconnections
- Priority queue handling (using multiple queues)
- Batch push operations (pipeline)
- JSON serialization/deserialization round-trip
"""

import asyncio
import json
import os
import uuid
from datetime import datetime, timezone
from typing import AsyncGenerator, List

import pytest
import pytest_asyncio
import redis.asyncio as redis

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
        # Test connection
        client.ping()
        return client
    except (redis.ConnectionError, redis.TimeoutError):
        pytest.skip("Redis not available", allow_module_level=True)


@pytest_asyncio.fixture
async def test_queue_name() -> str:
    """Generate a unique queue name for each test to avoid conflicts."""
    return f"test:queue:{uuid.uuid4().hex[:8]}"


@pytest_asyncio.fixture
async def cleanup_queue(redis_client: redis.Redis):
    """Cleanup fixture to delete test queues after tests."""
    queues_to_cleanup = []
    
    def register_queue(queue_name: str):
        queues_to_cleanup.append(queue_name)
        return queue_name
    
    yield register_queue
    
    # Cleanup after test
    for queue_name in queues_to_cleanup:
        try:
            await redis_client.delete(queue_name)
        except Exception:
            pass


@pytest.fixture
def sample_video() -> VideoData:
    """Create a sample video for testing."""
    return VideoData(
        id="test_video_123",
        desc="Test video description #viral #trending",
        create_time=int(datetime.now(timezone.utc).timestamp()),
        stats=VideoStats(
            play_count=100000,
            digg_count=15000,
            share_count=2500,
            comment_count=800,
        ),
        author=VideoAuthor(
            unique_id="testuser",
            nickname="Test User",
            follower_count=50000,
        ),
        music=VideoMusic(
            id="music_456",
            title="Test Sound",
            author_name="Music Artist",
        ),
        hashtags=["viral", "trending", "test"],
        source_type="trending",
        source_query=None,
    )


@pytest.fixture
def sample_video_batch() -> List[VideoData]:
    """Create a batch of sample videos for testing."""
    videos = []
    for i in range(10):
        video = VideoData(
            id=f"test_video_{i:03d}",
            desc=f"Test video {i} description #test",
            create_time=int(datetime.now(timezone.utc).timestamp()) - i * 3600,
            stats=VideoStats(
                play_count=10000 * (i + 1),
                digg_count=1000 * (i + 1),
                share_count=100 * (i + 1),
                comment_count=50 * (i + 1),
            ),
            author=VideoAuthor(
                unique_id=f"testuser{i}",
                nickname=f"Test User {i}",
                follower_count=10000 * (i + 1),
            ),
            music=VideoMusic(
                id=f"music_{i}",
                title=f"Sound {i}",
                author_name=f"Artist {i}",
            ),
            hashtags=["test", f"tag{i}"],
            source_type="hashtag",
            source_query="test",
        )
        videos.append(video)
    return videos


# =============================================================================
# Basic Queue Operations
# =============================================================================

@pytest.mark.integration
@pytest.mark.requires_redis
async def test_push_single_video_to_queue(
    redis_client: redis.Redis,
    test_queue_name: str,
    cleanup_queue,
    sample_video: VideoData,
):
    """Test pushing a single video to the queue."""
    queue_name = cleanup_queue(test_queue_name)
    
    # Push video to queue
    video_json = sample_video.model_dump_json()
    result = await redis_client.lpush(queue_name, video_json)
    
    # Verify push was successful (returns new length of list)
    assert result == 1
    
    # Verify video is in queue
    queue_length = await redis_client.llen(queue_name)
    assert queue_length == 1


@pytest.mark.integration
@pytest.mark.requires_redis
async def test_push_multiple_videos_to_queue(
    redis_client: redis.Redis,
    test_queue_name: str,
    cleanup_queue,
    sample_video_batch: List[VideoData],
):
    """Test pushing multiple videos to the queue."""
    queue_name = cleanup_queue(test_queue_name)
    
    # Push all videos
    for video in sample_video_batch:
        await redis_client.lpush(queue_name, video.model_dump_json())
    
    # Verify queue length
    queue_length = await redis_client.llen(queue_name)
    assert queue_length == len(sample_video_batch)


@pytest.mark.integration
@pytest.mark.requires_redis
async def test_pop_video_from_queue(
    redis_client: redis.Redis,
    test_queue_name: str,
    cleanup_queue,
    sample_video: VideoData,
):
    """Test popping a video from the queue using RPOP."""
    queue_name = cleanup_queue(test_queue_name)
    
    # Push video
    video_json = sample_video.model_dump_json()
    await redis_client.lpush(queue_name, video_json)
    
    # Pop video using RPOP (removes from tail - FIFO order)
    result = await redis_client.rpop(queue_name)
    
    # Verify result
    assert result is not None
    assert isinstance(result, (str, bytes))
    
    # Parse and verify video data
    if isinstance(result, bytes):
        result = result.decode('utf-8')
    
    parsed_video = VideoData.model_validate_json(result)
    assert parsed_video.id == sample_video.id
    assert parsed_video.desc == sample_video.desc


@pytest.mark.integration
@pytest.mark.requires_redis
async def test_queue_length_tracking(
    redis_client: redis.Redis,
    test_queue_name: str,
    cleanup_queue,
    sample_video_batch: List[VideoData],
):
    """Test queue length tracking with LLEN."""
    queue_name = cleanup_queue(test_queue_name)
    
    # Initially empty
    length = await redis_client.llen(queue_name)
    assert length == 0
    
    # Add videos one by one and check length
    for i, video in enumerate(sample_video_batch, 1):
        await redis_client.lpush(queue_name, video.model_dump_json())
        length = await redis_client.llen(queue_name)
        assert length == i


@pytest.mark.integration
@pytest.mark.requires_redis
async def test_queue_empty_handling(
    redis_client: redis.Redis,
    test_queue_name: str,
    cleanup_queue,
):
    """Test handling of empty queue."""
    queue_name = cleanup_queue(test_queue_name)
    
    # Try to pop from empty queue
    result = await redis_client.rpop(queue_name)
    assert result is None
    
    # LLEN on non-existent key returns 0
    length = await redis_client.llen(queue_name)
    assert length == 0


@pytest.mark.integration
@pytest.mark.requires_redis
async def test_fifo_order(
    redis_client: redis.Redis,
    test_queue_name: str,
    cleanup_queue,
):
    """Test FIFO (First In, First Out) order of queue."""
    queue_name = cleanup_queue(test_queue_name)
    
    # Push videos in order
    video_ids = ["first", "second", "third"]
    for vid in video_ids:
        video = VideoData(
            id=vid,
            desc=f"Video {vid}",
            create_time=int(datetime.now(timezone.utc).timestamp()),
            stats=VideoStats(play_count=100, digg_count=10, share_count=5, comment_count=2),
            author=VideoAuthor(unique_id="test", nickname="Test", follower_count=100),
        )
        await redis_client.lpush(queue_name, video.model_dump_json())
    
    # Pop and verify FIFO order (RPOP gives us first pushed first)
    popped_ids = []
    for _ in range(len(video_ids)):
        result = await redis_client.rpop(queue_name)
        if result:
            if isinstance(result, bytes):
                result = result.decode('utf-8')
            parsed = VideoData.model_validate_json(result)
            popped_ids.append(parsed.id)
    
    # FIFO order: first pushed should be first popped
    assert popped_ids == list(reversed(video_ids))


# =============================================================================
# TTL and Persistence Tests
# =============================================================================

@pytest.mark.integration
@pytest.mark.requires_redis
async def test_ttl_enforcement_on_queue(
    redis_client: redis.Redis,
    test_queue_name: str,
    cleanup_queue,
    sample_video: VideoData,
):
    """Test TTL enforcement on queue using EXPIRE."""
    queue_name = cleanup_queue(test_queue_name)
    
    # Push video
    await redis_client.lpush(queue_name, sample_video.model_dump_json())
    
    # Set TTL to 2 seconds
    ttl_set = await redis_client.expire(queue_name, 2)
    assert ttl_set is True
    
    # Verify TTL is set
    ttl = await redis_client.ttl(queue_name)
    assert 0 < ttl <= 2
    
    # Verify data exists
    length = await redis_client.llen(queue_name)
    assert length == 1
    
    # Wait for expiration
    await asyncio.sleep(3)
    
    # Verify queue is expired
    length = await redis_client.llen(queue_name)
    assert length == 0
    
    # Key should not exist anymore
    exists = await redis_client.exists(queue_name)
    assert exists == 0


@pytest.mark.integration
@pytest.mark.requires_redis
async def test_queue_persistence_across_reconnections(
    redis_client: redis.Redis,
    test_queue_name: str,
    cleanup_queue,
    sample_video_batch: List[VideoData],
):
    """Test queue persistence across Redis reconnections."""
    queue_name = cleanup_queue(test_queue_name)
    
    # Push videos with first connection
    for video in sample_video_batch[:5]:
        await redis_client.lpush(queue_name, video.model_dump_json())
    
    # Create new connection (simulating reconnection)
    redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    new_client = redis.Redis.from_url(redis_url)
    
    try:
        # Verify data is still there
        length = await new_client.llen(queue_name)
        assert length == 5
        
        # Pop some videos with new connection
        result = await new_client.rpop(queue_name)
        assert result is not None
        
        # Verify with original connection
        length = await redis_client.llen(queue_name)
        assert length == 4
    finally:
        await new_client.close()


@pytest.mark.integration
@pytest.mark.requires_redis
async def test_ttl_refresh_on_push(
    redis_client: redis.Redis,
    test_queue_name: str,
    cleanup_queue,
    sample_video: VideoData,
):
    """Test that TTL can be refreshed when pushing new items."""
    queue_name = cleanup_queue(test_queue_name)
    
    # Push first video with short TTL
    await redis_client.lpush(queue_name, sample_video.model_dump_json())
    await redis_client.expire(queue_name, 10)
    
    # Get initial TTL
    ttl1 = await redis_client.ttl(queue_name)
    assert ttl1 > 5  # Should be close to 10
    
    # Wait a bit
    await asyncio.sleep(2)
    
    # Push another video and refresh TTL
    video2 = sample_video.model_copy(update={"id": "test_video_456"})
    await redis_client.lpush(queue_name, video2.model_dump_json())
    await redis_client.expire(queue_name, 10)
    
    # Verify TTL is refreshed
    ttl2 = await redis_client.ttl(queue_name)
    assert ttl2 > ttl1 - 1  # Should be close to 10 again


# =============================================================================
# Batch Operations
# =============================================================================

@pytest.mark.integration
@pytest.mark.requires_redis
async def test_batch_push_with_pipeline(
    redis_client: redis.Redis,
    test_queue_name: str,
    cleanup_queue,
    sample_video_batch: List[VideoData],
):
    """Test batch push operations using Redis pipeline."""
    queue_name = cleanup_queue(test_queue_name)
    
    # Use pipeline for batch operation
    async with redis_client.pipeline() as pipe:
        for video in sample_video_batch:
            pipe.lpush(queue_name, video.model_dump_json())
        results = await pipe.execute()
    
    # Verify all pushes succeeded
    assert len(results) == len(sample_video_batch)
    
    # Verify queue length
    length = await redis_client.llen(queue_name)
    assert length == len(sample_video_batch)


@pytest.mark.integration
@pytest.mark.requires_redis
async def test_batch_push_with_ttl(
    redis_client: redis.Redis,
    test_queue_name: str,
    cleanup_queue,
    sample_video_batch: List[VideoData],
):
    """Test batch push with TTL setting."""
    queue_name = cleanup_queue(test_queue_name)
    
    # Batch push using pipeline
    async with redis_client.pipeline() as pipe:
        for video in sample_video_batch:
            pipe.lpush(queue_name, video.model_dump_json())
        await pipe.execute()
    
    # Set TTL once for the queue
    await redis_client.expire(queue_name, 3600)
    
    # Verify TTL is set
    ttl = await redis_client.ttl(queue_name)
    assert ttl > 0
    
    # Verify all videos are there
    length = await redis_client.llen(queue_name)
    assert length == len(sample_video_batch)


# =============================================================================
# Priority Queue Tests (using multiple queues)
# =============================================================================

@pytest.mark.integration
@pytest.mark.requires_redis
async def test_priority_queue_with_multiple_queues(
    redis_client: redis.Redis,
    cleanup_queue,
    sample_video: VideoData,
):
    """Test priority queue simulation using multiple Redis queues."""
    high_priority_queue = cleanup_queue("test:queue:high")
    normal_priority_queue = cleanup_queue("test:queue:normal")
    low_priority_queue = cleanup_queue("test:queue:low")
    
    # Push to different priority queues
    video_high = sample_video.model_copy(update={"id": "high_priority_video"})
    video_normal = sample_video.model_copy(update={"id": "normal_priority_video"})
    video_low = sample_video.model_copy(update={"id": "low_priority_video"})
    
    await redis_client.lpush(high_priority_queue, video_high.model_dump_json())
    await redis_client.lpush(normal_priority_queue, video_normal.model_dump_json())
    await redis_client.lpush(low_priority_queue, video_low.model_dump_json())
    
    # Verify queue lengths
    assert await redis_client.llen(high_priority_queue) == 1
    assert await redis_client.llen(normal_priority_queue) == 1
    assert await redis_client.llen(low_priority_queue) == 1
    
    # Simulate priority consumption (high first)
    result = await redis_client.rpop(high_priority_queue)
    assert result is not None
    parsed = VideoData.model_validate_json(result if isinstance(result, str) else result.decode())
    assert parsed.id == "high_priority_video"


# =============================================================================
# Serialization Tests
# =============================================================================

@pytest.mark.integration
@pytest.mark.requires_redis
async def test_json_serialization_roundtrip(
    redis_client: redis.Redis,
    test_queue_name: str,
    cleanup_queue,
):
    """Test JSON serialization and deserialization round-trip."""
    queue_name = cleanup_queue(test_queue_name)
    
    # Create video with all fields
    original = VideoData(
        id="roundtrip_test_123",
        desc="Testing serialization round-trip #test",
        create_time=1704067200,
        stats=VideoStats(
            play_count=999999,
            digg_count=88888,
            share_count=7777,
            comment_count=666,
        ),
        author=VideoAuthor(
            unique_id="roundtripuser",
            nickname="Roundtrip User",
            follower_count=123456,
        ),
        music=VideoMusic(
            id="music_roundtrip",
            title="Roundtrip Song",
            author_name="Roundtrip Artist",
        ),
        hashtags=["test", "roundtrip", "serialization"],
        source_type="trending",
        source_query="test",
    )
    
    # Serialize and push
    json_str = original.model_dump_json()
    await redis_client.lpush(queue_name, json_str)
    
    # Pop and deserialize
    result = await redis_client.rpop(queue_name)
    assert result is not None
    
    if isinstance(result, bytes):
        result = result.decode('utf-8')
    
    parsed = VideoData.model_validate_json(result)
    
    # Verify all fields match
    assert parsed.id == original.id
    assert parsed.desc == original.desc
    assert parsed.create_time == original.create_time
    assert parsed.stats.play_count == original.stats.play_count
    assert parsed.stats.digg_count == original.stats.digg_count
    assert parsed.stats.share_count == original.stats.share_count
    assert parsed.stats.comment_count == original.stats.comment_count
    assert parsed.author.unique_id == original.author.unique_id
    assert parsed.author.nickname == original.author.nickname
    assert parsed.author.follower_count == original.author.follower_count
    assert parsed.music.id == original.music.id
    assert parsed.music.title == original.music.title
    assert parsed.music.author_name == original.music.author_name
    assert parsed.hashtags == original.hashtags
    assert parsed.source_type == original.source_type
    assert parsed.source_query == original.source_query


@pytest.mark.integration
@pytest.mark.requires_redis
async def test_complex_video_data_serialization(
    redis_client: redis.Redis,
    test_queue_name: str,
    cleanup_queue,
):
    """Test serialization of video data with special characters and edge cases."""
    queue_name = cleanup_queue(test_queue_name)
    
    # Create video with special characters
    video = VideoData(
        id="special_chars_123",
        desc='Special chars: "quotes" \n newline \t tab 🔥 emoji',
        create_time=int(datetime.now(timezone.utc).timestamp()),
        stats=VideoStats(play_count=0, digg_count=0, share_count=0, comment_count=0),
        author=VideoAuthor(unique_id="user_with_🔥", nickname="User 🎵", follower_count=1),
        music=None,  # Test null music
        hashtags=["tag-with-dash", "tag_with_underscore", "123numeric"],
        source_type="hashtag",
        source_query="special-query_test",
    )
    
    # Push and pop
    await redis_client.lpush(queue_name, video.model_dump_json())
    result = await redis_client.rpop(queue_name)
    
    assert result is not None
    if isinstance(result, bytes):
        result = result.decode('utf-8')
    
    parsed = VideoData.model_validate_json(result)
    assert parsed.id == video.id
    assert parsed.desc == video.desc
    assert parsed.music is None


@pytest.mark.integration
@pytest.mark.requires_redis
async def test_large_batch_serialization(
    redis_client: redis.Redis,
    test_queue_name: str,
    cleanup_queue,
):
    """Test serialization with larger batch of videos (50 records)."""
    queue_name = cleanup_queue(test_queue_name)
    
    # Generate 50 video records
    videos = []
    for i in range(50):
        video = VideoData(
            id=f"bulk_video_{i:03d}",
            desc=f"Bulk test video {i} with some longer description text",
            create_time=int(datetime.now(timezone.utc).timestamp()) - i * 60,
            stats=VideoStats(
                play_count=10000 + i * 100,
                digg_count=1000 + i * 10,
                share_count=100 + i,
                comment_count=50 + i // 2,
            ),
            author=VideoAuthor(
                unique_id=f"bulkuser{i}",
                nickname=f"Bulk User {i}",
                follower_count=1000 * (i + 1),
            ),
            music=VideoMusic(
                id=f"bulkmusic{i}",
                title=f"Bulk Song {i}",
                author_name=f"Bulk Artist {i}",
            ) if i % 2 == 0 else None,  # Half have music
            hashtags=["bulk", f"tag{i}"],
            source_type="trending" if i % 2 == 0 else "hashtag",
            source_query="bulk_test",
        )
        videos.append(video)
    
    # Push all videos using pipeline
    async with redis_client.pipeline() as pipe:
        for video in videos:
            pipe.lpush(queue_name, video.model_dump_json())
        await pipe.execute()
    
    # Set TTL
    await redis_client.expire(queue_name, 3600)
    
    # Verify all 50 are there
    length = await redis_client.llen(queue_name)
    assert length == 50
    
    # Pop and verify all
    for i in range(50):
        result = await redis_client.rpop(queue_name)
        assert result is not None


# =============================================================================
# Error Handling and Edge Cases
# =============================================================================

@pytest.mark.integration
@pytest.mark.requires_redis
async def test_concurrent_push_operations(
    redis_client: redis.Redis,
    test_queue_name: str,
    cleanup_queue,
):
    """Test concurrent push operations from multiple tasks."""
    queue_name = cleanup_queue(test_queue_name)
    
    async def push_videos(start_id: int, count: int):
        """Push videos with IDs from start_id to start_id + count."""
        for i in range(start_id, start_id + count):
            video = VideoData(
                id=f"concurrent_{i:03d}",
                desc=f"Concurrent video {i}",
                create_time=int(datetime.now(timezone.utc).timestamp()),
                stats=VideoStats(play_count=i, digg_count=i, share_count=i, comment_count=i),
                author=VideoAuthor(unique_id="concurrent", nickname="Concurrent", follower_count=100),
            )
            await redis_client.lpush(queue_name, video.model_dump_json())
    
    # Run concurrent pushes
    await asyncio.gather(
        push_videos(0, 10),
        push_videos(10, 10),
        push_videos(20, 10),
    )
    
    # Verify all 30 videos are there
    length = await redis_client.llen(queue_name)
    assert length == 30


@pytest.mark.integration
@pytest.mark.requires_redis
async def test_queue_with_special_characters_in_name(
    redis_client: redis.Redis,
    cleanup_queue,
    sample_video: VideoData,
):
    """Test queue names with various characters."""
    # Test various queue name patterns
    queue_names = [
        "test:queue:with:colons",
        "test_queue_with_underscores",
        "test-queue-with-dashes",
        "test123numeric",
    ]
    
    for queue_name in queue_names:
        cleanup_queue(queue_name)
        await redis_client.lpush(queue_name, sample_video.model_dump_json())
        
        length = await redis_client.llen(queue_name)
        assert length == 1, f"Failed for queue name: {queue_name}"
        
        # Cleanup immediately
        await redis_client.delete(queue_name)


@pytest.mark.integration
@pytest.mark.requires_redis
async def test_lrange_operation(
    redis_client: redis.Redis,
    test_queue_name: str,
    cleanup_queue,
    sample_video_batch: List[VideoData],
):
    """Test LRANGE operation for peeking at queue without removing items."""
    queue_name = cleanup_queue(test_queue_name)
    
    # Push batch
    for video in sample_video_batch:
        await redis_client.lpush(queue_name, video.model_dump_json())
    
    # Get first 5 items without removing
    items = await redis_client.lrange(queue_name, 0, 4)
    assert len(items) == 5
    
    # Verify queue is still intact
    length = await redis_client.llen(queue_name)
    assert length == len(sample_video_batch)
    
    # Parse first item
    first_item = items[0]
    if isinstance(first_item, bytes):
        first_item = first_item.decode('utf-8')
    parsed = VideoData.model_validate_json(first_item)
    assert parsed.id == sample_video_batch[-1].id  # Last pushed is first in list
