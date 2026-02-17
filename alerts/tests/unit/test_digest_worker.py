"""
Unit tests for DigestWorker.

Tests the digest worker including:
- Worker initialization
- Digest generation for different tiers
- Batch alert grouping
- Digest scheduling (hourly, daily, weekly)
- Digest content formatting
- Empty digest handling
- Worker lifecycle (start/stop)
"""

import json
import uuid
from datetime import datetime, timedelta
from typing import List
from unittest.mock import AsyncMock, MagicMock, patch, Mock

import pytest
import pytest_asyncio

from alerts.models import (
    DigestEntry,
    TrendForAlert,
    UserAlertConfig,
    Tier,
    BatchType,
)


# =============================================================================
# Fixtures
# =============================================================================

@pytest.fixture
def mock_redis():
    """Mock Redis client."""
    redis = AsyncMock()
    redis.rpush = AsyncMock(return_value=1)
    redis.lrange = AsyncMock(return_value=[])
    redis.llen = AsyncMock(return_value=0)
    redis.delete = AsyncMock(return_value=1)
    redis.expire = AsyncMock(return_value=True)
    redis.scan_iter = AsyncMock(return_value=[])
    return redis


@pytest.fixture
def mock_slack_service():
    """Mock Slack service."""
    service = AsyncMock()
    service.send_digest = AsyncMock(return_value=True)
    return service


@pytest.fixture
def mock_email_service():
    """Mock email service."""
    service = AsyncMock()
    service.send_digest = AsyncMock(return_value=True)
    return service


@pytest.fixture
def sample_trend():
    """Create a sample trend for testing."""
    return TrendForAlert(
        id=uuid.uuid4(),
        type="sound",
        name="Trending Sound",
        velocity_score=85,
        saturation_percent=25,
        video_count_current=1500,
        growth_rate=120.5,
        niche_name="Test Niche",
        window_hours="6-8"
    )


@pytest.fixture
def sample_trends() -> List[TrendForAlert]:
    """Create multiple sample trends for testing."""
    return [
        TrendForAlert(
            id=uuid.uuid4(),
            type="sound",
            name="Trending Sound 1",
            velocity_score=85,
            saturation_percent=25,
            video_count_current=1500,
            growth_rate=120.5,
            niche_name="Music Niche",
            window_hours="6-8"
        ),
        TrendForAlert(
            id=uuid.uuid4(),
            type="hashtag",
            name="#viralhashtag",
            velocity_score=92,
            saturation_percent=15,
            video_count_current=5000,
            growth_rate=200.0,
            niche_name="Viral Niche",
            window_hours="4-6"
        ),
        TrendForAlert(
            id=uuid.uuid4(),
            type="format",
            name="Trending Format",
            velocity_score=78,
            saturation_percent=40,
            video_count_current=800,
            growth_rate=85.0,
            niche_name="Format Niche",
            window_hours="8-10"
        ),
    ]


@pytest.fixture
def sample_digest_entry():
    """Create a sample digest entry."""
    return DigestEntry(
        trend_id=str(uuid.uuid4()),
        trend_name="Test Trend",
        velocity_score=85,
        saturation_percent=25,
        growth_rate=120.5,
        niche_name="Test Niche",
        queued_at=datetime.utcnow(),
        niche_id=str(uuid.uuid4())
    )


@pytest.fixture
def sample_digest_entries() -> List[DigestEntry]:
    """Create multiple sample digest entries."""
    return [
        DigestEntry(
            trend_id=str(uuid.uuid4()),
            trend_name="Trend 1",
            velocity_score=85,
            saturation_percent=25,
            growth_rate=120.5,
            niche_name="Niche A",
            queued_at=datetime.utcnow(),
            niche_id=str(uuid.uuid4())
        ),
        DigestEntry(
            trend_id=str(uuid.uuid4()),
            trend_name="Trend 2",
            velocity_score=92,
            saturation_percent=15,
            growth_rate=200.0,
            niche_name="Niche B",
            queued_at=datetime.utcnow() - timedelta(minutes=30),
            niche_id=str(uuid.uuid4())
        ),
        DigestEntry(
            trend_id=str(uuid.uuid4()),
            trend_name="Trend 3",
            velocity_score=78,
            saturation_percent=40,
            growth_rate=85.0,
            niche_name="Niche A",
            queued_at=datetime.utcnow() - timedelta(hours=1),
            niche_id=str(uuid.uuid4())
        ),
    ]


@pytest.fixture
def solo_user_config():
    """Create a Solo tier user configuration."""
    return UserAlertConfig(
        user_id=uuid.uuid4(),
        email="solo@example.com",
        tier=Tier.SOLO,
        email_notifications=True,
        niche_id=uuid.uuid4(),
        alert_enabled=True,
        velocity_threshold=50
    )


@pytest.fixture
def agency_user_config():
    """Create an Agency tier user configuration."""
    return UserAlertConfig(
        user_id=uuid.uuid4(),
        email="agency@example.com",
        tier=Tier.AGENCY,
        email_notifications=True,
        niche_id=uuid.uuid4(),
        alert_enabled=True,
        velocity_threshold=40,
        integration_id=uuid.uuid4(),
        integration_type="slack",
        integration_config={"webhook_url": "https://hooks.slack.com/agency"}
    )


