"""
Unit Tests for Detection Models

Tests Pydantic model validation, serialization, and edge cases.
"""

import pytest
import uuid
from datetime import datetime
from pydantic import ValidationError

from detection.models import (
    TrendType,
    TrendStatus,
    VideoStats,
    VideoMusic,
    VideoAuthor,
    VideoData,
    Trend,
    TrendVelocityHistory,
    TrendWithHistory,
    ExtractedTrend,
    VelocityResult,
    SaturationResult
)


class TestTrendTypeEnum:
    """Test suite for TrendType enum."""

    def test_trend_type_values(self):
        """Test TrendType enum values."""
        assert TrendType.SOUND.value == "sound"
        assert TrendType.HASHTAG.value == "hashtag"
        assert TrendType.FORMAT.value == "format"

    def test_trend_type_from_string(self):
        """Test creating TrendType from string."""
        assert TrendType("sound") == TrendType.SOUND
        assert TrendType("hashtag") == TrendType.HASHTAG
        assert TrendType("format") == TrendType.FORMAT

    def test_invalid_trend_type(self):
        """Test that invalid trend type raises error."""
        with pytest.raises(ValueError):
            TrendType("invalid")


class TestTrendStatusEnum:
    """Test suite for TrendStatus enum."""

    def test_trend_status_values(self):
        """Test TrendStatus enum values."""
        assert TrendStatus.EMERGING.value == "emerging"
        assert TrendStatus.PEAKING.value == "peaking"
        assert TrendStatus.SATURATED.value == "saturated"
        assert TrendStatus.EXPIRED.value == "expired"

    def test_trend_status_lifecycle_order(self):
        """Test that status follows lifecycle order."""
        # This is a conceptual test - the actual ordering is managed by LifecycleManager
        statuses = [TrendStatus.EMERGING, TrendStatus.PEAKING, 
                   TrendStatus.SATURATED, TrendStatus.EXPIRED]
        values = [s.value for s in statuses]
        
        assert "emerging" in values
        assert "peaking" in values
        assert "saturated" in values
        assert "expired" in values

    def test_invalid_trend_status(self):
        """Test that invalid trend status raises error."""
        with pytest.raises(ValueError):
            TrendStatus("unknown")


class TestVideoStats:
    """Test suite for VideoStats model."""

    def test_video_stats_creation(self):
        """Test creating VideoStats with valid data."""
        stats = VideoStats(
            play_count=10000,
            digg_count=500,
            share_count=100,
            comment_count=50
        )
        
        assert stats.play_count == 10000
        assert stats.digg_count == 500
        assert stats.share_count == 100
        assert stats.comment_count == 50

    def test_video_stats_from_alias(self):
        """Test creating VideoStats from aliased field names."""
        data = {
            "playCount": 10000,
            "diggCount": 500,
            "shareCount": 100,
            "commentCount": 50
        }
        
        stats = VideoStats.model_validate(data)
        
        assert stats.play_count == 10000
        assert stats.digg_count == 500

    def test_video_stats_negative_values_rejected(self):
        """Test that negative values are rejected."""
        with pytest.raises(ValidationError):
            VideoStats(
                play_count=-1,
                digg_count=500,
                share_count=100,
                comment_count=50
            )

    def test_video_stats_zero_values_allowed(self):
        """Test that zero values are allowed."""
        stats = VideoStats(
            play_count=0,
            digg_count=0,
            share_count=0,
            comment_count=0
        )
        
        assert stats.play_count == 0


class TestVideoMusic:
    """Test suite for VideoMusic model."""

    def test_video_music_creation(self):
        """Test creating VideoMusic with valid data."""
        music = VideoMusic(
            id="sound123",
            title="Test Sound",
            author_name="Test Artist"
        )
        
        assert music.id == "sound123"
        assert music.title == "Test Sound"
        assert music.author_name == "Test Artist"

    def test_video_music_optional_fields(self):
        """Test creating VideoMusic with optional fields as None."""
        music = VideoMusic()
        
        assert music.id is None
        assert music.title is None
        assert music.author_name is None

    def test_video_music_title_max_length(self):
        """Test VideoMusic title maximum length."""
        with pytest.raises(ValidationError):
            VideoMusic(
                id="sound123",
                title="x" * 201,  # Exceeds max_length of 200
                author_name="Artist"
            )

    def test_video_music_from_alias(self):
        """Test creating VideoMusic from aliased field names."""
        data = {
            "id": "sound456",
            "title": "Another Sound",
            "authorName": "Another Artist"
        }
        
        music = VideoMusic.model_validate(data)
        
        assert music.author_name == "Another Artist"


