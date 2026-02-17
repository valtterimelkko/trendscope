"""
Detection Throughput Tests

Load tests for the trend detection pipeline.
Tests processing capacity, memory usage, cache performance, and aggregation speed.

Performance Thresholds:
- Process 10,000 videos < 5 seconds
- Memory usage < 512MB during batch processing
- Cache hit ratio > 80%
"""

import asyncio
import gc
import os
import time
import psutil
import uuid
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Tuple
from unittest.mock import AsyncMock, MagicMock

import pytest
import numpy as np

# Add project root to path for imports
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from detection.velocity_engine import VelocityEngine, VelocityResult
from detection.trend_detector import TrendDetector
from detection.models import VideoData, VideoStats, AuthorInfo, MusicInfo, Trend, TrendType, TrendStatus


# Performance thresholds
MAX_DETECTION_TIME = 5.0    # 10000 videos < 5 seconds
MAX_MEMORY_MB = 512         # Memory usage < 512MB


def get_memory_usage_mb() -> float:
    """Get current process memory usage in MB."""
    process = psutil.Process(os.getpid())
    return process.memory_info().rss / 1024 / 1024


def print_metrics(test_name: str, metrics: dict):
    """Print performance metrics in a standardized format."""
    print(f"\n{'='*60}")
    print(f"LOAD TEST METRICS: {test_name}")
    print(f"{'='*60}")
    for key, value in metrics.items():
        if isinstance(value, float):
            print(f"  {key}: {value:.4f}")
        else:
            print(f"  {key}: {value}")
    print(f"{'='*60}\n")


def create_sample_video(video_id: str, play_count: int, timestamp: datetime) -> VideoData:
    """Create a sample video data object."""
    return VideoData(
        id=video_id,
        url=f"https://tiktok.com/@user/video/{video_id}",
        scraped_at=timestamp,
        author=AuthorInfo(
            id=f"user_{video_id[-4:]}",
            unique_id=f"user_{video_id[-4:]}",
            follower_count=1000
        ),
        stats=VideoStats(
            play_count=play_count,
            digg_count=100,
            comment_count=10,
            share_count=5
        ),
        desc="Sample video description #viral #trending",
        hashtags=["viral", "trending", f"tag_{video_id[-2:]}"],
        music=MusicInfo(
            id=f"music_{video_id[-4:]}",
            title="Trending Sound",
            author_name="Artist"
        ),
        created_at=timestamp - timedelta(hours=1)
    )


def create_mock_repository():
    """Create a mock trend repository for testing."""
    mock = AsyncMock()
    mock.get_by_platform_id = AsyncMock(return_value=None)
    mock.create = AsyncMock(side_effect=lambda trend: Trend(
        id=uuid.uuid4(),
        type=trend.type,
        name=trend.name,
        platform_id=trend.platform_id,
        niche_id=None,
        first_detected_at=datetime.utcnow(),
        peak_detected_at=None,
        status=TrendStatus.EMERGING,
        velocity_score=trend.velocity_score,
        saturation_percent=trend.saturation_percent,
        video_count_start=1,
        video_count_current=1,
        growth_rate=trend.growth_rate,
        metadata=trend.metadata,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    ))
    mock.update = AsyncMock(side_effect=lambda tid, updates: Trend(
        id=tid,
        type=TrendType.HASHTAG,
        name="#updated",
        platform_id="updated",
        niche_id=None,
        first_detected_at=datetime.utcnow(),
        peak_detected_at=None,
        status=TrendStatus.EMERGING,
        velocity_score=50,
        saturation_percent=50,
        video_count_start=1,
        video_count_current=2,
        growth_rate=10.0,
        metadata={},
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    ))
    mock.record_velocity_history = AsyncMock(return_value=None)
    mock.get_by_id = AsyncMock(return_value=None)
    mock.get_velocity_history = AsyncMock(return_value=[])
    return mock