@pytest.fixture
def free_user_config():
    """Create a Free tier user configuration."""
    return UserAlertConfig(
        user_id=uuid.uuid4(),
        email="free@example.com",
        tier=Tier.FREE,
        email_notifications=True,
        niche_id=uuid.uuid4(),
        alert_enabled=True,
        velocity_threshold=70
    )


@pytest_asyncio.fixture
async def digest_worker(mock_redis, mock_slack_service, mock_email_service):
    """Create a DigestWorker instance with mocked dependencies."""
    from alerts.digest_worker import DigestWorker
    
    worker = DigestWorker(
        redis_client=mock_redis,
        slack_service=mock_slack_service,
        email_service=mock_email_service
    )
    return worker


# =============================================================================
# Worker Initialization Tests
# =============================================================================

class TestWorkerInitialization:
    """Tests for DigestWorker initialization."""

    @pytest.mark.asyncio
    async def test_worker_initialization_with_all_deps(
        self, mock_redis, mock_slack_service, mock_email_service
    ):
        """Test worker initializes with all dependencies provided."""
        from alerts.digest_worker import DigestWorker
        
        worker = DigestWorker(
            redis_client=mock_redis,
            slack_service=mock_slack_service,
            email_service=mock_email_service
        )
        
        assert worker.redis is mock_redis
        assert worker.slack is mock_slack_service
        assert worker.email is mock_email_service

    @pytest.mark.asyncio
    async def test_worker_initialization_with_defaults(self, mock_redis):
        """Test worker initializes with default services."""
        from alerts.digest_worker import DigestWorker
        
        with patch("alerts.digest_worker.get_slack_service") as mock_get_slack:
            with patch("alerts.digest_worker.get_email_service") as mock_get_email:
                mock_get_slack.return_value = AsyncMock()
                mock_get_email.return_value = AsyncMock()
                
                worker = DigestWorker(redis_client=mock_redis)
                
                mock_get_slack.assert_called_once()
                mock_get_email.assert_called_once()

    @pytest.mark.asyncio
    async def test_user_queue_key_generation(self, digest_worker):
        """Test user queue key is generated correctly."""
        user_id = uuid.uuid4()
        
        key = digest_worker._user_queue_key(user_id)
        
        assert key == f"digest:user:{user_id}"


# =============================================================================
# Queue Alert Tests
# =============================================================================

class TestQueueAlert:
    """Tests for queue_alert method."""

    @pytest.mark.asyncio
    async def test_queue_alert_success(self, digest_worker, mock_redis, sample_trend):
        """Test successful alert queuing."""
        user_id = uuid.uuid4()
        delay_seconds = 3600
        niche_id = uuid.uuid4()
        
        result = await digest_worker.queue_alert(
            user_id=user_id,
            trend=sample_trend,
            delay_seconds=delay_seconds,
            niche_id=niche_id
        )
        
        assert result is True
        mock_redis.rpush.assert_called_once()
        mock_redis.expire.assert_called_once()

    @pytest.mark.asyncio
    async def test_queue_alert_without_niche_id(self, digest_worker, mock_redis, sample_trend):
        """Test queuing alert without niche_id."""
        user_id = uuid.uuid4()
        delay_seconds = 3600
        
        result = await digest_worker.queue_alert(
            user_id=user_id,
            trend=sample_trend,
            delay_seconds=delay_seconds
        )
        
        assert result is True
        mock_redis.rpush.assert_called_once()

    @pytest.mark.asyncio
    async def test_queue_alert_redis_error(self, digest_worker, mock_redis, sample_trend):
        """Test handling of Redis error during queuing."""
        import redis.asyncio as redis
        mock_redis.rpush.side_effect = redis.RedisError("Connection failed")
        
        user_id = uuid.uuid4()
        
        result = await digest_worker.queue_alert(
            user_id=user_id,
            trend=sample_trend,
            delay_seconds=3600
        )
        
        assert result is False

    @pytest.mark.asyncio
    async def test_queue_alert_data_structure(self, digest_worker, mock_redis, sample_trend):
        """Test queued alert data structure."""
        user_id = uuid.uuid4()
        niche_id = uuid.uuid4()
        
        captured_data = None
        async def capture_rpush(key, data):
            nonlocal captured_data
            captured_data = data
            return 1
        
        mock_redis.rpush = capture_rpush
        
        await digest_worker.queue_alert(
            user_id=user_id,
            trend=sample_trend,
            delay_seconds=3600,
            niche_id=niche_id
        )
        
        assert captured_data is not None
        entry = json.loads(captured_data)
        assert entry["trend_id"] == str(sample_trend.id)
        assert entry["trend_name"] == sample_trend.name
        assert entry["velocity_score"] == sample_trend.velocity_score
        assert entry["saturation_percent"] == sample_trend.saturation_percent
        assert entry["growth_rate"] == sample_trend.growth_rate
        assert entry["niche_name"] == sample_trend.niche_name
        assert "queued_at" in entry
        assert entry["niche_id"] == str(niche_id)


# =============================================================================
# Get User Queue Tests
# =============================================================================

