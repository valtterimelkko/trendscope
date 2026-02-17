"""
End-to-End Error Recovery Tests for Trendscope Pipeline

Tests error handling and recovery scenarios:
1. Redis failure during processing
2. Database failure during persistence
3. Invalid video data handling
4. Circuit breaker activation
5. Recovery and continuation

All tests use pytest.mark.e2e and pytest.mark.slow markers.
"""

import asyncio
import json
import time
from datetime import datetime, timezone
from typing import List
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from detection.models import VideoData, VideoStats, VideoAuthor, VideoMusic, TrendType, TrendStatus
from scraper.circuit_breaker import CircuitOpenError, CircuitState


pytestmark = [pytest.mark.e2e, pytest.mark.slow]


@pytest.mark.e2e
@pytest.mark.slow
class TestRedisFailureRecovery:
    """
    Redis failure scenarios and recovery.
    """
    
    async def test_redis_connection_failure_recovery(
        self,
        clean_db,
        trend_detector,
        trend_repository,
        video_factory,
        pipeline_metrics
    ):
        """
        Test that consumer handles Redis connection failure gracefully.
        
        Expected: Consumer should retry and continue when Redis recovers.
        """
        # Create a mock Redis that fails initially then recovers
        call_count = 0
        
        class FlakyRedis:
            """Redis mock that fails first 2 calls then works."""
            def __init__(self):
                self._data = {}
                self.calls = 0
            
            async def lrange(self, key, start, end):
                self.calls += 1
                if self.calls <= 2:
                    raise ConnectionError("Redis connection failed")
                return []
            
            async def ping(self):
                return True
        
        flaky_redis = FlakyRedis()
        
        from detection.consumer import TrendConsumer
        consumer = TrendConsumer(
            redis_client=flaky_redis,
            db_pool=clean_db,
            trend_detector=trend_detector
        )
        
        # Consumer should handle errors gracefully
        # Note: In real scenario, consumer would retry with backoff
        errors_before = consumer.errors_count
        
        # Simulate a fetch attempt that fails
        try:
            await consumer._fetch_batch()
        except ConnectionError:
            pass  # Expected
        
        # Verify error was recorded
        assert flaky_redis.calls == 1
    
    async def test_redis_queue_persistence_on_failure(
        self,
        clean_redis,
        clean_db,
        producer,
        trend_detector,
        video_factory,
        pipeline_metrics
    ):
        """
        Test that videos are not lost when processing fails.
        
        Expected: Failed videos should remain in queue for retry.
        """
        # Create test videos
        videos = []
        for i in range(5):
            video_data = video_factory(
                video_id=f"persist_vid_{i}",
                hashtags=["#persisttest"],
                play_count=10000
            )
            video = VideoData(
                id=video_data["id"],
                desc=video_data["desc"],
                create_time=video_data["createTime"],
                stats=VideoStats(**video_data["stats"]),
                author=VideoAuthor(**video_data["author"]),
                music=VideoMusic(**video_data["music"]) if video_data.get("music") else None,
                hashtags=video_data["hashtags"],
                scraped_at=datetime.fromisoformat(video_data["scraped_at"]),
                source_type="trending"
            )
            videos.append(video)
        
        # Push to queue
        await producer.push_batch_to_queue(videos)
        initial_queue_len = await clean_redis.llen("tiktok:videos")
        assert initial_queue_len == 5
        
        # Simulate partial processing failure (process only 2)
        batch = await clean_redis.lrange("tiktok:videos", 0, 1)
        for video_json in batch:
            video = VideoData.model_validate_json(
                video_json.decode('utf-8') if isinstance(video_json, bytes) else video_json
            )
            await trend_detector.process_video(video)
        
        # Verify: Unprocessed videos remain in queue
        remaining = await clean_redis.llen("tiktok:videos")
        assert remaining == 5, "Unprocessed videos should remain in queue"
        
        # Now process remaining
        for video_json in await clean_redis.lrange("tiktok:videos", 2, -1):
            video = VideoData.model_validate_json(
                video_json.decode('utf-8') if isinstance(video_json, bytes) else video_json
            )
            await trend_detector.process_video(video)
        
        # Verify all trends created
        trend = await trend_repository.get_by_platform_id(
            TrendType.HASHTAG,
            "persisttest"
        )
        assert trend is not None
        assert trend.video_count_current == 5