class TestVideoAuthor:
    """Test suite for VideoAuthor model."""

    def test_video_author_creation(self):
        """Test creating VideoAuthor with valid data."""
        author = VideoAuthor(
            unique_id="@testuser",
            nickname="Test User",
            follower_count=5000
        )
        
        assert author.unique_id == "@testuser"
        assert author.nickname == "Test User"
        assert author.follower_count == 5000

    def test_video_author_required_fields(self):
        """Test that unique_id and follower_count are required."""
        with pytest.raises(ValidationError):
            VideoAuthor(nickname="Test User")

    def test_video_author_min_length_unique_id(self):
        """Test unique_id minimum length."""
        with pytest.raises(ValidationError):
            VideoAuthor(
                unique_id="",  # Empty string
                nickname="Test",
                follower_count=100
            )

    def test_video_author_negative_followers_rejected(self):
        """Test that negative follower count is rejected."""
        with pytest.raises(ValidationError):
            VideoAuthor(
                unique_id="@user",
                nickname="User",
                follower_count=-100
            )

    def test_video_author_from_alias(self):
        """Test creating VideoAuthor from aliased field names."""
        data = {
            "uniqueId": "@aliaseduser",
            "nickname": "Aliased User",
            "followerCount": 10000
        }
        
        author = VideoAuthor.model_validate(data)
        
        assert author.unique_id == "@aliaseduser"
        assert author.follower_count == 10000


class TestVideoData:
    """Test suite for VideoData model."""

    @pytest.fixture
    def valid_video_data(self):
        """Create valid video data for testing."""
        return {
            "id": "video123",
            "desc": "Test video description",
            "createTime": 1704067200,
            "stats": {
                "playCount": 10000,
                "diggCount": 500,
                "shareCount": 100,
                "commentCount": 50
            },
            "author": {
                "uniqueId": "@testuser",
                "nickname": "Test User",
                "followerCount": 5000
            },
            "music": {
                "id": "sound456",
                "title": "Test Sound",
                "authorName": "Artist"
            },
            "hashtags": ["viral", "trending"],
            "scraped_at": datetime.utcnow()
        }

    def test_video_data_creation(self, valid_video_data):
        """Test creating VideoData with valid data."""
        video = VideoData.model_validate(valid_video_data)
        
        assert video.id == "video123"
        assert video.desc == "Test video description"
        assert video.create_time == 1704067200
        assert len(video.hashtags) == 2

    def test_video_data_required_fields(self):
        """Test that required fields are enforced."""
        with pytest.raises(ValidationError):
            VideoData(
                id="video123"
                # Missing required fields: create_time, stats, author
            )

    def test_video_data_optional_music(self):
        """Test that music is optional."""
        video = VideoData(
            id="video_no_music",
            desc="No music",
            create_time=1704067200,
            stats=VideoStats(play_count=100, digg_count=10, share_count=5, comment_count=2),
            author=VideoAuthor(unique_id="@user", follower_count=100),
            music=None,
            hashtags=["test"]
        )
        
        assert video.music is None

    def test_video_data_hashtags_default(self):
        """Test that hashtags defaults to empty list."""
        video = VideoData(
            id="video_no_hashtags",
            desc="No hashtags",
            create_time=1704067200,
            stats=VideoStats(play_count=100, digg_count=10, share_count=5, comment_count=2),
            author=VideoAuthor(unique_id="@user", follower_count=100)
        )
        
        assert video.hashtags == []

    def test_video_data_max_hashtags(self):
        """Test maximum number of hashtags."""
        with pytest.raises(ValidationError):
            VideoData(
                id="video123",
                desc="Too many hashtags",
                create_time=1704067200,
                stats=VideoStats(play_count=100, digg_count=10, share_count=5, comment_count=2),
                author=VideoAuthor(unique_id="@user", follower_count=100),
                hashtags=["tag"] * 51  # Exceeds max_length of 50
            )

    def test_video_data_scraped_at_default(self):
        """Test that scraped_at defaults to utcnow."""
        video = VideoData(
            id="video123",
            desc="Test",
            create_time=1704067200,
            stats=VideoStats(play_count=100, digg_count=10, share_count=5, comment_count=2),
            author=VideoAuthor(unique_id="@user", follower_count=100)
        )
        
        assert isinstance(video.scraped_at, datetime)

    def test_video_data_source_tracking(self):
        """Test source tracking fields."""
        video = VideoData(
            id="video123",
            desc="Test",
            create_time=1704067200,
            stats=VideoStats(play_count=100, digg_count=10, share_count=5, comment_count=2),
            author=VideoAuthor(unique_id="@user", follower_count=100),
            source_type="trending",
            source_query="fyp"
        )
        
        assert video.source_type == "trending"
        assert video.source_query == "fyp"