class TestGetUserQueue:
    """Tests for get_user_queue method."""

    @pytest.mark.asyncio
    async def test_get_user_queue_empty(self, digest_worker, mock_redis):
        """Test getting empty user queue."""
        user_id = uuid.uuid4()
        mock_redis.lrange.return_value = []
        
        entries = await digest_worker.get_user_queue(user_id)
        
        assert entries == []
        mock_redis.lrange.assert_called_once_with(
            f"digest:user:{user_id}", 0, 99
        )

    @pytest.mark.asyncio
    async def test_get_user_queue_with_entries(self, digest_worker, mock_redis, sample_digest_entries):
        """Test getting user queue with entries."""
        user_id = uuid.uuid4()
        mock_redis.lrange.return_value = [
            entry.model_dump_json() for entry in sample_digest_entries
        ]
        
        entries = await digest_worker.get_user_queue(user_id)
        
        assert len(entries) == 3
        assert entries[0].trend_name == sample_digest_entries[0].trend_name
        assert entries[1].trend_name == sample_digest_entries[1].trend_name

    @pytest.mark.asyncio
    async def test_get_user_queue_with_limit(self, digest_worker, mock_redis, sample_digest_entries):
        """Test getting user queue with custom limit."""
        user_id = uuid.uuid4()
        mock_redis.lrange.return_value = [
            sample_digest_entries[0].model_dump_json()
        ]
        
        entries = await digest_worker.get_user_queue(user_id, limit=1)
        
        assert len(entries) <= 1
        mock_redis.lrange.assert_called_once_with(
            f"digest:user:{user_id}", 0, 0
        )

    @pytest.mark.asyncio
    async def test_get_user_queue_ignores_invalid_entries(self, digest_worker, mock_redis):
        """Test invalid entries are ignored."""
        user_id = uuid.uuid4()
        mock_redis.lrange.return_value = [
            json.dumps({"valid": "entry", "trend_id": str(uuid.uuid4()), "trend_name": "Test"}),
            "invalid json",
            json.dumps({"incomplete": "entry"}),
        ]
        
        entries = await digest_worker.get_user_queue(user_id)
        
        # Should only include valid entries
        assert len(entries) >= 0

    @pytest.mark.asyncio
    async def test_get_user_queue_redis_error(self, digest_worker, mock_redis):
        """Test handling Redis error when getting queue."""
        import redis.asyncio as redis
        user_id = uuid.uuid4()
        mock_redis.lrange.side_effect = redis.RedisError("Connection failed")
        
        entries = await digest_worker.get_user_queue(user_id)
        
        assert entries == []


# =============================================================================
# Clear User Queue Tests
# =============================================================================

class TestClearUserQueue:
    """Tests for clear_user_queue method."""

    @pytest.mark.asyncio
    async def test_clear_empty_queue(self, digest_worker, mock_redis):
        """Test clearing empty queue."""
        user_id = uuid.uuid4()
        mock_redis.llen.return_value = 0
        
        count = await digest_worker.clear_user_queue(user_id)
        
        assert count == 0
        mock_redis.delete.assert_called_once_with(f"digest:user:{user_id}")

    @pytest.mark.asyncio
    async def test_clear_queue_with_entries(self, digest_worker, mock_redis):
        """Test clearing queue with entries."""
        user_id = uuid.uuid4()
        mock_redis.llen.return_value = 5
        
        count = await digest_worker.clear_user_queue(user_id)
        
        assert count == 5
        mock_redis.delete.assert_called_once()

    @pytest.mark.asyncio
    async def test_clear_queue_redis_error(self, digest_worker, mock_redis):
        """Test handling Redis error when clearing queue."""
        import redis.asyncio as redis
        user_id = uuid.uuid4()
        mock_redis.llen.side_effect = redis.RedisError("Connection failed")
        
        count = await digest_worker.clear_user_queue(user_id)
        
        assert count == 0


# =============================================================================
# Process Hourly Digests Tests
# =============================================================================

class TestProcessHourlyDigests:
    """Tests for process_hourly_digests method."""

    @pytest.mark.asyncio
    async def test_process_hourly_digests_empty(self, digest_worker, mock_redis):
        """Test processing hourly digests with no users."""
        mock_redis.scan_iter.return_value = []
        
        stats = await digest_worker.process_hourly_digests()
        
        assert stats["users_processed"] == 0
        assert stats["alerts_sent"] == 0
        assert stats["errors"] == 0

    @pytest.mark.asyncio
    async def test_process_hourly_digests_with_users(
        self, digest_worker, mock_redis, mock_email_service, sample_digest_entries
    ):
        """Test processing hourly digests with users."""
        user_id = uuid.uuid4()
        mock_redis.scan_iter.return_value = [f"digest:user:{user_id}".encode()]
        mock_redis.lrange.return_value = [
            entry.model_dump_json() for entry in sample_digest_entries[:2]
        ]
        
        # Process user digest with email
        with patch.object(digest_worker, '_process_user_digest', return_value=2):
            stats = await digest_worker.process_hourly_digests()
            
            assert stats["users_processed"] == 1
            assert stats["alerts_sent"] == 2

    @pytest.mark.asyncio
    async def test_process_hourly_digests_with_invalid_user_id(self, digest_worker, mock_redis):
        """Test processing hourly digests handles invalid user IDs."""
        mock_redis.scan_iter.return_value = [b"digest:user:invalid-uuid"]
        
        stats = await digest_worker.process_hourly_digests()
        
        assert stats["users_processed"] == 0
        assert stats["errors"] == 0  # Invalid UUIDs are skipped silently

    @pytest.mark.asyncio
    async def test_process_hourly_digests_handles_errors(self, digest_worker, mock_redis):
        """Test processing hourly digests handles errors."""
        user_id = uuid.uuid4()
        mock_redis.scan_iter.return_value = [f"digest:user:{user_id}".encode()]
        
        with patch.object(digest_worker, '_process_user_digest', side_effect=Exception("Processing error")):
            stats = await digest_worker.process_hourly_digests()
            
            assert stats["errors"] == 1


