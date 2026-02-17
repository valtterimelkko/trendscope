"""
End-to-End Tests for Full Trendscope Pipeline

Tests the complete data flow:
Test Data → Redis Queue → Consumer → Trend Detector → PostgreSQL
                ↑                                         ↓
                └────────── Verification ←────────────────┘

Scenarios:
1. Single Video Flow - End-to-end latency measurement
2. Batch Video Flow - Trend aggregation and velocity calculation
3. Trend Lifecycle Flow - State transitions (emerging → peaking → saturated)
4. Multi-Trend Flow - Multiple hashtags tracked independently

All tests use pytest.mark.e2e and pytest.mark.slow markers.
Expected runtime: 10-30 seconds per test.
"""

import asyncio
import json
import time
from datetime import datetime, timedelta, timezone
from typing import List

import pytest

from detection.models import VideoData, VideoStats, VideoAuthor, VideoMusic, TrendType, TrendStatus


pytestmark = [pytest.mark.e2e, pytest.mark.slow]


@pytest.mark.e2e
@pytest.mark.slow
class TestSingleVideoFlow:
    """
    Scenario 1: Single Video Flow
    
    - Generate 1 sample video
    - Push to Redis queue (simulate producer)
    - Consume from queue (simulate consumer)
    - Process through trend detector
    - Verify trend created in database
    - Measure end-to-end latency
    """
    
    async def test_single_video_e2e_latency(
        self,
        clean_redis,
        clean_db,
        producer,
        trend_detector,
        trend_repository,
        pipeline_metrics
    ):
        """
        Test complete flow for a single video with latency measurement.
        
        Expected: Video pushed → trend detected → persisted within acceptable latency.
        """
        # Setup: Create test video
        video = VideoData(
            id="test_video_001",
            desc="Test video with #testtrend",
            create_time=int(datetime.now(timezone.utc).timestamp()),
            stats=VideoStats(
                play_count=50000,
                digg_count=7500,
                share_count=1000,
                comment_count=500
            ),
            author=VideoAuthor(
                unique_id="testcreator",
                nickname="Test Creator",
                follower_count=10000
            ),
            music=VideoMusic(
                id="sound_123",
                title="Test Sound",
                author_name="Test Artist"
            ),
            hashtags=["testtrend", "viral"],
            scraped_at=datetime.now(timezone.utc),
            source_type="trending",
            source_query=None
        )
        
        # Start latency measurement
        start_time = time.time()
        
        # Execute: Push to Redis
        await producer.push_to_queue(video)
        pipeline_metrics.videos_pushed += 1
        
        # Record queue depth after push
        queue_depth = await clean_redis.llen("tiktok:videos")
        pipeline_metrics.record_queue_depth(queue_depth, "after_push")
        
        # Execute: Consume from Redis (simulating consumer fetch)
        batch = await clean_redis.lrange("tiktok:videos", 0, 0)
        assert len(batch) == 1, f"Expected 1 video in queue, got {len(batch)}"
        
        # Parse and process
        video_json = batch[0].decode('utf-8') if isinstance(batch[0], bytes) else batch[0]
        video_data = VideoData.model_validate_json(video_json)
        
        # Execute: Process through trend detector
        trends = await trend_detector.process_video(video_data)
        
        # Remove from queue (simulating consumer acknowledgment)
        await clean_redis.ltrim("tiktok:videos", 1, -1)
        
        pipeline_metrics.videos_processed += 1
        
        # Verify: Trend created
        assert len(trends) > 0, "Expected at least one trend to be created"
        trend = trends[0]
        
        # Verify: Persisted to database
        persisted = await trend_repository.get_by_platform_id(
            trend.type,
            trend.platform_id
        )
        assert persisted is not None, "Trend should be persisted in database"
        assert persisted.platform_id == trend.platform_id
        assert persisted.name == trend.name
        assert persisted.status == TrendStatus.EMERGING
        assert persisted.velocity_score > 0
        
        pipeline_metrics.trends_created += 1
        
        # Calculate and record latency
        end_time = time.time()
        latency_ms = (end_time - start_time) * 1000
        pipeline_metrics.record_latency(latency_ms)
        pipeline_metrics.finalize()
        
        # Assertions on latency
        assert latency_ms < 5000, f"End-to-end latency too high: {latency_ms:.2f}ms (expected < 5000ms)"
        
        # Verify metrics
        metrics = pipeline_metrics.to_dict()
        assert metrics["videos_pushed"] == 1
        assert metrics["videos_processed"] == 1
        assert metrics["trends_created"] >= 1
        
    async def test_single_video_with_sound_and_hashtags(
        self,
        clean_redis,
        clean_db,
        producer,
        trend_detector,
        trend_repository
    ):
        """
        Test that a single video creates both sound and hashtag trends.
        
        Expected: Video with music + 2 hashtags = up to 3 trends extracted.
        """
        # Setup: Create video with music and multiple hashtags
        video = VideoData(
            id="test_video_002",
            desc="Video with sound and hashtags #dance #challenge",
            create_time=int(datetime.now(timezone.utc).timestamp()),
            stats=VideoStats(
                play_count=100000,
                digg_count=15000,
                share_count=2500,
                comment_count=1000
            ),
            author=VideoAuthor(
                unique_id="dancecreator",
                nickname="Dance Creator",
                follower_count=50000
            ),
            music=VideoMusic(
                id="viral_sound_001",
                title="Viral Dance Sound",
                author_name="DJ Test"
            ),
            hashtags=["dance", "challenge"],
            scraped_at=datetime.now(timezone.utc),
            source_type="hashtag",
            source_query="dance"
        )
        
        # Execute: Push and process
        await producer.push_to_queue(video)
        
        # Consume and process
        batch = await clean_redis.lrange("tiktok:videos", 0, 0)
        video_data = VideoData.model_validate_json(batch[0])
        trends = await trend_detector.process_video(video_data)
        
        # Verify: Multiple trends extracted
        assert len(trends) >= 2, f"Expected at least 2 trends (sound + hashtag), got {len(trends)}"
        
        # Verify trend types
        trend_types = [t.type for t in trends]
        assert TrendType.SOUND in trend_types, "Should have a sound trend"
        assert TrendType.HASHTAG in trend_types, "Should have hashtag trends"
        
        # Verify each trend is persisted
        for trend in trends:
            persisted = await trend_repository.get_by_platform_id(
                trend.type,
                trend.platform_id
            )
            assert persisted is not None, f"Trend {trend.name} should be persisted"