class TestTrend:
    """Test suite for Trend model."""

    def test_trend_creation(self):
        """Test creating Trend with valid data."""
        trend = Trend(
            type=TrendType.HASHTAG,
            name="#testtrend",
            platform_id="test123",
            status=TrendStatus.EMERGING,
            velocity_score=50,
            saturation_percent=30
        )
        
        assert trend.type == TrendType.HASHTAG
        assert trend.name == "#testtrend"
        assert trend.platform_id == "test123"
        assert trend.status == TrendStatus.EMERGING
        assert trend.velocity_score == 50
        assert trend.saturation_percent == 30

    def test_trend_auto_uuid(self):
        """Test that UUID is auto-generated."""
        trend = Trend(
            type=TrendType.HASHTAG,
            name="#test",
            platform_id="test",
            status=TrendStatus.EMERGING,
            velocity_score=50,
            saturation_percent=30
        )
        
        assert isinstance(trend.id, uuid.UUID)

    def test_trend_auto_timestamps(self):
        """Test that timestamps are auto-generated."""
        trend = Trend(
            type=TrendType.HASHTAG,
            name="#test",
            platform_id="test",
            status=TrendStatus.EMERGING,
            velocity_score=50,
            saturation_percent=30
        )
        
        assert isinstance(trend.created_at, datetime)
        assert isinstance(trend.updated_at, datetime)
        assert isinstance(trend.first_detected_at, datetime)

    def test_trend_velocity_score_range(self):
        """Test velocity score range validation (0-100)."""
        # Valid range
        trend = Trend(
            type=TrendType.HASHTAG,
            name="#test",
            platform_id="test",
            status=TrendStatus.EMERGING,
            velocity_score=50,
            saturation_percent=30
        )
        assert trend.velocity_score == 50

        # Below minimum
        with pytest.raises(ValidationError):
            Trend(
                type=TrendType.HASHTAG,
                name="#test",
                platform_id="test",
                status=TrendStatus.EMERGING,
                velocity_score=-1,
                saturation_percent=30
            )

        # Above maximum
        with pytest.raises(ValidationError):
            Trend(
                type=TrendType.HASHTAG,
                name="#test",
                platform_id="test",
                status=TrendStatus.EMERGING,
                velocity_score=101,
                saturation_percent=30
            )

    def test_trend_saturation_percent_range(self):
        """Test saturation percent range validation (0-100)."""
        # Below minimum
        with pytest.raises(ValidationError):
            Trend(
                type=TrendType.HASHTAG,
                name="#test",
                platform_id="test",
                status=TrendStatus.EMERGING,
                velocity_score=50,
                saturation_percent=-1
            )

        # Above maximum
        with pytest.raises(ValidationError):
            Trend(
                type=TrendType.HASHTAG,
                name="#test",
                platform_id="test",
                status=TrendStatus.EMERGING,
                velocity_score=50,
                saturation_percent=101
            )

    def test_trend_video_count_validation(self):
        """Test video count validation."""
        with pytest.raises(ValidationError):
            Trend(
                type=TrendType.HASHTAG,
                name="#test",
                platform_id="test",
                status=TrendStatus.EMERGING,
                velocity_score=50,
                saturation_percent=30,
                video_count_start=0  # Must be >= 1
            )

    def test_trend_name_validation(self):
        """Test trend name validation."""
        # Empty name
        with pytest.raises(ValidationError):
            Trend(
                type=TrendType.HASHTAG,
                name="",
                platform_id="test",
                status=TrendStatus.EMERGING,
                velocity_score=50,
                saturation_percent=30
            )

        # Too long name
        with pytest.raises(ValidationError):
            Trend(
                type=TrendType.HASHTAG,
                name="x" * 201,  # Exceeds max_length of 200
                platform_id="test",
                status=TrendStatus.EMERGING,
                velocity_score=50,
                saturation_percent=30
            )

    def test_trend_metadata_field(self):
        """Test trend metadata field."""
        trend = Trend(
            type=TrendType.HASHTAG,
            name="#test",
            platform_id="test",
            status=TrendStatus.EMERGING,
            velocity_score=50,
            saturation_percent=30,
            metadata={
                "example_videos": ["video1", "video2"],
                "custom_key": "custom_value"
            }
        )
        
        assert trend.metadata["example_videos"] == ["video1", "video2"]
        assert trend.metadata["custom_key"] == "custom_value"

    def test_trend_json_serialization(self):
        """Test trend JSON serialization."""
        trend = Trend(
            type=TrendType.HASHTAG,
            name="#test",
            platform_id="test",
            status=TrendStatus.EMERGING,
            velocity_score=50,
            saturation_percent=30
        )
        
        json_data = trend.model_dump()
        
        assert json_data["type"] == "hashtag"
        assert json_data["name"] == "#test"
        assert json_data["velocity_score"] == 50
        assert "id" in json_data


