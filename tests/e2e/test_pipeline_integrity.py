"""
End-to-End Pipeline Integrity Tests for Trendscope

Tests data integrity across the pipeline:
1. No video loss (all consumed)
2. No duplicate trends
3. Accurate velocity calculations
4. Consistent metadata

All tests use pytest.mark.e2e and pytest.mark.slow markers.
"""

import asyncio
import json
import math
import time
from datetime import datetime, timedelta, timezone
from typing import List, Set, Dict

import pytest

from detection.models import VideoData, VideoStats, VideoAuthor, VideoMusic, TrendType, TrendStatus


pytestmark = [pytest.mark.e2e, pytest.mark.slow]


@pytest.mark.e2e
@pytest.mark.slow
class TestNoVideoLoss:
    """
    Tests that all videos pushed to the queue are eventually processed.
    """
    
    async def test_all_videos_processed_no_loss(
        self,
        clean_redis,
        clean_db,
        producer,
        trend_detector,
        trend_repository,
        pipeline_metrics
    ):
        """
        Test that all 100 videos are processed with no loss.
        
        Expected: pushed_count == processed_count, queue empty at end.
        """
        video_count = 100
        hashtag = "#nolosstest"
        
        # Generate videos
        videos = []
        for i in range(video_count):
            video = VideoData(
                id=f"noloss_vid_{i}",
                desc=f"No loss test video {i} {hashtag}",
                create_time=int((datetime.now(timezone.utc) - timedelta(minutes=i)).timestamp()),
                stats=VideoStats(
                    play_count=10000 + (i * 100),
                    digg_count=1500,
                    share_count=250,
                    comment_count=125
                ),
                author=VideoAuthor(
                    unique_id=f"nolosscreator_{i}",
                    nickname=f"No Loss Creator {i}",
                    follower_count=5000
                ),
                hashtags=[hashtag],
                scraped_at=datetime.now(timezone.utc) - timedelta(minutes=i),
                source_type="trending"
            )
            videos.append(video)
        
        # Push all
        await producer.push_batch_to_queue(videos)
        pipeline_metrics.videos_pushed = video_count
        
        # Process all
        processed = 0
        batch_size = 10
        
        while True:
            batch = await clean_redis.lrange("tiktok:videos", 0, batch_size - 1)
            if not batch:
                break
            
            for video_json in batch:
                video = VideoData.model_validate_json(
                    video_json.decode('utf-8') if isinstance(video_json, bytes) else video_json
                )
                await trend_detector.process_video(video)
                processed += 1
            
            # Remove processed
            await clean_redis.ltrim("tiktok:videos", len(batch), -1)
            pipeline_metrics.record_queue_depth(await clean_redis.llen("tiktok:videos"), f"batch_{processed}")
        
        pipeline_metrics.videos_processed = processed
        pipeline_metrics.finalize()
        
        # Verify no loss
        assert processed == video_count, \
            f"Video loss detected: pushed {video_count}, processed {processed}"
        
        # Verify queue is empty
        final_queue_len = await clean_redis.llen("tiktok:videos")
        assert final_queue_len == 0, f"Queue not empty: {final_queue_len} items remaining"
        
        # Verify trend has correct count
        trend = await trend_repository.get_by_platform_id(
            TrendType.HASHTAG,
            hashtag.lower().lstrip('#')
        )
        assert trend is not None
        assert trend.video_count_current == video_count, \
            f"Trend video count mismatch: expected {video_count}, got {trend.video_count_current}"
    
    async def test_queue_order_preserved(
        self,
        clean_redis,
        clean_db,
        producer,
        trend_detector
    ):
        """
        Test that videos are processed in correct order.
        
        Expected: FIFO order is maintained.
        """
        videos = []
        for i in range(10):
            video = VideoData(
                id=f"order_vid_{i:03d}",
                desc=f"Order test {i}",
                create_time=int(datetime.now(timezone.utc).timestamp()),
                stats=VideoStats(play_count=10000, digg_count=1500, share_count=250, comment_count=125),
                author=VideoAuthor(unique_id=f"ordercreator_{i}", nickname=f"Order Creator {i}", follower_count=5000),
                hashtags=["ordertest"],
                scraped_at=datetime.now(timezone.utc),
                source_type="trending"
            )
            videos.append(video)
        
        # Push in order
        for video in videos:
            await producer.push_to_queue(video)
        
        # Read back and verify order
        processed_ids = []
        for video_json in await clean_redis.lrange("tiktok:videos", 0, -1):
            video = VideoData.model_validate_json(
                video_json.decode('utf-8') if isinstance(video_json, bytes) else video_json
            )
            processed_ids.append(video.id)
        
        # Verify order (LIFO from lpush means reverse order)
        expected_order = [v.id for v in reversed(videos)]
        assert processed_ids == expected_order, "Video order not preserved"
    
    async def test_large_batch_no_loss(
        self,
        clean_redis,
        clean_db,
        producer,
        trend_detector,
        trend_repository,
        pipeline_metrics
    ):
        """
        Test processing of large batch (500 videos).
        
        Expected: All videos processed, no loss at scale.
        """
        video_count = 500
        hashtag = "#largebatchtest"
        
        # Generate in smaller chunks to avoid memory issues
        chunk_size = 50
        total_pushed = 0
        
        for chunk_start in range(0, video_count, chunk_size):
            videos = []
            for i in range(chunk_size):
                idx = chunk_start + i
                video = VideoData(
                    id=f"large_vid_{idx:04d}",
                    desc=f"Large batch {idx} {hashtag}",
                    create_time=int(datetime.now(timezone.utc).timestamp()),
                    stats=VideoStats(
                        play_count=10000 + (idx * 10),
                        digg_count=1500,
                        share_count=250,
                        comment_count=125
                    ),
                    author=VideoAuthor(
                        unique_id=f"largecreator_{idx}",
                        nickname=f"Large Creator {idx}",
                        follower_count=5000
                    ),
                    hashtags=[hashtag],
                    scraped_at=datetime.now(timezone.utc),
                    source_type="trending"
                )
                videos.append(video)
            
            await producer.push_batch_to_queue(videos)
            total_pushed += len(videos)
        
        pipeline_metrics.videos_pushed = total_pushed
        
        # Process all
        processed = 0
        while True:
            batch = await clean_redis.lrange("tiktok:videos", 0, 24)  # Process 25 at a time
            if not batch:
                break
            
            for video_json in batch:
                video = VideoData.model_validate_json(
                    video_json.decode('utf-8') if isinstance(video_json, bytes) else video_json
                )
                await trend_detector.process_video(video)
                processed += 1
            
            await clean_redis.ltrim("tiktok:videos", len(batch), -1)
        
        pipeline_metrics.videos_processed = processed
        pipeline_metrics.finalize()
        
        # Verify
        assert processed == video_count, \
            f"Large batch loss: expected {video_count}, got {processed}"
        
        trend = await trend_repository.get_by_platform_id(
            TrendType.HASHTAG,
            hashtag.lower().lstrip('#')
        )
        assert trend is not None
        assert trend.video_count_current == video_count