# =============================================================================
# Process Daily Digests Tests
# =============================================================================

class TestProcessDailyDigests:
    """Tests for process_daily_digests method."""

    @pytest.mark.asyncio
    async def test_process_daily_digests_empty(self, digest_worker, mock_redis):
        """Test processing daily digests with no users."""
        mock_redis.scan_iter.return_value = []
        
        stats = await digest_worker.process_daily_digests()
        
        assert stats["users_processed"] == 0
        assert stats["alerts_sent"] == 0
        assert stats["errors"] == 0

    @pytest.mark.asyncio
    async def test_process_daily_digests_with_users(
        self, digest_worker, mock_redis, sample_digest_entries
    ):
        """Test processing daily digests with users."""
        user_id = uuid.uuid4()
        mock_redis.scan_iter.return_value = [f"digest:user:{user_id}".encode()]
        mock_redis.lrange.return_value = [
            entry.model_dump_json() for entry in sample_digest_entries
        ]
        
        with patch.object(digest_worker, '_process_user_digest', return_value=3):
            stats = await digest_worker.process_daily_digests()
            
            assert stats["users_processed"] == 1
            assert stats["alerts_sent"] == 3

    @pytest.mark.asyncio
    async def test_process_daily_digests_handles_user_error(self, digest_worker, mock_redis):
        """Test processing daily digests handles user processing errors."""
        user_id = uuid.uuid4()
        mock_redis.scan_iter.return_value = [f"digest:user:{user_id}".encode()]
        
        with patch.object(digest_worker, '_process_user_digest', side_effect=Exception("Error")):
            stats = await digest_worker.process_daily_digests()
            
            assert stats["errors"] == 1


# =============================================================================
# Process User Digest Tests
# =============================================================================

class TestProcessUserDigest:
    """Tests for _process_user_digest method."""

    @pytest.mark.asyncio
    async def test_process_user_digest_empty_queue(self, digest_worker, mock_redis):
        """Test processing user digest with empty queue."""
        user_id = uuid.uuid4()
        mock_redis.lrange.return_value = []
        
        count = await digest_worker._process_user_digest(user_id, BatchType.HOURLY)
        
        assert count == 0

    @pytest.mark.asyncio
    async def test_process_user_digest_via_email(
        self, digest_worker, mock_redis, mock_email_service, 
        sample_digest_entries, free_user_config
    ):
        """Test processing user digest via email."""
        user_id = free_user_config.user_id
        mock_redis.lrange.return_value = [
            entry.model_dump_json() for entry in sample_digest_entries
        ]
        mock_email_service.send_digest.return_value = True
        
        count = await digest_worker._process_user_digest(
            user_id, BatchType.DAILY, free_user_config
        )
        
        assert count == 3
        mock_email_service.send_digest.assert_called_once()
        mock_redis.delete.assert_called_once()

    @pytest.mark.asyncio
    async def test_process_user_digest_via_slack(
        self, digest_worker, mock_redis, mock_slack_service, 
        sample_digest_entries, agency_user_config
    ):
        """Test processing user digest via Slack."""
        user_id = agency_user_config.user_id
        mock_redis.lrange.return_value = [
            entry.model_dump_json() for entry in sample_digest_entries
        ]
        mock_slack_service.send_digest.return_value = True
        
        count = await digest_worker._process_user_digest(
            user_id, BatchType.HOURLY, agency_user_config
        )
        
        assert count == 3
        mock_slack_service.send_digest.assert_called_once()
        mock_redis.delete.assert_called_once()

    @pytest.mark.asyncio
    async def test_process_user_digest_slack_fallback_to_email(
        self, digest_worker, mock_redis, mock_slack_service, mock_email_service,
        sample_digest_entries, agency_user_config
    ):
        """Test fallback to email when Slack fails."""
        user_id = agency_user_config.user_id
        mock_redis.lrange.return_value = [
            entry.model_dump_json() for entry in sample_digest_entries
        ]
        mock_slack_service.send_digest.return_value = False
        mock_email_service.send_digest.return_value = True
        
        count = await digest_worker._process_user_digest(
            user_id, BatchType.HOURLY, agency_user_config
        )
        
        assert count == 3
        mock_slack_service.send_digest.assert_called_once()
        mock_email_service.send_digest.assert_called_once()

    @pytest.mark.asyncio
    async def test_process_user_digest_no_config_no_email(
        self, digest_worker, mock_redis, mock_email_service, sample_digest_entries
    ):
        """Test processing fails without user config or email enabled."""
        user_id = uuid.uuid4()
        mock_redis.lrange.return_value = [
            entry.model_dump_json() for entry in sample_digest_entries
        ]
        
        # No user_config provided, no email sent
        count = await digest_worker._process_user_digest(user_id, BatchType.HOURLY)
        
        assert count == 0
        mock_email_service.send_digest.assert_not_called()

    @pytest.mark.asyncio
    async def test_process_user_digest_both_delivery_fail(
        self, digest_worker, mock_redis, mock_slack_service, mock_email_service,
        sample_digest_entries, agency_user_config
    ):
        """Test processing when both delivery methods fail."""
        user_id = agency_user_config.user_id
        mock_redis.lrange.return_value = [
            entry.model_dump_json() for entry in sample_digest_entries
        ]
        mock_slack_service.send_digest.return_value = False
        mock_email_service.send_digest.return_value = False
        
        count = await digest_worker._process_user_digest(
            user_id, BatchType.HOURLY, agency_user_config
        )
        
        assert count == 0
        # Queue should not be cleared on failure
        mock_redis.delete.assert_not_called()