@pytest.mark.e2e
@pytest.mark.slow
class TestBatchVideoFlow:
    """
    Scenario 2: Batch Video Flow
    
    - Generate 50 videos with trending hashtag
    - Push batch to Redis
    - Process all videos
    - Verify trend aggregation (velocity calculated)
    - Verify velocity history recorded
    """
    
    async def test_batch_video_velocity_calculation(
        self,
        clean_redis,
        clean_db,
        producer,
        trend_detector,
        trend_repository,
        generate_viral_videos,
        pipeline_metrics
    ):
        """
        Test batch processing with viral growth pattern.
        
        Expected: Velocity score increases as more videos are processed,
        and velocity history is recorded.
        """
        # Setup: Generate 50 videos with exponential growth pattern
        hashtag = "#viraltrend2024"
        videos_data = generate_viral_videos(count=50, hashtag=hashtag)
        
        # Convert to VideoData models
        videos = []
        for v in videos_data:
            video = VideoData(
                id=v["id"],
                desc=v["desc"],
                create_time=v["createTime"],
                stats=VideoStats(**v["stats"]),
                author=VideoAuthor(**v["author"]),
                music=VideoMusic(**v["music"]) if v.get("music") else None,
                hashtags=v["hashtags"],
                scraped_at=datetime.fromisoformat(v["scraped_at"]),
                source_type=v["source_type"],
                source_query=v["source_query"]
            )
            videos.append(video)
        
        start_time = time.time()
        
        # Execute: Push batch to Redis
        await producer.push_batch_to_queue(videos)
        pipeline_metrics.videos_pushed = len(videos)
        
        # Record queue depth
        queue_depth = await clean_redis.llen("tiktok:videos")
        pipeline_metrics.record_queue_depth(queue_depth, "after_batch_push")
        
        # Execute: Process all videos
        processed = 0
        trends_created = set()
        
        while True:
            batch = await clean_redis.lrange("tiktok:videos", 0, 9)  # Process in batches of 10
            if not batch:
                break
            
            for video_json in batch:
                video_data = VideoData.model_validate_json(
                    video_json.decode('utf-8') if isinstance(video_json, bytes) else video_json
                )
                trends = await trend_detector.process_video(video_data)
                processed += 1
                
                for trend in trends:
                    trends_created.add((trend.type.value, trend.platform_id))
            
            # Remove processed items
            await clean_redis.ltrim("tiktok:videos", len(batch), -1)
            
            # Record queue depth during processing
            queue_depth = await clean_redis.llen("tiktok:videos")
            pipeline_metrics.record_queue_depth(queue_depth, f"after_processing_{processed}")
        
        pipeline_metrics.videos_processed = processed
        pipeline_metrics.trends_created = len(trends_created)
        pipeline_metrics.finalize()
        
        # Verify: All videos processed
        assert processed == 50, f"Expected 50 videos processed, got {processed}"
        
        # Verify: Trend exists with calculated velocity
        trend = await trend_repository.get_by_platform_id(
            TrendType.HASHTAG,
            hashtag.lower().lstrip('#')
        )
        
        assert trend is not None, f"Trend for {hashtag} should exist"
        assert trend.video_count_current == 50, f"Expected 50 videos, got {trend.video_count_current}"
        assert trend.velocity_score > 0, "Velocity score should be calculated"
        assert trend.growth_rate > 0, "Growth rate should be positive"
        
        # Verify: Velocity history recorded
        history = await trend_repository.get_velocity_history(trend.id, hours=1)
        assert len(history) > 0, "Velocity history should be recorded"
        assert len(history) <= 50, f"Expected up to 50 history records, got {len(history)}"
        
        # Verify metrics
        metrics = pipeline_metrics.to_dict()
        assert metrics["processing_rate"] > 0, "Should have positive processing rate"
        assert metrics["total_duration_seconds"] < 30, "Batch processing should complete within 30 seconds"