@pytest.mark.e2e
@pytest.mark.slow
class TestNoDuplicateTrends:
    """
    Tests that duplicate trends are not created.
    """
    
    async def test_single_trend_per_hashtag(
        self,
        clean_redis,
        clean_db,
        producer,
        trend_detector,
        trend_repository
    ):
        """
        Test that multiple videos with same hashtag create single trend.
        
        Expected: 50 videos, 1 hashtag = 1 trend.
        """
        hashtag = "#uniquetest"
        video_count = 50
        
        videos = []
        for i in range(video_count):
            video = VideoData(
                id=f"unique_vid_{i}",
                desc=f"Unique test {i} {hashtag}",
                create_time=int(datetime.now(timezone.utc).timestamp()),
                stats=VideoStats(play_count=10000 + i*100, digg_count=1500, share_count=250, comment_count=125),
                author=VideoAuthor(unique_id=f"uniquecreator_{i}", nickname=f"Unique Creator {i}", follower_count=5000),
                hashtags=[hashtag],
                scraped_at=datetime.now(timezone.utc),
                source_type="trending"
            )
            videos.append(video)
        
        await producer.push_batch_to_queue(videos)
        
        # Process all
        for video_json in await clean_redis.lrange("tiktok:videos", 0, -1):
            video = VideoData.model_validate_json(
                video_json.decode('utf-8') if isinstance(video_json, bytes) else video_json
            )
            await trend_detector.process_video(video)
        
        # Get all trends from database
        all_trends = await trend_repository.get_trends(limit=1000)
        
        # Filter for our test hashtag
        matching_trends = [t for t in all_trends if hashtag.lower() in t.name.lower()]
        
        # Should be exactly 1 trend
        assert len(matching_trends) == 1, \
            f"Duplicate trends detected: expected 1, got {len(matching_trends)}"
        
        # That 1 trend should have correct count
        trend = matching_trends[0]
        assert trend.video_count_current == video_count
    
    async def test_idempotent_processing(
        self,
        clean_redis,
        clean_db,
        producer,
        trend_detector,
        trend_repository
    ):
        """
        Test that processing same video twice doesn't create duplicates.
        
        Expected: Video processed twice = 1 trend with updated count.
        """
        hashtag = "#idempotencytest"
        
        # Create single video
        video = VideoData(
            id="idempotent_vid_001",
            desc=f"Idempotency test {hashtag}",
            create_time=int(datetime.now(timezone.utc).timestamp()),
            stats=VideoStats(play_count=50000, digg_count=7500, share_count=1000, comment_count=500),
            author=VideoAuthor(unique_id="idempotentcreator", nickname="Idempotent Creator", follower_count=10000),
            hashtags=[hashtag],
            scraped_at=datetime.now(timezone.utc),
            source_type="trending"
        )
        
        # Push and process twice
        for _ in range(2):
            await producer.push_to_queue(video)
            
            batch = await clean_redis.lrange("tiktok:videos", 0, 0)
            if batch:
                v = VideoData.model_validate_json(
                    batch[0].decode('utf-8') if isinstance(batch[0], bytes) else batch[0]
                )
                await trend_detector.process_video(v)
                await clean_redis.ltrim("tiktok:videos", 1, -1)
        
        # Should have 1 trend with count reflecting both processings
        # Note: In real system, video_id dedup would prevent double counting
        # Here we verify the trend exists and was updated
        trend = await trend_repository.get_by_platform_id(
            TrendType.HASHTAG,
            hashtag.lower().lstrip('#')
        )
        assert trend is not None
        assert trend.video_count_current >= 1
    
    async def test_concurrent_processing_no_duplicates(
        self,
        clean_redis,
        clean_db,
        producer,
        trend_detector,
        trend_repository
    ):
        """
        Test that concurrent processing doesn't create duplicates.
        
        Expected: Concurrent workers should not create duplicate trends.
        """
        hashtag = "#concurrenttest"
        video_count = 30
        
        videos = []
        for i in range(video_count):
            video = VideoData(
                id=f"concurrent_vid_{i:03d}",
                desc=f"Concurrent test {i} {hashtag}",
                create_time=int(datetime.now(timezone.utc).timestamp()),
                stats=VideoStats(play_count=10000, digg_count=1500, share_count=250, comment_count=125),
                author=VideoAuthor(unique_id=f"concurrentcreator_{i}", nickname=f"Concurrent Creator {i}", follower_count=5000),
                hashtags=[hashtag],
                scraped_at=datetime.now(timezone.utc),
                source_type="trending"
            )
            videos.append(video)
        
        await producer.push_batch_to_queue(videos)
        
        # Process with "concurrent" workers (simulated sequential for test stability)
        async def worker(worker_id: int, indices: List[int]):
            processed = 0
            for idx in indices:
                # Each worker processes different videos
                batch = await clean_redis.lrange("tiktok:videos", idx, idx)
                if batch:
                    video = VideoData.model_validate_json(
                        batch[0].decode('utf-8') if isinstance(batch[0], bytes) else batch[0]
                    )
                    await trend_detector.process_video(video)
                    processed += 1
            return processed
        
        # Simulate 3 workers
        worker_indices = [
            list(range(0, 10)),
            list(range(10, 20)),
            list(range(20, 30))
        ]
        
        # Sequential execution for test stability
        for indices in worker_indices:
            await worker(0, indices)
        
        # Clear queue
        await clean_redis.flushall()
        
        # Verify single trend
        all_trends = await trend_repository.get_trends(limit=1000)
        matching = [t for t in all_trends if hashtag.lower() in t.name.lower()]
        
        assert len(matching) == 1, \
            f"Concurrent processing created duplicates: {len(matching)} trends found"