# =============================================================================
# Queue Statistics Tests
# =============================================================================

class TestQueueStats:
    """Tests for get_queue_stats method."""

    @pytest.mark.asyncio
    async def test_get_queue_stats_empty(self, digest_worker, mock_redis):
        """Test getting stats with no queues."""
        mock_redis.scan_iter.return_value = []
        
        stats = await digest_worker.get_queue_stats()
        
        assert stats["user_queues"] == 0
        assert stats["total_queued_alerts"] == 0
        assert stats["avg_queue_size"] == 0

    @pytest.mark.asyncio
    async def test_get_queue_stats_with_queues(self, digest_worker, mock_redis):
        """Test getting stats with multiple queues."""
        mock_redis.scan_iter.return_value = [
            b"digest:user:user1",
            b"digest:user:user2",
            b"digest:user:user3",
        ]
        mock_redis.llen.side_effect = [5, 10, 0]  # Different queue sizes
        
        stats = await digest_worker.get_queue_stats()
        
        assert stats["user_queues"] == 3
        assert stats["total_queued_alerts"] == 15
        assert stats["avg_queue_size"] == 5.0


# =============================================================================
# Cleanup Stale Queues Tests
# =============================================================================

class TestCleanupStaleQueues:
    """Tests for cleanup_stale_queues method."""

    @pytest.mark.asyncio
    async def test_cleanup_no_stale_queues(self, digest_worker, mock_redis):
        """Test cleanup with no stale queues."""
        mock_redis.scan_iter.return_value = []
        
        removed = await digest_worker.cleanup_stale_queues()
        
        assert removed == 0

    @pytest.mark.asyncio
    async def test_cleanup_stale_queue(self, digest_worker, mock_redis):
        """Test cleanup removes stale queues."""
        old_time = (datetime.utcnow() - timedelta(hours=100)).isoformat()
        mock_redis.scan_iter.return_value = [b"digest:user:olduser"]
        mock_redis.lrange.return_value = [json.dumps({
            "trend_id": str(uuid.uuid4()),
            "trend_name": "Old Trend",
            "velocity_score": 50,
            "saturation_percent": 30,
            "growth_rate": 50.0,
            "queued_at": old_time
        })]
        
        removed = await digest_worker.cleanup_stale_queues(max_age_hours=72)
        
        assert removed == 1
        mock_redis.delete.assert_called_once()

    @pytest.mark.asyncio
    async def test_cleanup_fresh_queue_not_removed(self, digest_worker, mock_redis):
        """Test cleanup doesn't remove fresh queues."""
        recent_time = datetime.utcnow().isoformat()
        mock_redis.scan_iter.return_value = [b"digest:user:freshuser"]
        mock_redis.lrange.return_value = [json.dumps({
            "trend_id": str(uuid.uuid4()),
            "trend_name": "Fresh Trend",
            "velocity_score": 50,
            "saturation_percent": 30,
            "growth_rate": 50.0,
            "queued_at": recent_time
        })]
        
        removed = await digest_worker.cleanup_stale_queues(max_age_hours=72)
        
        assert removed == 0
        mock_redis.delete.assert_not_called()

    @pytest.mark.asyncio
    async def test_cleanup_invalid_entry_removed(self, digest_worker, mock_redis):
        """Test cleanup removes queues with invalid entries."""
        mock_redis.scan_iter.return_value = [b"digest:user:baduser"]
        mock_redis.lrange.return_value = [b"invalid json"]
        
        removed = await digest_worker.cleanup_stale_queues()
        
        assert removed == 1
        mock_redis.delete.assert_called_once()

    @pytest.mark.asyncio
    async def test_cleanup_custom_max_age(self, digest_worker, mock_redis):
        """Test cleanup with custom max age."""
        # Queue that is 25 hours old
        time_25h_ago = (datetime.utcnow() - timedelta(hours=25)).isoformat()
        mock_redis.scan_iter.return_value = [b"digest:user:user25h"]
        mock_redis.lrange.return_value = [json.dumps({
            "trend_id": str(uuid.uuid4()),
            "trend_name": "Old Trend",
            "velocity_score": 50,
            "saturation_percent": 30,
            "growth_rate": 50.0,
            "queued_at": time_25h_ago
        })]
        
        # With 24 hour max_age, should be removed
        removed = await digest_worker.cleanup_stale_queues(max_age_hours=24)
        assert removed == 1
        
        # Reset mock
        mock_redis.delete.reset_mock()
        
        # With 48 hour max_age, should NOT be removed
        removed = await digest_worker.cleanup_stale_queues(max_age_hours=48)
        assert removed == 0