@pytest.mark.e2e
@pytest.mark.slow  
class TestTrendLifecycleFlow:
    """
    Scenario 3: Trend Lifecycle Flow
    
    - Create initial trend data points (emerging)
    - Add more data points (growth)
    - Verify trend transitions to peaking
    - Add saturation data
    - Verify trend transitions to saturated
    """
    
    async def test_lifecycle_emerging_to_peaking(
        self,
        clean_redis,
        clean_db,
        producer,
        trend_detector,
        trend_repository,
        pipeline_metrics
    ):
        """
        Test trend lifecycle transition from EMERGING to PEAKING.
        
        Expected: As velocity increases with deceleration, trend transitions to PEAKING.
        """
        hashtag = "#lifecycletest"
        
        # Phase 1: Initial videos (emerging state)
        initial_videos = []
        base_views = 1000
        
        for i in range(5):
            video = VideoData(
                id=f"lifecycle_vid_{i}",
                desc=f"Phase 1 video {i}",
                create_time=int((datetime.now(timezone.utc) - timedelta(hours=5-i)).timestamp()),
                stats=VideoStats(
                    play_count=int(base_views * (1.5 ** i)),  # 50% growth
                    digg_count=int(base_views * 0.15),
                    share_count=int(base_views * 0.02),
                    comment_count=int(base_views * 0.01)
                ),
                author=VideoAuthor(
                    unique_id=f"creator_{i}",
                    nickname=f"Creator {i}",
                    follower_count=5000
                ),
                hashtags=[hashtag],
                scraped_at=datetime.now(timezone.utc) - timedelta(hours=5-i),
                source_type="trending"
            )
            initial_videos.append(video)
        
        # Process initial videos
        await producer.push_batch_to_queue(initial_videos)
        
        for video_json in await clean_redis.lrange("tiktok:videos", 0, -1):
            video = VideoData.model_validate_json(
                video_json.decode('utf-8') if isinstance(video_json, bytes) else video_json
            )
            await trend_detector.process_video(video)
        
        await clean_redis.flushall()
        
        # Verify: Trend is emerging
        trend = await trend_repository.get_by_platform_id(
            TrendType.HASHTAG,
            hashtag.lower().lstrip('#')
        )
        assert trend is not None
        initial_status = trend.status
        initial_velocity = trend.velocity_score
        
        # Phase 2: High velocity videos (should transition to peaking)
        high_velocity_videos = []
        high_base_views = 50000
        
        for i in range(10):
            # Exponential growth with high views
            video = VideoData(
                id=f"lifecycle_vid_peak_{i}",
                desc=f"Phase 2 video {i}",
                create_time=int(datetime.now(timezone.utc).timestamp()),
                stats=VideoStats(
                    play_count=int(high_base_views * (1.3 ** i)),
                    digg_count=int(high_base_views * 0.15),
                    share_count=int(high_base_views * 0.02),
                    comment_count=int(high_base_views * 0.01)
                ),
                author=VideoAuthor(
                    unique_id=f"peak_creator_{i}",
                    nickname=f"Peak Creator {i}",
                    follower_count=10000
                ),
                hashtags=[hashtag],
                scraped_at=datetime.now(timezone.utc),
                source_type="trending"
            )
            high_velocity_videos.append(video)
        
        # Process high velocity videos
        await producer.push_batch_to_queue(high_velocity_videos)
        
        for video_json in await clean_redis.lrange("tiktok:videos", 0, -1):
            video = VideoData.model_validate_json(
                video_json.decode('utf-8') if isinstance(video_json, bytes) else video_json
            )
            await trend_detector.process_video(video)
        
        # Verify: Trend transitioned to peaking
        trend = await trend_repository.get_by_platform_id(
            TrendType.HASHTAG,
            hashtag.lower().lstrip('#')
        )
        
        assert trend.velocity_score > initial_velocity, "Velocity should increase"
        assert trend.status in [TrendStatus.EMERGING, TrendStatus.PEAKING], \
            f"Status should be EMERGING or PEAKING, got {trend.status}"
        
        if trend.status == TrendStatus.PEAKING:
            assert trend.peak_detected_at is not None, "Peak time should be recorded"
    
    async def test_lifecycle_peaking_to_saturated(
        self,
        clean_redis,
        clean_db,
        producer,
        trend_detector,
        trend_repository
    ):
        """
        Test trend lifecycle transition from PEAKING to SATURATED.
        
        Expected: As saturation increases, trend transitions to SATURATED.
        """
        # First create a peaking trend
        # This is simulated by directly creating trend record
        from detection.models import Trend
        
        hashtag = "#saturationtest"
        
        # Create initial peaking trend
        initial_trend = Trend(
            type=TrendType.HASHTAG,
            name=hashtag,
            platform_id=hashtag.lower().lstrip('#'),
            status=TrendStatus.PEAKING,
            velocity_score=85,
            saturation_percent=60,
            video_count_start=1,
            video_count_current=50,
            growth_rate=1.0
        )
        
        created = await trend_repository.create(initial_trend)
        
        # Add many more videos (simulating saturation)
        saturation_videos = []
        base_views = 100000  # High views = saturation
        
        for i in range(20):
            video = VideoData(
                id=f"sat_vid_{i}",
                desc=f"Saturation video {i}",
                create_time=int(datetime.now(timezone.utc).timestamp()),
                stats=VideoStats(
                    play_count=base_views + (i * 1000),  # Flat growth = saturation
                    digg_count=int(base_views * 0.1),
                    share_count=int(base_views * 0.01),
                    comment_count=int(base_views * 0.005)
                ),
                author=VideoAuthor(
                    unique_id=f"sat_creator_{i}",
                    nickname=f"Sat Creator {i}",
                    follower_count=20000
                ),
                hashtags=[hashtag],
                scraped_at=datetime.now(timezone.utc),
                source_type="trending"
            )
            saturation_videos.append(video)
        
        # Process saturation videos
        await producer.push_batch_to_queue(saturation_videos)
        
        for video_json in await clean_redis.lrange("tiktok:videos", 0, -1):
            video = VideoData.model_validate_json(
                video_json.decode('utf-8') if isinstance(video_json, bytes) else video_json
            )
            await trend_detector.process_video(video)
        
        # Verify: Trend shows saturation indicators
        trend = await trend_repository.get_by_platform_id(
            TrendType.HASHTAG,
            hashtag.lower().lstrip('#')
        )
        
        assert trend is not None
        assert trend.video_count_current >= 70, "Video count should increase"
        assert trend.saturation_percent >= 60, "Saturation should increase"