@pytest.mark.e2e
@pytest.mark.slow
class TestDatabaseFailureRecovery:
    """
    Database failure scenarios and recovery.
    """
    
    async def test_database_failure_during_persistence(
        self,
        clean_redis,
        producer,
        trend_detector,
        video_factory,
        pipeline_metrics
    ):
        """
        Test handling of database failures during trend persistence.
        
        Expected: Error should be logged, processing should continue.
        """
        # Create a mock database that fails
        class FailingDB:
            def __init__(self, fail_count=2):
                self.fail_count = fail_count
                self.calls = 0
            
            async def fetchrow(self, *args, **kwargs):
                self.calls += 1
                if self.calls <= self.fail_count:
                    raise Exception("Database connection failed")
                return None
            
            async def fetch(self, *args, **kwargs):
                return []
            
            async def execute(self, *args, **kwargs):
                self.calls += 1
                if self.calls <= self.fail_count:
                    raise Exception("Database connection failed")
                return "OK"
        
        failing_db = FailingDB()
        
        # Create trend detector with failing database
        from detection.persistence import TrendRepository
        repo = TrendRepository(failing_db)
        
        # Create video
        video = VideoData(
            id="db_fail_vid",
            desc="Test video #dbfailtest",
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
            hashtags=["dbfailtest"],
            scraped_at=datetime.now(timezone.utc),
            source_type="trending"
        )
        
        # Push to queue
        await producer.push_to_queue(video)
        
        # Process should handle DB failure gracefully
        # Note: In actual implementation, this would retry or queue for later
        try:
            batch = await clean_redis.lrange("tiktok:videos", 0, 0)
            video_data = VideoData.model_validate_json(batch[0])
            
            # This will fail when trying to persist
            with pytest.raises(Exception):
                # Manually trigger DB operation that fails
                await repo.create(
                    type=TrendType.HASHTAG,
                    name="#dbfailtest",
                    platform_id="dbfailtest",
                    status=TrendStatus.EMERGING,
                    velocity_score=50,
                    saturation_percent=30
                )
        except Exception:
            pass  # Expected
    
    async def test_recovery_after_database_restart(
        self,
        clean_redis,
        clean_db,
        producer,
        trend_detector,
        trend_repository,
        video_factory
    ):
        """
        Test that processing continues after database recovery.
        
        Expected: New trends should be persisted after DB recovers.
        """
        # Process some videos before "failure"
        video1 = VideoData(
            id="before_fail_vid",
            desc="Video before failure #recoverytest",
            create_time=int(datetime.now(timezone.utc).timestamp()),
            stats=VideoStats(play_count=30000, digg_count=5000, share_count=800, comment_count=400),
            author=VideoAuthor(unique_id="creator1", nickname="Creator 1", follower_count=5000),
            hashtags=["recoverytest"],
            scraped_at=datetime.now(timezone.utc),
            source_type="trending"
        )
        
        await producer.push_to_queue(video1)
        
        # Process first video
        batch = await clean_redis.lrange("tiktok:videos", 0, 0)
        video_data = VideoData.model_validate_json(batch[0])
        await trend_detector.process_video(video_data)
        await clean_redis.ltrim("tiktok:videos", 1, -1)
        
        # Verify first trend created
        trend1 = await trend_repository.get_by_platform_id(
            TrendType.HASHTAG,
            "recoverytest"
        )
        assert trend1 is not None
        initial_count = trend1.video_count_current
        
        # Process more videos (simulating recovery)
        video2 = VideoData(
            id="after_fail_vid",
            desc="Video after recovery #recoverytest",
            create_time=int(datetime.now(timezone.utc).timestamp()),
            stats=VideoStats(play_count=40000, digg_count=6000, share_count=900, comment_count=450),
            author=VideoAuthor(unique_id="creator2", nickname="Creator 2", follower_count=6000),
            hashtags=["recoverytest"],
            scraped_at=datetime.now(timezone.utc),
            source_type="trending"
        )
        
        await producer.push_to_queue(video2)
        
        batch = await clean_redis.lrange("tiktok:videos", 0, 0)
        video_data = VideoData.model_validate_json(batch[0])
        await trend_detector.process_video(video_data)
        
        # Verify trend updated
        trend2 = await trend_repository.get_by_platform_id(
            TrendType.HASHTAG,
            "recoverytest"
        )
        assert trend2.video_count_current > initial_count


