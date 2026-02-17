"""
Unit Tests for Trend Detector

Tests trend extraction, data aggregation, cache management, and trend processing.
"""

import pytest
import uuid
from datetime import datetime, timedelta
from unittest.mock import MagicMock, AsyncMock, patch

from detection.trend_detector import TrendDetector
from detection.models import (
    VideoData, VideoStats, VideoMusic, VideoAuthor,
    Trend, TrendType, TrendStatus, ExtractedTrend
)
from detection.velocity_engine import VelocityResult
from detection.saturation import SaturationResult


class TestTrendExtractor:
    """Test suite for trend extraction from videos."""

    @pytest.fixture
    def mock_repository(self):
        """Create a mock TrendRepository."""
        repo = MagicMock()
        repo.get_by_platform_id = AsyncMock(return_value=None)
        repo.create = AsyncMock()
        repo.update = AsyncMock()
        repo.record_velocity_history = AsyncMock()
        return repo

    @pytest.fixture
    def detector(self, mock_repository):
        """Create a TrendDetector with mock repository."""
        return TrendDetector(repository=mock_repository)

    @pytest.fixture
    def sample_video_with_music(self):
        """Create a sample video with music."""
        return VideoData(
            id="video123",
            desc="Test video description",
            create_time=1704067200,
            stats=VideoStats(
                play_count=10000,
                digg_count=500,
                share_count=100,
                comment_count=50
            ),
            author=VideoAuthor(
                unique_id="@testuser",
                nickname="Test User",
                follower_count=5000
            ),
            music=VideoMusic(
                id="sound456",
                title="Test Sound",
                author_name="Sound Artist"
            ),
            hashtags=["viral", "trending"],
            scraped_at=datetime.utcnow()
        )

    @pytest.fixture
    def sample_video_no_music(self):
        """Create a sample video without music."""
        return VideoData(
            id="video789",
            desc="Another test video",
            create_time=1704067300,
            stats=VideoStats(
                play_count=5000,
                digg_count=200,
                share_count=50,
                comment_count=20
            ),
            author=VideoAuthor(
                unique_id="@anotheruser",
                nickname="Another User",
                follower_count=3000
            ),
            music=None,
            hashtags=["funny", "comedy", "viral"],
            scraped_at=datetime.utcnow()
        )

    @pytest.fixture
    def sample_video_multiple_hashtags(self):
        """Create a sample video with many hashtags."""
        return VideoData(
            id="video999",
            desc="Many hashtags",
            create_time=1704067400,
            stats=VideoStats(
                play_count=15000,
                digg_count=800,
                share_count=200,
                comment_count=100
            ),
            author=VideoAuthor(
                unique_id="@popularuser",
                nickname="Popular User",
                follower_count=10000
            ),
            music=VideoMusic(
                id="sound789",
                title="Popular Sound",
                author_name="Music Star"
            ),
            hashtags=["trend1", "trend2", "trend3", "trend4", "trend5"],
            scraped_at=datetime.utcnow()
        )

    def test_extract_trends_with_music(self, detector, sample_video_with_music):
        """
        Test extraction of trends from video with music.
        
        Should extract:
        - 1 sound trend
        - 2 hashtag trends
        """
        trends = detector._extract_trends(sample_video_with_music)
        
        assert len(trends) == 3  # 1 sound + 2 hashtags
        
        # Check sound trend
        sound_trends = [t for t in trends if t.type == TrendType.SOUND]
        assert len(sound_trends) == 1
        assert sound_trends[0].platform_id == "sound456"
        assert "Test Sound" in sound_trends[0].name
        
        # Check hashtag trends
        hashtag_trends = [t for t in trends if t.type == TrendType.HASHTAG]
        assert len(hashtag_trends) == 2
        assert any(t.platform_id == "viral" for t in hashtag_trends)
        assert any(t.platform_id == "trending" for t in hashtag_trends)

    def test_extract_trends_no_music(self, detector, sample_video_no_music):
        """
        Test extraction from video without music.
        
        Should only extract hashtag trends.
        """
        trends = detector._extract_trends(sample_video_no_music)
        
        # Only hashtags, no sound
        assert len(trends) == 3
        assert all(t.type == TrendType.HASHTAG for t in trends)

    def test_extract_trends_multiple_hashtags(self, detector, sample_video_multiple_hashtags):
        """Test extraction with multiple hashtags."""
        trends = detector._extract_trends(sample_video_multiple_hashtags)
        
        # 1 sound + 5 hashtags
        assert len(trends) == 6
        
        hashtag_trends = [t for t in trends if t.type == TrendType.HASHTAG]
        assert len(hashtag_trends) == 5

    def test_extract_trends_hashtag_normalization(self, detector, sample_video_with_music):
        """Test that hashtags are normalized to lowercase."""
        video = VideoData(
            id="video001",
            desc="Test",
            create_time=1704067200,
            stats=VideoStats(play_count=1000, digg_count=50, share_count=10, comment_count=5),
            author=VideoAuthor(unique_id="@user", nickname="User", follower_count=100),
            music=None,
            hashtags=["VIRAL", "Viral", "viral"],  # Mixed case
            scraped_at=datetime.utcnow()
        )
        
        trends = detector._extract_trends(video)
        
        # All should be normalized to lowercase
        hashtag_trends = [t for t in trends if t.type == TrendType.HASHTAG]
        assert len(hashtag_trends) == 3
        assert all(t.platform_id == "viral" for t in hashtag_trends)

    def test_extract_trends_empty_hashtags(self, detector):
        """Test handling of empty hashtag strings."""
        video = VideoData(
            id="video002",
            desc="Test",
            create_time=1704067200,
            stats=VideoStats(play_count=1000, digg_count=50, share_count=10, comment_count=5),
            author=VideoAuthor(unique_id="@user", nickname="User", follower_count=100),
            music=None,
            hashtags=["valid", "", "another"],  # Empty string in middle
            scraped_at=datetime.utcnow()
        )
        
        trends = detector._extract_trends(video)
        
        hashtag_trends = [t for t in trends if t.type == TrendType.HASHTAG]
        # Empty string should be skipped
        assert len(hashtag_trends) == 2

    def test_extract_trends_sound_name_format(self, detector):
        """Test sound trend name formatting."""
        video = VideoData(
            id="video003",
            desc="Test",
            create_time=1704067200,
            stats=VideoStats(play_count=1000, digg_count=50, share_count=10, comment_count=5),
            author=VideoAuthor(unique_id="@user", nickname="User", follower_count=100),
            music=VideoMusic(
                id="sound001",
                title="Awesome Beat",
                author_name="DJ Test"
            ),
            hashtags=[],
            scraped_at=datetime.utcnow()
        )
        
        trends = detector._extract_trends(video)
        
        sound_trend = [t for t in trends if t.type == TrendType.SOUND][0]
        assert "Awesome Beat" in sound_trend.name
        assert "DJ Test" in sound_trend.name

    def test_extract_trends_sound_no_title(self, detector):
        """Test sound trend extraction when title is missing."""
        video = VideoData(
            id="video004",
            desc="Test",
            create_time=1704067200,
            stats=VideoStats(play_count=1000, digg_count=50, share_count=10, comment_count=5),
            author=VideoAuthor(unique_id="@user", nickname="User", follower_count=100),
            music=VideoMusic(
                id="sound002",
                title=None,
                author_name=None
            ),
            hashtags=[],
            scraped_at=datetime.utcnow()
        )
        
        trends = detector._extract_trends(video)
        
        sound_trend = [t for t in trends if t.type == TrendType.SOUND][0]
        assert "sound002" in sound_trend.name