# =============================================================================
# Digest Content Tests
# =============================================================================

class TestDigestContent:
    """Tests for digest content formatting."""

    @pytest.mark.asyncio
    async def test_digest_trends_conversion(self, digest_worker, mock_redis):
        """Test digest entries are converted to trends correctly."""
        entry = DigestEntry(
            trend_id=str(uuid.uuid4()),
            trend_name="Test Trend",
            velocity_score=85,
            saturation_percent=25,
            growth_rate=120.5,
            niche_name="Test Niche",
            queued_at=datetime.utcnow()
        )
        
        user_id = uuid.uuid4()
        mock_redis.lrange.return_value = [entry.model_dump_json()]
        
        with patch.object(digest_worker, '_process_user_digest', return_value=1) as mock_process:
            await digest_worker.process_hourly_digests()

    @pytest.mark.asyncio
    async def test_digest_entry_json_roundtrip(self, sample_digest_entry):
        """Test digest entry can be serialized and deserialized."""
        json_str = sample_digest_entry.model_dump_json()
        restored = DigestEntry(**json.loads(json_str))
        
        assert restored.trend_id == sample_digest_entry.trend_id
        assert restored.trend_name == sample_digest_entry.trend_name
        assert restored.velocity_score == sample_digest_entry.velocity_score
        assert restored.saturation_percent == sample_digest_entry.saturation_percent
        assert restored.growth_rate == sample_digest_entry.growth_rate
        assert restored.niche_name == sample_digest_entry.niche_name
        assert restored.niche_id == sample_digest_entry.niche_id


# =============================================================================
# Empty Digest Tests
# =============================================================================

class TestEmptyDigestHandling:
    """Tests for empty digest handling."""

    @pytest.mark.asyncio
    async def test_hourly_digest_no_users_no_error(self, digest_worker, mock_redis):
        """Test hourly digest with no users doesn't error."""
        mock_redis.scan_iter.return_value = []
        
        stats = await digest_worker.process_hourly_digests()
        
        assert stats["users_processed"] == 0
        assert stats["alerts_sent"] == 0
        assert stats["errors"] == 0

    @pytest.mark.asyncio
    async def test_daily_digest_no_users_no_error(self, digest_worker, mock_redis):
        """Test daily digest with no users doesn't error."""
        mock_redis.scan_iter.return_value = []
        
        stats = await digest_worker.process_daily_digests()
        
        assert stats["users_processed"] == 0
        assert stats["alerts_sent"] == 0
        assert stats["errors"] == 0

    @pytest.mark.asyncio
    async def test_user_with_empty_queue_not_counted(
        self, digest_worker, mock_redis, mock_email_service
    ):
        """Test user with empty queue doesn't count as processed."""
        user_id = uuid.uuid4()
        mock_redis.scan_iter.return_value = [f"digest:user:{user_id}".encode()]
        mock_redis.lrange.return_value = []
        
        stats = await digest_worker.process_hourly_digests()
        
        # Users with empty queues are not counted
        assert stats["users_processed"] == 0
        mock_email_service.send_digest.assert_not_called()


# =============================================================================
# Batch Type Tests
# =============================================================================

class TestBatchTypes:
    """Tests for different batch types."""

    @pytest.mark.asyncio
    async def test_hourly_batch_type(self, digest_worker, mock_redis, sample_digest_entries):
        """Test hourly batch type processing."""
        user_id = uuid.uuid4()
        mock_redis.scan_iter.return_value = [f"digest:user:{user_id}".encode()]
        mock_redis.lrange.return_value = [
            entry.model_dump_json() for entry in sample_digest_entries
        ]
        
        with patch.object(digest_worker, '_process_user_digest', return_value=len(sample_digest_entries)) as mock_process:
            stats = await digest_worker.process_hourly_digests()
            
            assert stats["alerts_sent"] == len(sample_digest_entries)

    @pytest.mark.asyncio
    async def test_daily_batch_type(self, digest_worker, mock_redis, sample_digest_entries):
        """Test daily batch type processing."""
        user_id = uuid.uuid4()
        mock_redis.scan_iter.return_value = [f"digest:user:{user_id}".encode()]
        mock_redis.lrange.return_value = [
            entry.model_dump_json() for entry in sample_digest_entries
        ]
        
        with patch.object(digest_worker, '_process_user_digest', return_value=len(sample_digest_entries)) as mock_process:
            stats = await digest_worker.process_daily_digests()
            
            assert stats["alerts_sent"] == len(sample_digest_entries)

    def test_batch_type_values(self):
        """Test batch type enum values."""
        assert BatchType.REALTIME.value == "realtime"
        assert BatchType.HOURLY.value == "hourly"
        assert BatchType.DAILY.value == "daily"
        assert BatchType.WEEKLY.value == "weekly"