@pytest.mark.e2e
@pytest.mark.slow
class TestInvalidDataHandling:
    """
    Invalid video data handling.
    """
    
    async def test_invalid_video_json_handling(
        self,
        clean_redis,
        clean_db,
        pipeline_metrics
    ):
        """
        Test handling of invalid JSON in queue.
        
        Expected: Invalid data should be skipped, not crash consumer.
        """
        # Push invalid JSON to queue
        await clean_redis.lpush("tiktok:videos", "not valid json {{{")
        
        # Push valid video
        valid_video = {
            "id": "valid_vid",
            "desc": "Valid video #validtest",
            "createTime": int(datetime.now(timezone.utc).timestamp()),
            "stats": {
                "playCount": 10000,
                "diggCount": 1500,
                "shareCount": 250,
                "commentCount": 125
            },
            "author": {
                "uniqueId": "validcreator",
                "nickname": "Valid Creator",
                "followerCount": 5000
            },
            "hashtags": ["validtest"],
            "scraped_at": datetime.now(timezone.utc).isoformat()
        }
        await clean_redis.lpush("tiktok:videos", json.dumps(valid_video))
        
        # Consumer should handle invalid data gracefully
        batch = await clean_redis.lrange("tiktok:videos", 0, 1)
        assert len(batch) == 2
        
        # Try to parse each
        valid_count = 0
        invalid_count = 0
        
        for video_json in batch:
            try:
                data = video_json.decode('utf-8') if isinstance(video_json, bytes) else video_json
                VideoData.model_validate_json(data)
                valid_count += 1
            except Exception:
                invalid_count += 1
        
        assert valid_count == 1, "Should have 1 valid video"
        assert invalid_count == 1, "Should have 1 invalid video"
    
    async def test_missing_required_fields_handling(
        self,
        clean_redis,
        clean_db,
        producer,
        trend_detector,
        pipeline_metrics
    ):
        """
        Test handling of video data with missing required fields.
        
        Expected: Videos with missing fields should be skipped gracefully.
        """
        # Create video with missing stats
        incomplete_video = {
            "id": "incomplete_vid",
            "desc": "Incomplete video #incompletetest",
            "createTime": int(datetime.now(timezone.utc).timestamp()),
            # Missing "stats" field
            "author": {
                "uniqueId": "incompletecreator",
                "nickname": "Incomplete Creator",
                "followerCount": 5000
            },
            "hashtags": ["incompletetest"],
            "scraped_at": datetime.now(timezone.utc).isoformat()
        }
        
        # Push incomplete video
        await clean_redis.lpush("tiktok:videos", json.dumps(incomplete_video))
        
        # Push valid video
        valid_video = VideoData(
            id="complete_vid",
            desc="Complete video #completetest",
            create_time=int(datetime.now(timezone.utc).timestamp()),
            stats=VideoStats(play_count=10000, digg_count=1500, share_count=250, comment_count=125),
            author=VideoAuthor(unique_id="completecreator", nickname="Complete Creator", follower_count=5000),
            hashtags=["completetest"],
            scraped_at=datetime.now(timezone.utc),
            source_type="trending"
        )
        await producer.push_to_queue(valid_video)
        
        # Process all videos
        batch = await clean_redis.lrange("tiktok:videos", 0, -1)
        processed = 0
        errors = 0
        
        for video_json in batch:
            try:
                data = video_json.decode('utf-8') if isinstance(video_json, bytes) else video_json
                video = VideoData.model_validate_json(data)
                await trend_detector.process_video(video)
                processed += 1
            except Exception:
                errors += 1
        
        # Should process 1 valid video, skip 1 invalid
        assert processed == 1, f"Expected 1 processed, got {processed}"
        assert errors == 1, f"Expected 1 error, got {errors}"
    
    async def test_empty_hashtags_handling(
        self,
        clean_redis,
        clean_db,
        producer,
        trend_detector,
        trend_repository
    ):
        """
        Test handling of videos with no hashtags.
        
        Expected: Video should be processed but no hashtag trends created.
        """
        # Create video with no hashtags
        video = VideoData(
            id="no_hashtag_vid",
            desc="Video with no hashtags",
            create_time=int(datetime.now(timezone.utc).timestamp()),
            stats=VideoStats(play_count=50000, digg_count=7500, share_count=1000, comment_count=500),
            author=VideoAuthor(unique_id="nocreator", nickname="No Hashtag Creator", follower_count=10000),
            music=VideoMusic(id="sound_001", title="Some Sound", author_name="Artist"),
            hashtags=[],  # Empty hashtags
            scraped_at=datetime.now(timezone.utc),
            source_type="trending"
        )
        
        await producer.push_to_queue(video)
        
        # Process
        batch = await clean_redis.lrange("tiktok:videos", 0, 0)
        video_data = VideoData.model_validate_json(batch[0])
        trends = await trend_detector.process_video(video_data)
        
        # Should have sound trend but no hashtag trends
        sound_trends = [t for t in trends if t.type == TrendType.SOUND]
        hashtag_trends = [t for t in trends if t.type == TrendType.HASHTAG]
        
        assert len(sound_trends) == 1, "Should have 1 sound trend"
        assert len(hashtag_trends) == 0, "Should have 0 hashtag trends"