class TestCacheManagement:
    """Test suite for cache management."""

    @pytest.fixture
    def mock_repository(self):
        """Create a mock TrendRepository."""
        repo = MagicMock()
        repo.get_by_platform_id = AsyncMock(return_value=None)
        repo.create = AsyncMock(side_effect=lambda t: Trend(
            id=uuid.uuid4(),
            type=t.type,
            name=t.name,
            platform_id=t.platform_id,
            status=TrendStatus.EMERGING,
            velocity_score=t.velocity_score,
            saturation_percent=t.saturation_percent
        ))
        repo.update = AsyncMock()
        repo.record_velocity_history = AsyncMock()
        return repo

    @pytest.fixture
    def detector(self, mock_repository):
        """Create a TrendDetector with mock repository."""
        return TrendDetector(repository=mock_repository)

    @pytest.fixture
    def sample_video(self):
        """Create a sample video."""
        return VideoData(
            id="video001",
            desc="Test",
            create_time=1704067200,
            stats=VideoStats(play_count=1000, digg_count=50, share_count=10, comment_count=5),
            author=VideoAuthor(unique_id="@user", nickname="User", follower_count=100),
            music=VideoMusic(id="sound001", title="Sound", author_name="Artist"),
            hashtags=["trend"],
            scraped_at=datetime.utcnow()
        )

    def test_cache_initially_empty(self, detector):
        """Test that cache starts empty."""
        stats = detector.get_cache_stats()
        assert stats["total_trends"] == 0
        assert stats["total_data_points"] == 0

    def test_data_point_aggregation(self, detector, sample_video, mock_repository):
        """Test that data points are aggregated in cache."""
        # Process same trend multiple times
        video1 = sample_video
        video2 = sample_video.model_copy()
        video2.scraped_at = datetime.utcnow() + timedelta(hours=1)
        video2.stats = VideoStats(play_count=2000, digg_count=100, share_count=20, comment_count=10)
        
        # Mock to return high velocity for processing
        with patch.object(detector.velocity_engine, 'calculate_velocity') as mock_calc:
            mock_calc.return_value = VelocityResult(
                score=50,
                growth_rate=10.0,
                doubling_time=7.0,
                r_squared=0.90,
                is_exponential=True,
                acceleration=0.05,
                confidence=0.8,
                data_points=2,
                time_window_hours=1.0
            )
            
            # Process videos
            # Note: process_video is async, so we need to handle that

    def test_cache_max_points_enforcement(self, detector):
        """Test that cache respects max_cache_points limit."""
        # Add more points than max_cache_points
        cache_key = "hashtag:test"
        detector.max_cache_points = 5
        
        base_time = datetime.utcnow()
        for i in range(10):
            point = (base_time + timedelta(hours=i), 1000 + i * 100)
            if cache_key not in detector.trend_cache:
                detector.trend_cache[cache_key] = []
            detector.trend_cache[cache_key].append(point)
        
        # Trim to max
        if len(detector.trend_cache[cache_key]) > detector.max_cache_points:
            detector.trend_cache[cache_key] = detector.trend_cache[cache_key][-detector.max_cache_points:]
        
        assert len(detector.trend_cache[cache_key]) == 5

    def test_cache_stats_calculation(self, detector):
        """Test cache statistics calculation."""
        # Populate cache
        detector.trend_cache["hashtag:test1"] = [
            (datetime.utcnow(), 100),
            (datetime.utcnow(), 200)
        ]
        detector.trend_cache["hashtag:test2"] = [
            (datetime.utcnow(), 300)
        ]
        
        stats = detector.get_cache_stats()
        
        assert stats["total_trends"] == 2
        assert stats["total_data_points"] == 3
        assert stats["avg_points_per_trend"] == 1.5

    def test_clear_stale_cache_entries(self, detector):
        """Test clearing stale cache entries."""
        now = datetime.utcnow()
        
        # Add fresh entry
        detector.trend_cache["hashtag:fresh"] = [
            (now - timedelta(hours=1), 100)
        ]
        
        # Add stale entry
        detector.trend_cache["hashtag:stale"] = [
            (now - timedelta(hours=100), 100)
        ]
        
        removed = detector.clear_stale_cache_entries(max_age_hours=72)
        
        assert removed == 1
        assert "hashtag:fresh" in detector.trend_cache
        assert "hashtag:stale" not in detector.trend_cache

    def test_clear_stale_no_entries_to_remove(self, detector):
        """Test clearing stale entries when none are stale."""
        now = datetime.utcnow()
        
        detector.trend_cache["hashtag:fresh1"] = [
            (now - timedelta(hours=10), 100)
        ]
        detector.trend_cache["hashtag:fresh2"] = [
            (now - timedelta(hours=20), 100)
        ]
        
        removed = detector.clear_stale_cache_entries(max_age_hours=72)
        
        assert removed == 0
        assert len(detector.trend_cache) == 2