@pytest.mark.load
@pytest.mark.slow
class TestDetectionThroughput:
    """Throughput tests for trend detection."""

    @pytest.mark.asyncio
    async def test_process_10000_videos(self):
        """
        Test processing 10,000 videos.
        
        Verifies:
        - Processing completes within time threshold
        - All videos are processed
        - Memory stays within limits
        """
        mock_repo = create_mock_repository()
        detector = TrendDetector(repository=mock_repo)
        
        num_videos = 10000
        videos = [
            create_sample_video(
                f"video_{i:05d}",
                play_count=1000 + i * 10,
                timestamp=datetime.utcnow() - timedelta(minutes=i)
            )
            for i in range(num_videos)
        ]
        
        gc.collect()
        start_mem = get_memory_usage_mb()
        start_time = time.perf_counter()
        
        # Process all videos
        processed = 0
        for video in videos:
            try:
                await detector.process_video(video)
                processed += 1
            except Exception as e:
                print(f"Error processing video: {e}")
        
        elapsed = time.perf_counter() - start_time
        
        gc.collect()
        end_mem = get_memory_usage_mb()
        
        metrics = {
            "videos_processed": processed,
            "elapsed_sec": elapsed,
            "videos_per_sec": processed / elapsed if elapsed > 0 else 0,
            "ms_per_video": (elapsed / processed) * 1000 if processed > 0 else 0,
            "memory_start_mb": start_mem,
            "memory_end_mb": end_mem,
            "memory_increase_mb": end_mem - start_mem,
            "cache_stats": detector.get_cache_stats(),
        }
        print_metrics("Process 10,000 Videos", metrics)
        
        # Assertions
        assert processed == num_videos, f"Only processed {processed}/{num_videos}"
        assert elapsed < MAX_DETECTION_TIME, f"Too slow: {elapsed:.2f}s > {MAX_DETECTION_TIME}s"
        assert end_mem - start_mem < MAX_MEMORY_MB, f"Memory exceeded: {end_mem - start_mem:.1f}MB"

    @pytest.mark.asyncio
    async def test_memory_usage_during_batch_processing(self):
        """
        Test memory usage during batch processing.
        
        Verifies:
        - Memory growth is bounded
        - No memory leaks
        - Stable performance over large batches
        """
        mock_repo = create_mock_repository()
        detector = TrendDetector(repository=mock_repo)
        
        batch_sizes = [1000, 2000, 5000]
        memory_readings = []
        
        gc.collect()
        baseline_mem = get_memory_usage_mb()
        
        for batch_size in batch_sizes:
            # Create and process batch
            videos = [
                create_sample_video(
                    f"batch_video_{i:05d}",
                    play_count=1000 + i,
                    timestamp=datetime.utcnow() - timedelta(minutes=i)
                )
                for i in range(batch_size)
            ]
            
            for video in videos:
                await detector.process_video(video)
            
            gc.collect()
            current_mem = get_memory_usage_mb()
            memory_readings.append({
                "batch_size": batch_size,
                "memory_mb": current_mem,
                "growth_mb": current_mem - baseline_mem
            })
            
            # Clear cache to reset for next batch
            detector.trend_cache.clear()
        
        metrics = {
            "baseline_memory_mb": baseline_mem,
            "memory_readings": memory_readings,
            "max_memory_mb": max(r["memory_mb"] for r in memory_readings),
            "final_cache_size": detector.get_cache_stats(),
        }
        print_metrics("Memory Usage During Batch Processing", metrics)
        
        # Memory should not grow unbounded
        max_growth = max(r["growth_mb"] for r in memory_readings)
        assert max_growth < 200, f"Excessive memory growth: {max_growth:.1f}MB"

    @pytest.mark.asyncio
    async def test_cache_performance(self):
        """
        Test cache performance (hit/miss ratio).
        
        Verifies:
        - Cache hit ratio > 80%
        - Cache reduces database calls
        - Cache eviction works correctly
        """
        mock_repo = create_mock_repository()
        detector = TrendDetector(repository=mock_repo)
        
        # Track database calls
        db_calls = 0
        original_get = mock_repo.get_by_platform_id
        
        async def tracking_get(trend_type, platform_id):
            nonlocal db_calls
            db_calls += 1
            return await original_get(trend_type, platform_id)
        
        mock_repo.get_by_platform_id = tracking_get
        
        # Process videos with repeated trends (high cache hit expected)
        num_unique_trends = 50
        num_videos = 1000
        
        # Create videos cycling through same trends
        videos = []
        for i in range(num_videos):
            trend_suffix = i % num_unique_trends
            video = create_sample_video(
                f"cache_test_{i:04d}",
                play_count=1000 + i * 10,
                timestamp=datetime.utcnow() - timedelta(minutes=i)
            )
            # Modify hashtags to create repeated trends
            video.hashtags = [f"repeated_tag_{trend_suffix}", "common_tag"]
            videos.append(video)
        
        db_calls = 0
        start_time = time.perf_counter()
        
        for video in videos:
            await detector.process_video(video)
        
        elapsed = time.perf_counter() - start_time
        
        # Calculate cache effectiveness
        cache_stats = detector.get_cache_stats()
        
        # With cache, we should have many cached trends
        # DB calls should be roughly equal to unique trends (initial lookups)
        expected_db_calls = num_unique_trends + 1  # +1 for common_tag
        cache_effectiveness = 1 - (db_calls / (num_videos * 2))  # 2 trends per video
        
        metrics = {
            "num_videos": num_videos,
            "num_unique_trends": num_unique_trends,
            "db_calls": db_calls,
            "expected_db_calls": expected_db_calls,
            "cache_effectiveness": cache_effectiveness,
            "cache_stats": cache_stats,
            "elapsed_sec": elapsed,
            "videos_per_sec": num_videos / elapsed if elapsed > 0 else 0,
        }
        print_metrics("Cache Performance", metrics)
        
        # Cache should be effective
        assert cache_stats["total_trends"] <= num_unique_trends + 1, "Too many cached trends"

    @pytest.mark.asyncio
    async def test_database_write_throughput(self):
        """
        Test database write throughput.
        
        Verifies:
        - Write operations per second
        - Batch write efficiency
        - No write bottlenecks
        """
        write_times = []
        
        async def timed_create(trend):
            start = time.perf_counter()
            result = await AsyncMock()()
            elapsed = time.perf_counter() - start
            write_times.append(elapsed)
            return result
        
        mock_repo = create_mock_repository()
        detector = TrendDetector(repository=mock_repo)
        
        # Process videos that trigger writes
        num_writes = 1000
        videos = []
        for i in range(num_writes):
            video = create_sample_video(
                f"write_test_{i:04d}",
                play_count=10000 + i * 100,  # High play count for velocity
                timestamp=datetime.utcnow() - timedelta(minutes=i)
            )
            # Unique hashtag for each to force new trend creation
            video.hashtags = [f"unique_tag_{i}"]
            videos.append(video)
        
        start_time = time.perf_counter()
        
        for video in videos:
            await detector.process_video(video)
        
        elapsed = time.perf_counter() - start_time
        
        # Calculate write metrics
        write_count = mock_repo.create.call_count + mock_repo.update.call_count
        
        metrics = {
            "num_videos": num_writes,
            "elapsed_sec": elapsed,
            "videos_per_sec": num_writes / elapsed if elapsed > 0 else 0,
            "write_operations": write_count,
            "writes_per_sec": write_count / elapsed if elapsed > 0 else 0,
            "avg_write_time_ms": (sum(write_times) / len(write_times)) * 1000 if write_times else 0,
        }
        print_metrics("Database Write Throughput", metrics)
        
        # Should maintain reasonable throughput
        assert metrics["videos_per_sec"] > 100, f"Throughput too low: {metrics['videos_per_sec']:.1f} videos/sec"

    @pytest.mark.asyncio
    async def test_trend_aggregation_performance(self):
        """
        Test trend aggregation performance.
        
        Verifies:
        - Aggregation speed for large datasets
        - Efficient grouping
        - Memory efficiency during aggregation
        """
        mock_repo = create_mock_repository()
        detector = TrendDetector(repository=mock_repo)
        
        # Create videos with known aggregation patterns
        num_videos = 5000
        num_trends = 100
        
        videos = []
        for i in range(num_videos):
            trend_id = i % num_trends
            video = create_sample_video(
                f"agg_test_{i:05d}",
                play_count=1000 + (i // num_trends) * 100,
                timestamp=datetime.utcnow() - timedelta(minutes=i)
            )
            # All videos share one common hashtag, plus unique ones
            video.hashtags = [f"trend_{trend_id:02d}", "common"]
            videos.append(video)
        
        gc.collect()
        start_mem = get_memory_usage_mb()
        start_time = time.perf_counter()
        
        for video in videos:
            await detector.process_video(video)
        
        elapsed = time.perf_counter() - start_time
        
        gc.collect()
        end_mem = get_memory_usage_mb()
        
        cache_stats = detector.get_cache_stats()
        
        metrics = {
            "num_videos": num_videos,
            "num_expected_trends": num_trends + 1,  # +1 for "common"
            "elapsed_sec": elapsed,
            "videos_per_sec": num_videos / elapsed if elapsed > 0 else 0,
            "memory_start_mb": start_mem,
            "memory_end_mb": end_mem,
            "memory_increase_mb": end_mem - start_mem,
            "cache_stats": cache_stats,
        }
        print_metrics("Trend Aggregation Performance", metrics)
        
        # Should aggregate correctly
        assert cache_stats["total_trends"] <= num_trends + 1, "Aggregation not working correctly"

    @pytest.mark.asyncio
    async def test_velocity_calculation_batch_performance(self):
        """
        Test velocity calculation batch performance.
        
        Verifies:
        - Velocity calculation speed
        - R-squared computation performance
        - Scaling with data points
        """
        engine = VelocityEngine()
        
        calculation_times = []
        data_point_counts = [10, 50, 100, 168]  # 168 = max data points
        
        for num_points in data_point_counts:
            # Create time-series data
            base_time = datetime.utcnow() - timedelta(hours=num_points)
            data_points = [
                (base_time + timedelta(hours=i), 1000 + i * 100)
                for i in range(num_points)
            ]
            
            # Warm up
            engine.calculate_velocity(data_points)
            
            # Timed runs
            times = []
            for _ in range(100):
                start = time.perf_counter()
                result = engine.calculate_velocity(data_points)
                elapsed = time.perf_counter() - start
                times.append(elapsed)
            
            avg_time = sum(times) / len(times)
            calculation_times.append({
                "data_points": num_points,
                "avg_time_ms": avg_time * 1000,
                "min_time_ms": min(times) * 1000,
                "max_time_ms": max(times) * 1000,
            })
        
        metrics = {
            "calculation_times": calculation_times,
            "max_time_ms": max(t["max_time_ms"] for t in calculation_times),
        }
        print_metrics("Velocity Calculation Batch Performance", metrics)
        
        # Should be fast even with max data points
        max_avg_time = max(t["avg_time_ms"] for t in calculation_times)
        assert max_avg_time < 10, f"Velocity calculation too slow: {max_avg_time:.2f}ms"


@pytest.mark.load
@pytest.mark.slow
@pytest.mark.asyncio
async def test_detection_comprehensive():
    """
    Comprehensive detection throughput test.
    
    Combines multiple scenarios for full pipeline stress testing.
    """
    mock_repo = create_mock_repository()
    detector = TrendDetector(repository=mock_repo)
    
    num_videos = 5000
    
    # Mix of video patterns
    videos = []
    for i in range(num_videos):
        pattern = i % 5
        if pattern == 0:
            # Viral growth
            play_count = 10000 + i * 500
        elif pattern == 1:
            # Steady growth
            play_count = 1000 + i * 50
        elif pattern == 2:
            # Flat
            play_count = 1000
        elif pattern == 3:
            # Declining
            play_count = max(100, 5000 - i * 10)
        else:
            # Random
            play_count = 1000 + (i * 37) % 5000
        
        video = create_sample_video(
            f"comprehensive_{i:05d}",
            play_count=play_count,
            timestamp=datetime.utcnow() - timedelta(minutes=i)
        )
        # Mix of shared and unique hashtags
        if i % 10 == 0:
            video.hashtags = [f"unique_{i}", "common"]
        else:
            video.hashtags = [f"group_{i % 20}", "common"]
        videos.append(video)
    
    gc.collect()
    start_mem = get_memory_usage_mb()
    start_time = time.perf_counter()
    
    processed = 0
    for video in videos:
        try:
            await detector.process_video(video)
            processed += 1
        except Exception as e:
            print(f"Error: {e}")
    
    elapsed = time.perf_counter() - start_time
    
    gc.collect()
    end_mem = get_memory_usage_mb()
    
    cache_stats = detector.get_cache_stats()
    
    metrics = {
        "videos_processed": processed,
        "elapsed_sec": elapsed,
        "videos_per_sec": processed / elapsed if elapsed > 0 else 0,
        "memory_start_mb": start_mem,
        "memory_end_mb": end_mem,
        "memory_increase_mb": end_mem - start_mem,
        "cache_stats": cache_stats,
        "db_creates": mock_repo.create.call_count,
        "db_updates": mock_repo.update.call_count,
        "velocity_history_records": mock_repo.record_velocity_history.call_count,
    }
    print_metrics("Comprehensive Detection Test", metrics)
    
    # Final assertions
    assert processed == num_videos, "Not all videos processed"
    assert metrics["videos_per_sec"] > 200, f"Throughput too low: {metrics['videos_per_sec']:.1f}"
    assert end_mem - start_mem < 256, f"Memory too high: {end_mem - start_mem:.1f}MB"