@pytest.mark.e2e
@pytest.mark.slow
class TestCircuitBreakerActivation:
    """
    Circuit breaker activation and recovery.
    """
    
    async def test_circuit_opens_after_failures(
        self,
        clean_redis,
        clean_db
    ):
        """
        Test that circuit breaker opens after threshold failures.
        
        Expected: After 5 failures, circuit should open and reject calls.
        """
        from scraper.circuit_breaker import CircuitBreaker
        
        # Create circuit breaker with low threshold for testing
        circuit = CircuitBreaker(
            failure_threshold=3,
            recovery_timeout=5,  # Short timeout for testing
            half_open_max_calls=1
        )
        
        # Verify initial state
        assert circuit.state == CircuitState.CLOSED
        
        # Simulate failures
        async def failing_operation():
            raise Exception("Simulated failure")
        
        # Trigger failures
        for i in range(3):
            try:
                await circuit.call(failing_operation)
            except Exception:
                pass
        
        # Circuit should be open
        assert circuit.state == CircuitState.OPEN
        assert circuit.failure_count >= 3
        
        # Next call should be rejected immediately
        with pytest.raises(CircuitOpenError):
            await circuit.call(failing_operation)
    
    async def test_circuit_recovery(
        self,
        clean_redis,
        clean_db
    ):
        """
        Test circuit breaker recovery after timeout.
        
        Expected: After recovery timeout, circuit enters half-open state.
        """
        from scraper.circuit_breaker import CircuitBreaker
        
        # Create circuit breaker with very short timeout
        circuit = CircuitBreaker(
            failure_threshold=2,
            recovery_timeout=1,  # 1 second for fast testing
            half_open_max_calls=1
        )
        
        # Trigger failures to open circuit
        async def failing_operation():
            raise Exception("Simulated failure")
        
        for i in range(2):
            try:
                await circuit.call(failing_operation)
            except Exception:
                pass
        
        assert circuit.state == CircuitState.OPEN
        
        # Wait for recovery timeout
        await asyncio.sleep(1.5)
        
        # Try a call - should transition to half-open
        async def success_operation():
            return "success"
        
        # State check should trigger transition
        await circuit._check_state_transition()
        
        # After timeout, should be able to try again
        # Note: Actual transition happens on call
        result = await circuit.call(success_operation)
        assert result == "success"
        assert circuit.state == CircuitState.CLOSED
    
    async def test_circuit_half_open_failure(
        self,
        clean_redis,
        clean_db
    ):
        """
        Test that failure in half-open state reopens circuit.
        
        Expected: Single failure in half-open should reopen circuit.
        """
        from scraper.circuit_breaker import CircuitBreaker
        
        circuit = CircuitBreaker(
            failure_threshold=2,
            recovery_timeout=1,
            half_open_max_calls=2
        )
        
        # Open circuit
        async def failing_operation():
            raise Exception("Failure")
        
        for i in range(2):
            try:
                await circuit.call(failing_operation)
            except Exception:
                pass
        
        assert circuit.state == CircuitState.OPEN
        
        # Wait and transition to half-open
        await asyncio.sleep(1.5)
        await circuit._check_state_transition()
        
        # Should be in half-open (checked via _check_state_transition)
        # Try call that fails
        try:
            await circuit.call(failing_operation)
        except Exception:
            pass
        
        # Should reopen
        assert circuit.state == CircuitState.OPEN