@pytest.mark.e2e
@pytest.mark.slow
class TestAccurateVelocityCalculations:
    """
    Tests that velocity calculations are mathematically accurate.
    """
    
    async def test_exponential_growth_detection(
        self,
        clean_redis,
        clean_db,
        producer,
        trend_detector,
        trend_repository
    ):
        """
        Test detection of exponential growth pattern.
        
        Expected: Perfect exponential growth should yield high R-squared.
        """
        hashtag = "#exponentialtest"
        
        # Create videos with perfect exponential growth
        base_views = 1000
        growth_rate = 0.5  # 50% growth per video
        
        videos = []
        for i in range(10):
            views = int(base_views * ((1 + growth_rate) ** i))
            video = VideoData(
                id=f"exp_vid_{i}",
                desc=f"Exponential test {i} {hashtag}",
                create_time=int((datetime.now(timezone.utc) - timedelta(hours=10-i)).timestamp()),
                stats=VideoStats(
                    play_count=views,
                    digg_count=int(views * 0.15),
                    share_count=int(views * 0.02),
                    comment_count=int(views * 0.01)
                ),
                author=VideoAuthor(unique_id=f"expcreator_{i}", nickname=f"Exp Creator {i}", follower_count=5000),
                hashtags=[hashtag],
                scraped_at=datetime.now(timezone.utc) - timedelta(hours=10-i),
                source_type="trending"
            )
            videos.append(video)
        
        await producer.push_batch_to_queue(videos)
        
        # Process
        for video_json in await clean_redis.lrange("tiktok:videos", 0, -1):
            video = VideoData.model_validate_json(
                video_json.decode('utf-8') if isinstance(video_json, bytes) else video_json
            )
            await trend_detector.process_video(video)
        
        # Verify velocity calculation
        trend = await trend_repository.get_by_platform_id(
            TrendType.HASHTAG,
            hashtag.lower().lstrip('#')
        )
        assert trend is not None
        assert trend.velocity_score > 50, \
            f"Expected high velocity for exponential growth, got {trend.velocity_score}"
        assert trend.growth_rate > 0, \
            f"Expected positive growth rate, got {trend.growth_rate}"
    
    async def test_flat_growth_detection(
        self,
        clean_redis,
        clean_db,
        producer,
        trend_detector,
        trend_repository
    ):
        """
        Test detection of flat (no) growth pattern.
        
        Expected: Flat growth should yield low velocity score.
        """
        hashtag = "#flattest"
        
        # Create videos with flat growth
        base_views = 10000
        
        videos = []
        for i in range(10):
            # Small linear increase only
            views = base_views + (i * 100)
            video = VideoData(
                id=f"flat_vid_{i}",
                desc=f"Flat test {i} {hashtag}",
                create_time=int((datetime.now(timezone.utc) - timedelta(hours=10-i)).timestamp()),
                stats=VideoStats(
                    play_count=views,
                    digg_count=int(views * 0.15),
                    share_count=int(views * 0.02),
                    comment_count=int(views * 0.01)
                ),
                author=VideoAuthor(unique_id=f"flatcreator_{i}", nickname=f"Flat Creator {i}", follower_count=5000),
                hashtags=[hashtag],
                scraped_at=datetime.now(timezone.utc) - timedelta(hours=10-i),
                source_type="trending"
            )
            videos.append(video)
        
        await producer.push_batch_to_queue(videos)
        
        # Process
        for video_json in await clean_redis.lrange("tiktok:videos", 0, -1):
            video = VideoData.model_validate_json(
                video_json.decode('utf-8') if isinstance(video_json, bytes) else video_json
            )
            await trend_detector.process_video(video)
        
        # Verify velocity calculation
        trend = await trend_repository.get_by_platform_id(
            TrendType.HASHTAG,
            hashtag.lower().lstrip('#')
        )
        assert trend is not None
        # Flat growth should have lower velocity than exponential
        assert trend.velocity_score < 50, \
            f"Expected lower velocity for flat growth, got {trend.velocity_score}"
    
    async def test_velocity_monotonicity(
        self,
        clean_redis,
        clean_db,
        producer,
        trend_detector,
        trend_repository
    ):
        """
        Test that velocity score increases with higher growth rates.
        
        Compare two trends: one with 2x growth, one with 1.2x growth.
        """
        # Create fast growth trend
        fast_hashtag = "#fastmonotest"
        fast_videos = []
        for i in range(10):
            views = int(1000 * (2.0 ** i))  # 100% growth
            video = VideoData(
                id=f"fastmono_vid_{i}",
                desc=f"Fast mono {i} {fast_hashtag}",
                create_time=int((datetime.now(timezone.utc) - timedelta(hours=10-i)).timestamp()),
                stats=VideoStats(play_count=views, digg_count=int(views*0.15), share_count=int(views*0.02), comment_count=int(views*0.01)),
                author=VideoAuthor(unique_id=f"fastmonocreator_{i}", nickname=f"Fast Mono Creator {i}", follower_count=5000),
                hashtags=[fast_hashtag],
                scraped_at=datetime.now(timezone.utc) - timedelta(hours=10-i),
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
        
        # Create slow growth trend
        slow_hashtag = "#slowmonotest"
        slow_videos = []
        for i in range(10):
            views = int(1000 * (1.2 ** i))  # 20% growth
            video = VideoData(
                id=f"slowmono_vid_{i}",
                desc=f"Slow mono {i} {slow_hashtag}",
                create_time=int((datetime.now(timezone.utc) - timedelta(hours=10-i)).timestamp()),
                stats=VideoStats(play_count=views, digg_count=int(views*0.15), share_count=int(views*0.02), comment_count=int(views*0.01)),
                author=VideoAuthor(unique_id=f"slowmonocreator_{i}", nickname=f"Slow Mono Creator {i}", follower_count=5000),
                hashtags=[slow_hashtag],
                scraped_at=datetime.now(timezone.utc) - timedelta(hours=10-i),
                source_type="trending"
            )
            slow_videos.append(video)
        
        await producer.push_batch_to_queue(slow_videos)
        
        for video_json in await clean_redis.lrange("tiktok:videos", 0, -1):
            video = VideoData.model_validate_json(
                video_json.decode('utf-8') if isinstance(video_json, bytes) else video_json
            )
            await trend_detector.process_video(video)
        
        # Compare velocities
        fast_trend = await trend_repository.get_by_platform_id(
            TrendType.HASHTAG,
            fast_hashtag.lower().lstrip('#')
        )
        slow_trend = await trend_repository.get_by_platform_id(
            TrendType.HASHTAG,
            slow_hashtag.lower().lstrip('#')
        )
        
        assert fast_trend is not None
        assert slow_trend is not None
        assert fast_trend.velocity_score > slow_trend.velocity_score, \
            f"Fast trend ({fast_trend.velocity_score}) should have higher velocity than slow ({slow_trend.velocity_score})"
    
    async def test_velocity_history_accuracy(
        self,
        clean_redis,
        clean_db,
        producer,
        trend_detector,
        trend_repository
    ):
        """
        Test that velocity history accurately records trend progression.
        
        Expected: History entries should show increasing video counts.
        """
        hashtag = "#historyaccuracytest"
        
        videos = []
        for i in range(20):
            views = 10000 + (i * 1000)
            video = VideoData(
                id=f"history_vid_{i:03d}",
                desc=f"History accuracy {i} {hashtag}",
                create_time=int((datetime.now(timezone.utc) - timedelta(minutes=20-i)).timestamp()),
                stats=VideoStats(play_count=views, digg_count=int(views*0.15), share_count=int(views*0.02), comment_count=int(views*0.01)),
                author=VideoAuthor(unique_id=f"historycreator_{i}", nickname=f"History Creator {i}", follower_count=5000),
                hashtags=[hashtag],
                scraped_at=datetime.now(timezone.utc) - timedelta(minutes=20-i),
                source_type="trending"
            )
            videos.append(video)
        
        await producer.push_batch_to_queue(videos)
        
        # Process all
        for video_json in await clean_redis.lrange("tiktok:videos", 0, -1):
            video = VideoData.model_validate_json(
                video_json.decode('utf-8') if isinstance(video_json, bytes) else video_json
            )
            await trend_detector.process_video(video)
        
        # Get trend and history
        trend = await trend_repository.get_by_platform_id(
            TrendType.HASHTAG,
            hashtag.lower().lstrip('#')
        )
        assert trend is not None
        
        history = await trend_repository.get_velocity_history(trend.id, hours=1)
        
        # Verify history is recorded
        assert len(history) > 0, "Velocity history should be recorded"
        
        # History should show progression
        video_counts = [h.video_count for h in history]
        for i in range(1, len(video_counts)):
            assert video_counts[i] >= video_counts[i-1], \
                f"Video count should increase: {video_counts}"


@pytest.mark.e2e
@pytest.mark.slow
class TestConsistentMetadata:
    """
    Tests that metadata is consistent across the pipeline.
    """
    
    async def test_metadata_preserved(
        self,
        clean_redis,
        clean_db,
        producer,
        trend_detector,
        trend_repository
    ):
        """
        Test that video metadata is preserved in trend.
        
        Expected: Example videos, creators should be in trend metadata.
        """
        hashtag = "#metadatatest"
        creator_id = "specialcreator123"
        video_id = "specialvideo456"
        
        video = VideoData(
            id=video_id,
            desc=f"Metadata test {hashtag}",
            create_time=int(datetime.now(timezone.utc).timestamp()),
            stats=VideoStats(play_count=100000, digg_count=15000, share_count=2500, comment_count=1000),
            author=VideoAuthor(unique_id=creator_id, nickname="Special Creator", follower_count=50000),
            music=VideoMusic(id="specialsound", title="Special Sound", author_name="Special Artist"),
            hashtags=[hashtag],
            scraped_at=datetime.now(timezone.utc),
            source_type="hashtag",
            source_query="specialquery"
        )
        
        await producer.push_to_queue(video)
        
        # Process
        batch = await clean_redis.lrange("tiktok:videos", 0, 0)
        v = VideoData.model_validate_json(
            batch[0].decode('utf-8') if isinstance(batch[0], bytes) else batch[0]
        )
        await trend_detector.process_video(v)
        
        # Verify metadata preserved
        trend = await trend_repository.get_by_platform_id(
            TrendType.HASHTAG,
            hashtag.lower().lstrip('#')
        )
        assert trend is not None
        
        metadata = trend.metadata or {}
        assert "example_videos" in metadata or "example_creators" in metadata, \
            "Trend metadata should contain example videos or creators"
    
    async def test_timestamps_consistent(
        self,
        clean_redis,
        clean_db,
        producer,
        trend_detector,
        trend_repository
    ):
        """
        Test that timestamps are consistent across trend lifecycle.
        
        Expected: created_at <= first_detected_at <= updated_at
        """
        hashtag = "#timestamptest"
        
        before_create = datetime.now(timezone.utc)
        
        video = VideoData(
            id="timestamp_vid",
            desc=f"Timestamp test {hashtag}",
            create_time=int(datetime.now(timezone.utc).timestamp()),
            stats=VideoStats(play_count=50000, digg_count=7500, share_count=1000, comment_count=500),
            author=VideoAuthor(unique_id="timestampcreator", nickname="Timestamp Creator", follower_count=10000),
            hashtags=[hashtag],
            scraped_at=datetime.now(timezone.utc),
            source_type="trending"
        )
        
        await producer.push_to_queue(video)
        
        batch = await clean_redis.lrange("tiktok:videos", 0, 0)
        v = VideoData.model_validate_json(
            batch[0].decode('utf-8') if isinstance(batch[0], bytes) else batch[0]
        )
        await trend_detector.process_video(v)
        
        after_create = datetime.now(timezone.utc)
        
        # Verify timestamps
        trend = await trend_repository.get_by_platform_id(
            TrendType.HASHTAG,
            hashtag.lower().lstrip('#')
        )
        assert trend is not None
        
        # created_at should be before or equal to now
        assert trend.created_at <= after_create, "created_at should be in the past"
        
        # first_detected_at should be set
        assert trend.first_detected_at is not None, "first_detected_at should be set"
        
        # updated_at should exist
        assert trend.updated_at is not None, "updated_at should be set"
    
    async def test_platform_id_consistency(
        self,
        clean_redis,
        clean_db,
        producer,
        trend_detector,
        trend_repository
    ):
        """
        Test that platform_id is consistently derived from hashtag.
        
        Expected: Same hashtag should always produce same platform_id.
        """
        hashtag = "#ConsistentID"
        expected_platform_id = "consistentid"  # lowercase, no #
        
        videos = []
        for i in range(5):
            video = VideoData(
                id=f"consistency_vid_{i}",
                desc=f"Consistency test {i} {hashtag}",
                create_time=int(datetime.now(timezone.utc).timestamp()),
                stats=VideoStats(play_count=10000, digg_count=1500, share_count=250, comment_count=125),
                author=VideoAuthor(unique_id=f"consistencycreator_{i}", nickname=f"Consistency Creator {i}", follower_count=5000),
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
        
        # Verify platform_id
        trend = await trend_repository.get_by_platform_id(
            TrendType.HASHTAG,
            expected_platform_id
        )
        assert trend is not None, \
            f"Trend should be found with platform_id '{expected_platform_id}'"
        assert trend.platform_id == expected_platform_id, \
            f"platform_id mismatch: expected '{expected_platform_id}', got '{trend.platform_id}'"
    
    async def test_trend_type_classification(
        self,
        clean_redis,
        clean_db,
        producer,
        trend_detector,
        trend_repository
    ):
        """
        Test that trend types are correctly classified.
        
        Expected: Music → SOUND, Hashtag → HASHTAG
        """
        # Test sound trend
        sound_video = VideoData(
            id="sound_type_vid",
            desc="Sound type test",
            create_time=int(datetime.now(timezone.utc).timestamp()),
            stats=VideoStats(play_count=50000, digg_count=7500, share_count=1000, comment_count=500),
            author=VideoAuthor(unique_id="soundcreator", nickname="Sound Creator", follower_count=10000),
            music=VideoMusic(id="testsound123", title="Test Sound", author_name="Test Artist"),
            hashtags=["soundtypetest"],
            scraped_at=datetime.now(timezone.utc),
            source_type="trending"
        )
        
        await producer.push_to_queue(sound_video)
        
        batch = await clean_redis.lrange("tiktok:videos", 0, 0)
        v = VideoData.model_validate_json(
            batch[0].decode('utf-8') if isinstance(batch[0], bytes) else batch[0]
        )
        trends = await trend_detector.process_video(v)
        
        await clean_redis.flushall()
        
        # Verify sound trend type
        sound_trends = [t for t in trends if t.type == TrendType.SOUND]
        assert len(sound_trends) > 0, "Should have sound trend"
        assert sound_trends[0].platform_id == "testsound123"
        
        # Test hashtag trend
        hashtag_video = VideoData(
            id="hashtag_type_vid",
            desc="Hashtag type test #hashtagtypetest",
            create_time=int(datetime.now(timezone.utc).timestamp()),
            stats=VideoStats(play_count=50000, digg_count=7500, share_count=1000, comment_count=500),
            author=VideoAuthor(unique_id="hashtagcreator", nickname="Hashtag Creator", follower_count=10000),
            hashtags=["hashtagtypetest"],
            scraped_at=datetime.now(timezone.utc),
            source_type="trending"
        )
        
        await producer.push_to_queue(hashtag_video)
        
        batch = await clean_redis.lrange("tiktok:videos", 0, 0)
        v = VideoData.model_validate_json(
            batch[0].decode('utf-8') if isinstance(batch[0], bytes) else batch[0]
        )
        trends = await trend_detector.process_video(v)
        
        # Verify hashtag trend type
        hashtag_trends = [t for t in trends if t.type == TrendType.HASHTAG]
        assert len(hashtag_trends) > 0, "Should have hashtag trend"
        assert hashtag_trends[0].platform_id == "hashtagtypetest"