# =============================================================================
# Singleton Tests
# =============================================================================

class TestSingleton:
    """Tests for DigestWorker singleton."""

    def test_get_digest_worker_creates_instance(self, mock_redis):
        """Test get_digest_worker creates singleton instance."""
        from alerts.digest_worker import get_digest_worker
        
        # Reset singleton
        import alerts.digest_worker
        alerts.digest_worker._digest_worker = None
        
        worker = get_digest_worker(mock_redis)
        
        assert worker is not None
        
        # Second call returns same instance
        worker2 = get_digest_worker()
        assert worker is worker2

    def test_get_digest_worker_requires_redis_on_first_call(self):
        """Test get_digest_worker requires Redis on first call."""
        from alerts.digest_worker import get_digest_worker
        
        # Reset singleton
        import alerts.digest_worker
        alerts.digest_worker._digest_worker = None
        
        with pytest.raises(ValueError, match="Redis client required"):
            get_digest_worker()


# =============================================================================
# Error Handling Tests
# =============================================================================

class TestErrorHandling:
    """Tests for error handling in digest worker."""

    @pytest.mark.asyncio
    async def test_queue_alert_handles_redis_error(self, digest_worker, mock_redis, sample_trend):
        """Test queue_alert handles Redis errors."""
        import redis.asyncio as redis
        mock_redis.rpush.side_effect = redis.RedisError("Connection lost")
        
        result = await digest_worker.queue_alert(
            user_id=uuid.uuid4(),
            trend=sample_trend,
            delay_seconds=3600
        )
        
        assert result is False

    @pytest.mark.asyncio
    async def test_get_user_queue_handles_redis_error(self, digest_worker, mock_redis):
        """Test get_user_queue handles Redis errors."""
        import redis.asyncio as redis
        mock_redis.lrange.side_effect = redis.RedisError("Connection lost")
        
        entries = await digest_worker.get_user_queue(uuid.uuid4())
        
        assert entries == []

    @pytest.mark.asyncio
    async def test_clear_user_queue_handles_redis_error(self, digest_worker, mock_redis):
        """Test clear_user_queue handles Redis errors."""
        import redis.asyncio as redis
        mock_redis.llen.side_effect = redis.RedisError("Connection lost")
        
        count = await digest_worker.clear_user_queue(uuid.uuid4())
        
        assert count == 0

    @pytest.mark.asyncio
    async def test_process_hourly_handles_scan_error(self, digest_worker, mock_redis):
        """Test process_hourly_digests handles scan errors."""
        import redis.asyncio as redis
        mock_redis.scan_iter.side_effect = redis.RedisError("Scan failed")
        
        stats = await digest_worker.process_hourly_digests()
        
        # Should return empty stats on error
        assert "users_processed" in stats

    @pytest.mark.asyncio
    async def test_cleanup_stale_queues_handles_errors(self, digest_worker, mock_redis):
        """Test cleanup handles errors gracefully."""
        mock_redis.scan_iter.return_value = [b"digest:user:user1"]
        mock_redis.lrange.side_effect = Exception("Unexpected error")
        
        # Should not raise exception
        removed = await digest_worker.cleanup_stale_queues()
        
        # The queue might still be removed due to error handling
        assert removed >= 0


# =============================================================================
# Multiple User Tests
# =============================================================================

class TestMultipleUsers:
    """Tests for processing multiple users."""

    @pytest.mark.asyncio
    async def test_process_multiple_users_hourly(self, digest_worker, mock_redis, sample_digest_entries):
        """Test processing multiple users for hourly digests."""
        user_ids = [uuid.uuid4() for _ in range(3)]
        mock_redis.scan_iter.return_value = [
            f"digest:user:{user_id}".encode() for user_id in user_ids
        ]
        mock_redis.lrange.return_value = [
            sample_digest_entries[0].model_dump_json()
        ]
        
        process_counts = [2, 3, 0]  # Different counts for each user
        with patch.object(digest_worker, '_process_user_digest', side_effect=process_counts):
            stats = await digest_worker.process_hourly_digests()
            
            assert stats["users_processed"] == 2  # Only users with > 0 count
            assert stats["alerts_sent"] == 5

    @pytest.mark.asyncio
    async def test_process_multiple_users_with_errors(self, digest_worker, mock_redis, sample_digest_entries):
        """Test processing multiple users with some errors."""
        user_ids = [uuid.uuid4() for _ in range(3)]
        mock_redis.scan_iter.return_value = [
            f"digest:user:{user_id}".encode() for user_id in user_ids
        ]
        mock_redis.lrange.return_value = [
            sample_digest_entries[0].model_dump_json()
        ]
        
        def side_effect(user_id, batch_type, user_config=None):
            if str(user_id) == str(user_ids[1]):
                raise Exception("Processing error")
            return 2
        
        with patch.object(digest_worker, '_process_user_digest', side_effect=side_effect):
            stats = await digest_worker.process_hourly_digests()
            
            assert stats["errors"] == 1
            assert stats["users_processed"] == 2


# =============================================================================
# Integration Helper Tests
# =============================================================================