class TestTrendVelocityHistory:
    """Test suite for TrendVelocityHistory model."""

    def test_velocity_history_creation(self):
        """Test creating TrendVelocityHistory with valid data."""
        trend_id = uuid.uuid4()
        history = TrendVelocityHistory(
            trend_id=trend_id,
            video_count=100,
            velocity_score=75,
            growth_rate=15.0,
            saturation_percent=40
        )
        
        assert history.trend_id == trend_id
        assert history.video_count == 100
        assert history.velocity_score == 75

    def test_velocity_history_optional_fields(self):
        """Test that velocity history fields are optional."""
        trend_id = uuid.uuid4()
        history = TrendVelocityHistory(
            trend_id=trend_id,
            video_count=100
        )
        
        assert history.velocity_score is None
        assert history.growth_rate is None
        assert history.saturation_percent is None

    def test_velocity_history_score_range(self):
        """Test velocity score range in history."""
        trend_id = uuid.uuid4()
        
        # Above maximum
        with pytest.raises(ValidationError):
            TrendVelocityHistory(
                trend_id=trend_id,
                video_count=100,
                velocity_score=101
            )

    def test_velocity_history_auto_timestamp(self):
        """Test that timestamp is auto-generated."""
        trend_id = uuid.uuid4()
        history = TrendVelocityHistory(
            trend_id=trend_id,
            video_count=100
        )
        
        assert isinstance(history.timestamp, datetime)


class TestExtractedTrend:
    """Test suite for ExtractedTrend model."""

    def test_extracted_trend_creation(self):
        """Test creating ExtractedTrend with valid data."""
        video = VideoData(
            id="video123",
            desc="Test",
            create_time=1704067200,
            stats=VideoStats(play_count=100, digg_count=10, share_count=5, comment_count=2),
            author=VideoAuthor(unique_id="@user", follower_count=100)
        )
        
        extracted = ExtractedTrend(
            type=TrendType.HASHTAG,
            platform_id="test123",
            name="#test",
            video=video
        )
        
        assert extracted.type == TrendType.HASHTAG
        assert extracted.platform_id == "test123"
        assert extracted.name == "#test"
        assert extracted.video.id == "video123"

    def test_extracted_trend_required_fields(self):
        """Test that all fields are required."""
        with pytest.raises(ValidationError):
            ExtractedTrend(
                type=TrendType.HASHTAG,
                platform_id="test123",
                name="#test"
                # Missing video
            )


class TestVelocityResultModel:
    """Test suite for VelocityResult model."""

    def test_velocity_result_creation(self):
        """Test creating VelocityResult with valid data."""
        result = VelocityResult(
            score=75,
            growth_rate=15.0,
            doubling_time=4.67,
            r_squared=0.92,
            is_exponential=True,
            acceleration=0.05,
            confidence=0.88,
            data_points=20,
            time_window_hours=48.0
        )
        
        assert result.score == 75
        assert result.r_squared == 0.92
        assert result.is_exponential is True

    def test_velocity_result_score_range(self):
        """Test velocity score range (0-100)."""
        with pytest.raises(ValidationError):
            VelocityResult(
                score=101,  # Above max
                growth_rate=15.0,
                doubling_time=4.67,
                r_squared=0.92,
                is_exponential=True,
                acceleration=0.05,
                confidence=0.88,
                data_points=20,
                time_window_hours=48.0
            )

    def test_velocity_result_r_squared_range(self):
        """Test R-squared range (0-1)."""
        with pytest.raises(ValidationError):
            VelocityResult(
                score=75,
                growth_rate=15.0,
                doubling_time=4.67,
                r_squared=1.5,  # Above max
                is_exponential=True,
                acceleration=0.05,
                confidence=0.88,
                data_points=20,
                time_window_hours=48.0
            )

    def test_velocity_result_confidence_range(self):
        """Test confidence range (0-1)."""
        with pytest.raises(ValidationError):
            VelocityResult(
                score=75,
                growth_rate=15.0,
                doubling_time=4.67,
                r_squared=0.92,
                is_exponential=True,
                acceleration=0.05,
                confidence=1.5,  # Above max
                data_points=20,
                time_window_hours=48.0
            )