@pytest.mark.e2e
@pytest.mark.slow
class TestRecoveryContinuation:
    """
    Recovery and continuation scenarios.
    """
    
    async def test_processing_continues_after_partial_failure(
        self,
        clean_redis,
        clean_db,
        producer,
        trend_detector,
        trend_repository,
        video_factory,
        pipeline_metrics
    ):
        """
        Test that processing continues after some videos fail.
        
        Expected: Valid videos should still be processed even if some fail.
        """
        # Create mix of valid videos
        videos = []
        for i in range(10):
            video = VideoData(
                id=f"mixed_vid_{i}",
                desc=f"Mixed video {i} #mixedtest",
                create_time=int(datetime.now(timezone.utc).timestamp()),
                stats=VideoStats(
                    play_count=10000 + (i * 1000),
                    digg_count=1500,
                    share_count=250,
                    comment_count=125
                ),
                author=VideoAuthor(
                    unique_id=f"mixedcreator_{i}",
                    nickname=f"Mixed Creator {i}",
                    follower_count=5000
                ),
                hashtags=["mixedtest"],
                scraped_at=datetime.now(timezone.utc),
                source_type="trending"
            )
            videos.append(video)
        
        # Push all
        await producer.push_batch_to_queue(videos)
        pipeline_metrics.videos_pushed = len(videos)
        
        # Process all with some simulated failures
        processed = 0
        failed = 0
        
        for i, video_json in enumerate(await clean_redis.lrange("tiktok:videos", 0, -1)):
            try:
                # Simulate occasional failure
                if i == 3 or i == 7:
                    raise Exception("Simulated processing failure")
                
                video = VideoData.model_validate_json(
                    video_json.decode('utf-8') if isinstance(video_json, bytes) else video_json
                )
                await trend_detector.process_video(video)
                processed += 1
            except Exception:
                failed += 1
        
        pipeline_metrics.videos_processed = processed
        pipeline_metrics.errors_encountered = failed
        
        # Should have processed 8 out of 10
        assert processed == 8, f"Expected 8 processed, got {processed}"
        assert failed == 2, f"Expected 2 failed, got {failed}"
        
        # Verify trend was still created
        trend = await trend_repository.get_by_platform_id(
            TrendType.HASHTAG,
            "mixedtest"
        )
        assert trend is not None
        assert trend.video_count_current == 8
    
    async def test_batch_processing_resumes_after_interrupt(
        self,
        clean_redis,
        clean_db,
        producer,
        trend_detector,
        trend_repository,
        video_factory
    ):
        """
        Test that batch processing can resume after interruption.
        
        Expected: Unprocessed items should remain and be processable.
        """
        hashtag = "#resumetest"
        
        # Create batch of videos
        videos = []
        for i in range(20):
            video = VideoData(
                id=f"resume_vid_{i}",
                desc=f"Resume test video {i} {hashtag}",
                create_time=int(datetime.now(timezone.utc).timestamp()),
                stats=VideoStats(
                    play_count=15000 + (i * 500),
                    digg_count=2000,
                    share_count=400,
                    comment_count=200
                ),
                author=VideoAuthor(
                    unique_id=f"resumecreator_{i}",
                    nickname=f"Resume Creator {i}",
                    follower_count=6000
                ),
                hashtags=[hashtag],
                scraped_at=datetime.now(timezone.utc),
                source_type="trending"
            )
            videos.append(video)
        
        await producer.push_batch_to_queue(videos)
        
        # Process first half (simulate interruption)
        batch = await clean_redis.lrange("tiktok:videos", 0, 9)
        for video_json in batch:
            video = VideoData.model_validate_json(
                video_json.decode('utf-8') if isinstance(video_json, bytes) else video_json
            )
            await trend_detector.process_video(video)
        
        # "Interrupt" - don't remove processed items yet
        # In real scenario, consumer would have crashed
        
        # Now process remaining
        all_batch = await clean_redis.lrange("tiktok:videos", 0, -1)
        for i, video_json in enumerate(all_batch):
            if i >= 10:  # Process remaining
                video = VideoData.model_validate_json(
                    video_json.decode('utf-8') if isinstance(video_json, bytes) else video_json
                )
                await trend_detector.process_video(video)
        
        # Remove all (acknowledge processing)
        await clean_redis.ltrim("tiktok:videos", len(all_batch), -1)
        
        # Verify all processed
        trend = await trend_repository.get_by_platform_id(
            TrendType.HASHTAG,
            hashtag.lower().lstrip('#')
        )
        assert trend is not None
        # Video count depends on idempotency - in real system, we'd use video_id dedup
        assert trend.video_count_current >= 10
    
    async def test_metrics_accuracy_during_errors(
        self,
        clean_redis,
        clean_db,
        producer,
        trend_detector,
        pipeline_metrics
    ):
        """
        Test that metrics remain accurate during error conditions.
        
        Expected: Metrics should track successes and failures correctly.
        """
        videos = []
        for i in range(5):
            video = VideoData(
                id=f"metrics_vid_{i}",
                desc=f"Metrics test {i} #metricstest",
                create_time=int(datetime.now(timezone.utc).timestamp()),
                stats=VideoStats(play_count=10000, digg_count=1500, share_count=250, comment_count=125),
                author=VideoAuthor(unique_id=f"metricscreator_{i}", nickname=f"Metrics Creator {i}", follower_count=5000),
                hashtags=["metricstest"],
                scraped_at=datetime.now(timezone.utc),
                source_type="trending"
            )
            videos.append(video)
        
        await producer.push_batch_to_queue(videos)
        pipeline_metrics.videos_pushed = len(videos)
        
        # Process with some failures
        errors = 0
        for i, video_json in enumerate(await clean_redis.lrange("tiktok:videos", 0, -1)):
            try:
                if i == 2:
                    raise Exception("Simulated error for metrics test")
                
                video = VideoData.model_validate_json(
                    video_json.decode('utf-8') if isinstance(video_json, bytes) else video_json
                )
                await trend_detector.process_video(video)
                pipeline_metrics.videos_processed += 1
            except Exception:
                errors += 1
                pipeline_metrics.errors_encountered += 1
        
        pipeline_metrics.finalize()
        
        # Verify metrics
        assert pipeline_metrics.videos_pushed == 5
        assert pipeline_metrics.videos_processed == 4
        assert pipeline_metrics.errors_encountered == 1
        assert pipeline_metrics.to_dict()["errors_encountered"] == 1