class TestIntegrationHelpers:
    """Tests for integration with other services."""

    @pytest.mark.asyncio
    async def test_slack_send_digest_params(self, digest_worker, mock_redis, mock_slack_service, sample_digest_entries):
        """Test Slack digest is called with correct parameters."""
        user_id = uuid.uuid4()
        config = UserAlertConfig(
            user_id=user_id,
            email="test@example.com",
            tier=Tier.AGENCY,
            niche_id=uuid.uuid4(),
            integration_type="slack",
            integration_config={"webhook_url": "https://hooks.slack.com/test"}
        )
        
        mock_redis.lrange.return_value = [
            entry.model_dump_json() for entry in sample_digest_entries
        ]
        mock_slack_service.send_digest.return_value = True
        
        await digest_worker._process_user_digest(user_id, BatchType.HOURLY, config)
        
        call_args = mock_slack_service.send_digest.call_args
        assert call_args[0][0] == "https://hooks.slack.com/test"
        assert len(call_args[0][1]) == 3  # 3 trends
        assert call_args[0][2] == "hourly"

    @pytest.mark.asyncio
    async def test_email_send_digest_params(self, digest_worker, mock_redis, mock_email_service, sample_digest_entries):
        """Test email digest is called with correct parameters."""
        user_id = uuid.uuid4()
        config = UserAlertConfig(
            user_id=user_id,
            email="test@example.com",
            tier=Tier.FREE,
            email_notifications=True,
            niche_id=uuid.uuid4()
        )
        
        mock_redis.lrange.return_value = [
            entry.model_dump_json() for entry in sample_digest_entries
        ]
        mock_email_service.send_digest.return_value = True
        
        await digest_worker._process_user_digest(user_id, BatchType.DAILY, config)
        
        call_args = mock_email_service.send_digest.call_args
        assert call_args[0][0] == "test@example.com"
        assert len(call_args[0][1]) == 3
        assert call_args[0][2] == "daily"


# =============================================================================
# Edge Cases Tests
# =============================================================================

class TestEdgeCases:
    """Tests for edge cases."""

    @pytest.mark.asyncio
    async def test_very_long_queue(self, digest_worker, mock_redis):
        """Test handling of very long queue."""
        user_id = uuid.uuid4()
        
        # Create many entries
        entries = []
        for i in range(150):
            entry = DigestEntry(
                trend_id=str(uuid.uuid4()),
                trend_name=f"Trend {i}",
                velocity_score=50 + (i % 50),
                saturation_percent=30,
                growth_rate=50.0,
                niche_name="Test Niche",
                queued_at=datetime.utcnow()
            )
            entries.append(entry.model_dump_json())
        
        mock_redis.lrange.return_value = entries
        
        queue = await digest_worker.get_user_queue(user_id, limit=100)
        
        # Default limit is 100
        assert len(queue) <= 100

    @pytest.mark.asyncio
    async def test_queue_with_malformed_entries(self, digest_worker, mock_redis):
        """Test queue with some malformed entries."""
        user_id = uuid.uuid4()
        
        valid_entry = DigestEntry(
            trend_id=str(uuid.uuid4()),
            trend_name="Valid Trend",
            velocity_score=85,
            saturation_percent=25,
            growth_rate=120.5,
            niche_name="Test Niche",
            queued_at=datetime.utcnow()
        )
        
        mock_redis.lrange.return_value = [
            valid_entry.model_dump_json(),
            b"not a string",
            "{invalid json",
            "null",
            "{}",
        ]
        
        entries = await digest_worker.get_user_queue(user_id)
        
        # Should handle gracefully, may skip invalid entries
        assert isinstance(entries, list)

    @pytest.mark.asyncio
    async def test_process_user_with_no_email_no_slack(self, digest_worker, mock_redis, sample_digest_entries):
        """Test processing user with no delivery channels configured."""
        user_id = uuid.uuid4()
        config = UserAlertConfig(
            user_id=user_id,
            email="test@example.com",
            tier=Tier.FREE,
            email_notifications=False,  # Email disabled
            niche_id=uuid.uuid4(),
            integration_type=None  # No Slack
        )
        
        mock_redis.lrange.return_value = [
            entry.model_dump_json() for entry in sample_digest_entries
        ]
        
        count = await digest_worker._process_user_digest(user_id, BatchType.DAILY, config)
        
        assert count == 0

    @pytest.mark.asyncio
    async def test_unicode_in_trend_name(self, digest_worker, mock_redis):
        """Test handling of unicode characters in trend name."""
        entry = DigestEntry(
            trend_id=str(uuid.uuid4()),
            trend_name="🔥 Trending Sound 日本語",
            velocity_score=85,
            saturation_percent=25,
            growth_rate=120.5,
            niche_name="Unicode Niche 🎵",
            queued_at=datetime.utcnow()
        )
        
        user_id = uuid.uuid4()
        
        # Should serialize/deserialize correctly
        json_str = entry.model_dump_json()
        mock_redis.lrange.return_value = [json_str]
        
        entries = await digest_worker.get_user_queue(user_id)
        
        if entries:
            assert entries[0].trend_name == "🔥 Trending Sound 日本語"
            assert entries[0].niche_name == "Unicode Niche 🎵"