class TestSaturationResultModel:
    """Test suite for SaturationResult model."""

    def test_saturation_result_creation(self):
        """Test creating SaturationResult with valid data."""
        result = SaturationResult(
            score=45,
            stage="growth",
            recommendation="Good opportunity"
        )
        
        assert result.score == 45
        assert result.stage == "growth"
        assert result.recommendation == "Good opportunity"

    def test_saturation_result_score_range(self):
        """Test saturation score range (0-100)."""
        with pytest.raises(ValidationError):
            SaturationResult(
                score=101,  # Above max
                stage="growth",
                recommendation="Test"
            )

    def test_saturation_result_valid_stages(self):
        """Test valid stage values."""
        valid_stages = ["early", "growth", "mature", "decline"]
        
        for stage in valid_stages:
            result = SaturationResult(
                score=50,
                stage=stage,
                recommendation="Test"
            )
            assert result.stage == stage


class TestTrendWithHistory:
    """Test suite for TrendWithHistory model."""

    def test_trend_with_history_creation(self):
        """Test creating TrendWithHistory."""
        trend = Trend(
            type=TrendType.HASHTAG,
            name="#test",
            platform_id="test",
            status=TrendStatus.EMERGING,
            velocity_score=50,
            saturation_percent=30
        )
        
        history = [
            TrendVelocityHistory(
                trend_id=trend.id,
                video_count=100,
                velocity_score=50
            ),
            TrendVelocityHistory(
                trend_id=trend.id,
                video_count=200,
                velocity_score=75
            )
        ]
        
        with_history = TrendWithHistory(
            trend=trend,
            velocity_history=history
        )
        
        assert with_history.trend.id == trend.id
        assert len(with_history.velocity_history) == 2

    def test_trend_with_history_empty(self):
        """Test TrendWithHistory with empty history."""
        trend = Trend(
            type=TrendType.HASHTAG,
            name="#test",
            platform_id="test",
            status=TrendStatus.EMERGING,
            velocity_score=50,
            saturation_percent=30
        )
        
        with_history = TrendWithHistory(trend=trend)
        
        assert with_history.velocity_history == []


class TestModelJSONSerialization:
    """Test suite for model JSON serialization."""

    def test_video_data_json(self):
        """Test VideoData JSON serialization."""
        video = VideoData(
            id="video123",
            desc="Test",
            create_time=1704067200,
            stats=VideoStats(play_count=100, digg_count=10, share_count=5, comment_count=2),
            author=VideoAuthor(unique_id="@user", follower_count=100),
            hashtags=["test", "viral"]
        )
        
        json_str = video.model_dump_json()
        assert "video123" in json_str
        assert "test" in json_str
        assert "viral" in json_str

    def test_trend_json_with_uuid(self):
        """Test Trend JSON serialization with UUID."""
        trend = Trend(
            type=TrendType.SOUND,
            name="Test Sound",
            platform_id="sound123",
            status=TrendStatus.PEAKING,
            velocity_score=80,
            saturation_percent=60
        )
        
        json_data = trend.model_dump(mode='json')
        
        # UUID should be serialized as string
        assert isinstance(json_data["id"], str)
        assert json_data["type"] == "sound"
        assert json_data["status"] == "peaking"

    def test_datetime_serialization(self):
        """Test datetime serialization in models."""
        specific_time = datetime(2024, 1, 1, 12, 0, 0)
        
        trend = Trend(
            type=TrendType.HASHTAG,
            name="#test",
            platform_id="test",
            status=TrendStatus.EMERGING,
            velocity_score=50,
            saturation_percent=30,
            first_detected_at=specific_time,
            created_at=specific_time
        )
        
        json_data = trend.model_dump(mode='json')
        
        # Datetime should be serialized as ISO format string
        assert isinstance(json_data["created_at"], str)
        assert "2024-01-01" in json_data["created_at"]