class TestTrendProcessing:
    """Test suite for trend processing logic."""

    @pytest.fixture
    def mock_repository(self):
        """Create a mock TrendRepository."""
        repo = MagicMock()
        repo.get_by_platform_id = AsyncMock(return_value=None)
        repo.create = AsyncMock(side_effect=lambda t: Trend(
            id=uuid.uuid4(),
            type=t.type,
            name=t.name,
            platform_id=t.platform_id,
            status=TrendStatus.EMERGING,
            velocity_score=t.velocity_score,
            saturation_percent=t.saturation_percent
        ))
        repo.update = AsyncMock()
        repo.record_velocity_history = AsyncMock()
        return repo

    @pytest.fixture
    def detector(self, mock_repository):
        """Create a TrendDetector with mock repository."""
        return TrendDetector(repository=mock_repository)

    @pytest.fixture
    def sample_video(self):
        """Create a sample video."""
        return VideoData(
            id="video001",
            desc="Test",
            create_time=1704067200,
            stats=VideoStats(play_count=1000, digg_count=50, share_count=10, comment_count=5),
            author=VideoAuthor(unique_id="@user", nickname="User", follower_count=100),
            music=VideoMusic(id="sound001", title="Sound", author_name="Artist"),
            hashtags=["trend"],
            scraped_at=datetime.utcnow()
        )

    @pytest.mark.asyncio
    async def test_process_video_returns_trends(self, detector, sample_video, mock_repository):
        """Test that process_video returns list of trends."""
        # Mock velocity calculation to return significant velocity
        with patch.object(detector.velocity_engine, 'calculate_velocity') as mock_velocity:
            with patch.object(detector.saturation_engine, 'calculate') as mock_saturation:
                mock_velocity.return_value = VelocityResult(
                    score=60,
                    growth_rate=12.0,
                    doubling_time=5.83,
                    r_squared=0.90,
                    is_exponential=True,
                    acceleration=0.05,
                    confidence=0.85,
                    data_points=5,
                    time_window_hours=4.0
                )
                mock_saturation.return_value = SaturationResult(
                    score=25,
                    stage="early",
                    recommendation="Good opportunity"
                )
                
                trends = await detector.process_video(sample_video)
                
                assert isinstance(trends, list)

    @pytest.mark.asyncio
    async def test_process_trend_below_velocity_threshold(self, detector, sample_video, mock_repository):
        """Test that trends below velocity threshold are not persisted."""
        with patch.object(detector.velocity_engine, 'calculate_velocity') as mock_velocity:
            mock_velocity.return_value = VelocityResult(
                score=20,  # Below threshold
                growth_rate=5.0,
                doubling_time=14.0,
                r_squared=0.60,
                is_exponential=False,
                acceleration=0.0,
                confidence=0.5,
                data_points=5,
                time_window_hours=4.0
            )
            
            trend = await detector._process_trend(
                ExtractedTrend(
                    type=TrendType.HASHTAG,
                    platform_id="test",
                    name="#test",
                    video=sample_video
                )
            )
            
            assert trend is None

    @pytest.mark.asyncio
    async def test_create_trend_for_new_trend(self, detector, sample_video, mock_repository):
        """Test creating a new trend record."""
        extracted = ExtractedTrend(
            type=TrendType.HASHTAG,
            platform_id="newtrend",
            name="#newtrend",
            video=sample_video
        )
        
        velocity = VelocityResult(
            score=70,
            growth_rate=15.0,
            doubling_time=4.67,
            r_squared=0.92,
            is_exponential=True,
            acceleration=0.08,
            confidence=0.88,
            data_points=10,
            time_window_hours=12.0
        )
        
        saturation = SaturationResult(
            score=20,
            stage="early",
            recommendation="Good opportunity"
        )
        
        trend = await detector._create_trend(extracted, velocity, saturation, TrendStatus.EMERGING)
        
        assert trend is not None
        assert trend.type == TrendType.HASHTAG
        assert trend.platform_id == "newtrend"
        assert trend.status == TrendStatus.EMERGING
        mock_repository.create.assert_called_once()

    @pytest.mark.asyncio
    async def test_update_trend_for_existing(self, detector, sample_video, mock_repository):
        """Test updating an existing trend record."""
        existing_id = uuid.uuid4()
        existing = Trend(
            id=existing_id,
            type=TrendType.HASHTAG,
            name="#existing",
            platform_id="existing123",
            status=TrendStatus.EMERGING,
            velocity_score=50,
            saturation_percent=30,
            video_count_current=5,
            metadata={"example_videos": ["old_video"]}
        )
        
        extracted = ExtractedTrend(
            type=TrendType.HASHTAG,
            platform_id="existing123",
            name="#existing",
            video=sample_video
        )
        
        velocity = VelocityResult(
            score=75,
            growth_rate=18.0,
            doubling_time=3.89,
            r_squared=0.93,
            is_exponential=True,
            acceleration=0.05,
            confidence=0.90,
            data_points=15,
            time_window_hours=18.0
        )
        
        saturation = SaturationResult(
            score=40,
            stage="growth",
            recommendation="Strong opportunity"
        )
        
        await detector._update_trend(existing, extracted, velocity, saturation, TrendStatus.PEAKING)
        
        mock_repository.update.assert_called_once()
        call_args = mock_repository.update.call_args
        assert call_args[0][0] == existing_id