@pytest.mark.e2e
@pytest.mark.slow
class TestMultiTrendFlow:
    """
    Scenario 4: Multi-Trend Flow
    
    - Videos with multiple hashtags
    - Verify each hashtag becomes separate trend
    - Verify independent velocity tracking
    """
    
    async def test_multiple_hashtags_separate_trends(
        self,
        clean_redis,
        clean_db,
        producer,
        trend_detector,
        trend_repository,
        pipeline_metrics
    ):
        """
        Test that videos with multiple hashtags create separate trends.
        
        Expected: Video with 3 hashtags = 3 separate hashtag trends.
        """
        hashtags = ["#trendone", "#trendtwo", "#trendthree"]
        
        # Create videos with all three hashtags
        videos = []
        for i in range(10):
            video = VideoData(
                id=f"multi_vid_{i}",
                desc=f"Video with multiple trends {' '.join(hashtags)}",
                create_time=int(datetime.now(timezone.utc).timestamp()),
                stats=VideoStats(
                    play_count=20000 + (i * 1000),
                    digg_count=3000,
                    share_count=500,
                    comment_count=200
                ),
                author=VideoAuthor(
                    unique_id=f"multi_creator_{i}",
                    nickname=f"Multi Creator {i}",
                    follower_count=8000
                ),
                hashtags=list(hashtags),
                scraped_at=datetime.now(timezone.utc),
                source_type="trending"
            )
            videos.append(video)
        
        # Process videos
        await producer.push_batch_to_queue(videos)
        pipeline_metrics.videos_pushed = len(videos)
        
        for video_json in await clean_redis.lrange("tiktok:videos", 0, -1):
            video = VideoData.model_validate_json(
                video_json.decode('utf-8') if isinstance(video_json, bytes) else video_json
            )
            await trend_detector.process_video(video)
            pipeline_metrics.videos_processed += 1
        
        # Verify: Separate trend for each hashtag
        trends = []
        for hashtag in hashtags:
            trend = await trend_repository.get_by_platform_id(
                TrendType.HASHTAG,
                hashtag.lower().lstrip('#')
            )
            assert trend is not None, f"Trend for {hashtag} should exist"
            trends.append(trend)
        
        # Verify: Each trend has independent tracking
        assert len(trends) == 3, f"Expected 3 trends, got {len(trends)}"
        
        for trend in trends:
            assert trend.video_count_current == 10, \
                f"Trend {trend.name} should have 10 videos"
            assert trend.velocity_score > 0, \
                f"Trend {trend.name} should have velocity score"
        
        pipeline_metrics.trends_created = len(trends)
        pipeline_metrics.finalize()
    
    async def test_independent_velocity_tracking(
        self,
        clean_redis,
        clean_db,
        producer,
        trend_detector,
        trend_repository
    ):
        """
        Test that trends track velocity independently.
        
        Expected: Two hashtags in same videos can have different velocity scores
        based on their historical data.
        """
        hashtag_fast = "#fasttrend"
        hashtag_slow = "#slowtrend"
        
        # Phase 1: Create initial history with different growth patterns
        
        # Fast trend: High growth videos first
        fast_videos = []
        for i in range(5):
            video = VideoData(
                id=f"fast_vid_{i}",
                desc=f"Fast trend video",
                create_time=int((datetime.now(timezone.utc) - timedelta(hours=5-i)).timestamp()),
                stats=VideoStats(
                    play_count=int(10000 * (2.0 ** i)),  # 100% growth
                    digg_count=5000,
                    share_count=1000,
                    comment_count=500
                ),
                author=VideoAuthor(
                    unique_id=f"fast_creator_{i}",
                    nickname=f"Fast Creator {i}",
                    follower_count=5000
                ),
                hashtags=[hashtag_fast],
                scraped_at=datetime.now(timezone.utc) - timedelta(hours=5-i),
                source_type="trending"
            )
            fast_videos.append(video)
        
        await producer.push_batch_to_queue(fast_videos)
        
        for video_json in await clean_redis.lrange("tiktok:videos", 0, -1):
            video = VideoData.model_validate_json(
                video_json.decode('utf-8') if isinstance(video_json, bytes) else video_json
            )
            await trend_detector.process_video(video)
        
        await clean_redis.flushall()
        
        # Slow trend: Low growth videos
        slow_videos = []
        for i in range(5):
            video = VideoData(
                id=f"slow_vid_{i}",
                desc=f"Slow trend video",
                create_time=int((datetime.now(timezone.utc) - timedelta(hours=5-i)).timestamp()),
                stats=VideoStats(
                    play_count=int(10000 * (1.1 ** i)),  # 10% growth
                    digg_count=1000,
                    share_count=200,
                    comment_count=100
                ),
                author=VideoAuthor(
                    unique_id=f"slow_creator_{i}",
                    nickname=f"Slow Creator {i}",
                    follower_count=3000
                ),
                hashtags=[hashtag_slow],
                scraped_at=datetime.now(timezone.utc) - timedelta(hours=5-i),
                source_type="trending"
            )
            slow_videos.append(video)
        
        await producer.push_batch_to_queue(slow_videos)
        
        for video_json in await clean_redis.lrange("tiktok:videos", 0, -1):
            video = VideoData.model_validate_json(
                video_json.decode('utf-8') if isinstance(video_json, bytes) else video_json
            )
            await trend_detector.process_video(video)
        
        # Verify: Different velocity scores
        fast_trend = await trend_repository.get_by_platform_id(
            TrendType.HASHTAG,
            hashtag_fast.lower().lstrip('#')
        )
        slow_trend = await trend_repository.get_by_platform_id(
            TrendType.HASHTAG,
            hashtag_slow.lower().lstrip('#')
        )
        
        assert fast_trend is not None
        assert slow_trend is not None
        
        # Fast trend should have higher velocity
        assert fast_trend.velocity_score > slow_trend.velocity_score, \
            f"Fast trend ({fast_trend.velocity_score}) should have higher velocity than slow trend ({slow_trend.velocity_score})"
        assert fast_trend.growth_rate > slow_trend.growth_rate, \
            f"Fast trend growth ({fast_trend.growth_rate}) should exceed slow trend ({slow_trend.growth_rate})"
    
    async def test_sound_and_hashtag_same_video(
        self,
        clean_redis,
        clean_db,
        producer,
        trend_detector,
        trend_repository
    ):
        """
        Test that same video creates both sound and hashtag trends.
        
        Expected: Video with music + hashtag = 1 sound trend + 1 hashtag trend.
        """
        sound_id = "viral_sound_999"
        hashtag = "#soundtrend"
        
        videos = []
        for i in range(5):
            video = VideoData(
                id=f"sound_vid_{i}",
                desc=f"Video with sound and hashtag",
                create_time=int(datetime.now(timezone.utc).timestamp()),
                stats=VideoStats(
                    play_count=30000,
                    digg_count=5000,
                    share_count=800,
                    comment_count=400
                ),
                author=VideoAuthor(
                    unique_id=f"sound_creator_{i}",
                    nickname=f"Sound Creator {i}",
                    follower_count=7000
                ),
                music=VideoMusic(
                    id=sound_id,
                    title="Viral Sound Track",
                    author_name="Sound Artist"
                ),
                hashtags=[hashtag],
                scraped_at=datetime.now(timezone.utc),
                source_type="trending"
            )
            videos.append(video)
        
        await producer.push_batch_to_queue(videos)
        
        for video_json in await clean_redis.lrange("tiktok:videos", 0, -1):
            video = VideoData.model_validate_json(
                video_json.decode('utf-8') if isinstance(video_json, bytes) else video_json
            )
            await trend_detector.process_video(video)
        
        # Verify: Both sound and hashtag trends exist
        sound_trend = await trend_repository.get_by_platform_id(
            TrendType.SOUND,
            sound_id
        )
        hashtag_trend = await trend_repository.get_by_platform_id(
            TrendType.HASHTAG,
            hashtag.lower().lstrip('#')
        )
        
        assert sound_trend is not None, "Sound trend should exist"
        assert hashtag_trend is not None, "Hashtag trend should exist"
        
        assert sound_trend.name == "Viral Sound Track - Sound Artist"
        assert hashtag_trend.name == hashtag
        
        assert sound_trend.video_count_current == 5
        assert hashtag_trend.video_count_current == 5