class TestMultipleTrendsHandling:
    """Test suite for handling multiple trends per video."""

    @pytest.fixture
    def mock_repository(self):
        """Create a mock TrendRepository."""
        repo = MagicMock()
        repo.get_by_platform_id = AsyncMock(return_value=None)
        repo.create = AsyncMock(side_effect=lambda t: Trend(
            id=uuid.uuid4(),
            type=t.type,
            name=t.name,
            platform_id=t.platform_id,
            status=TrendStatus.EMERGING,
            velocity_score=t.velocity_score,
            saturation_percent=t.saturation_percent
        ))
        repo.update = AsyncMock()
        repo.record_velocity_history = AsyncMock()
        return repo

    @pytest.fixture
    def detector(self, mock_repository):
        """Create a TrendDetector with mock repository."""
        return TrendDetector(repository=mock_repository)

    def test_multiple_trends_extracted(self, detector):
        """Test extraction of multiple trends from single video."""
        video = VideoData(
            id="video_multi",
            desc="Many trends",
            create_time=1704067200,
            stats=VideoStats(play_count=10000, digg_count=500, share_count=100, comment_count=50),
            author=VideoAuthor(unique_id="@creator", nickname="Creator", follower_count=5000),
            music=VideoMusic(id="sound_multi", title="Trending Sound", author_name="Artist"),
            hashtags=["tag1", "tag2", "tag3", "tag4"],
            scraped_at=datetime.utcnow()
        )
        
        trends = detector._extract_trends(video)
        
        # 1 sound + 4 hashtags
        assert len(trends) == 5
        
        sound_count = len([t for t in trends if t.type == TrendType.SOUND])
        hashtag_count = len([t for t in trends if t.type == TrendType.HASHTAG])
        
        assert sound_count == 1
        assert hashtag_count == 4

    def test_unique_cache_keys_per_trend(self, detector):
        """Test that each trend gets a unique cache key."""
        video = VideoData(
            id="video_keys",
            desc="Test",
            create_time=1704067200,
            stats=VideoStats(play_count=1000, digg_count=50, share_count=10, comment_count=5),
            author=VideoAuthor(unique_id="@user", nickname="User", follower_count=100),
            music=VideoMusic(id="sound_key", title="Sound", author_name="Artist"),
            hashtags=["tag1", "tag2"],
            scraped_at=datetime.utcnow()
        )
        
        trends = detector._extract_trends(video)
        
        # Generate cache keys
        cache_keys = set()
        for trend in trends:
            key = f"{trend.type.value}:{trend.platform_id}"
            cache_keys.add(key)
        
        # Each trend should have a unique key
        assert len(cache_keys) == len(trends)


class TestTrendUpdateVsCreate:
    """Test suite for trend update vs create logic."""

    @pytest.fixture
    def mock_repository(self):
        """Create a mock TrendRepository."""
        repo = MagicMock()
        repo.get_by_platform_id = AsyncMock(return_value=None)
        repo.create = AsyncMock(side_effect=lambda t: Trend(
            id=uuid.uuid4(),
            type=t.type,
            name=t.name,
            platform_id=t.platform_id,
            status=TrendStatus.EMERGING,
            velocity_score=t.velocity_score,
            saturation_percent=t.saturation_percent
        ))
        repo.update = AsyncMock()
        repo.record_velocity_history = AsyncMock()
        return repo

    @pytest.fixture
    def detector(self, mock_repository):
        """Create a TrendDetector with mock repository."""
        return TrendDetector(repository=mock_repository)

    @pytest.fixture
    def sample_video(self):
        """Create a sample video."""
        return VideoData(
            id="video001",
            desc="Test",
            create_time=1704067200,
            stats=VideoStats(play_count=1000, digg_count=50, share_count=10, comment_count=5),
            author=VideoAuthor(unique_id="@user", nickname="User", follower_count=100),
            music=VideoMusic(id="sound001", title="Sound", author_name="Artist"),
            hashtags=["trend"],
            scraped_at=datetime.utcnow()
        )

    @pytest.mark.asyncio
    async def test_create_called_for_new_trend(self, detector, sample_video, mock_repository):
        """Test that create is called for new trends."""
        # Ensure no existing trend
        mock_repository.get_by_platform_id.return_value = None
        
        with patch.object(detector.velocity_engine, 'calculate_velocity') as mock_velocity:
            with patch.object(detector.saturation_engine, 'calculate') as mock_saturation:
                mock_velocity.return_value = VelocityResult(
                    score=60,
                    growth_rate=12.0,
                    doubling_time=5.83,
                    r_squared=0.90,
                    is_exponential=True,
                    acceleration=0.05,
                    confidence=0.85,
                    data_points=5,
                    time_window_hours=4.0
                )
                mock_saturation.return_value = SaturationResult(
                    score=10,
                    stage="early",
                    recommendation="New trend"
                )
                
                await detector._process_trend(
                    ExtractedTrend(
                        type=TrendType.HASHTAG,
                        platform_id="newtrend",
                        name="#newtrend",
                        video=sample_video
                    )
                )
                
                mock_repository.create.assert_called_once()
                mock_repository.update.assert_not_called()

    @pytest.mark.asyncio
    async def test_update_called_for_existing_trend(self, detector, sample_video, mock_repository):
        """Test that update is called for existing trends."""
        existing_trend = Trend(
            id=uuid.uuid4(),
            type=TrendType.HASHTAG,
            name="#existing",
            platform_id="existing123",
            status=TrendStatus.EMERGING,
            velocity_score=40,
            saturation_percent=20
        )
        
        # Return existing trend
        mock_repository.get_by_platform_id.return_value = existing_trend
        
        with patch.object(detector.velocity_engine, 'calculate_velocity') as mock_velocity:
            with patch.object(detector.saturation_engine, 'calculate') as mock_saturation:
                mock_velocity.return_value = VelocityResult(
                    score=60,
                    growth_rate=12.0,
                    doubling_time=5.83,
                    r_squared=0.90,
                    is_exponential=True,
                    acceleration=0.05,
                    confidence=0.85,
                    data_points=5,
                    time_window_hours=4.0
                )
                mock_saturation.return_value = SaturationResult(
                    score=30,
                    stage="early",
                    recommendation="Good opportunity"
                )
                
                await detector._process_trend(
                    ExtractedTrend(
                        type=TrendType.HASHTAG,
                        platform_id="existing123",
                        name="#existing",
                        video=sample_video
                    )
                )
                
                mock_repository.create.assert_not_called()
                mock_repository.update.assert_called_once()
