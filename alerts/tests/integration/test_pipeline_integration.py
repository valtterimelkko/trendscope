"""
Integration tests for Alert Pipeline.

Tests the full pipeline integration including:
- Full pipeline: Trend → Alert → Digest
- Multi-tier routing (FREE, SOLO, AGENCY, ENTERPRISE)
- Database persistence of alerts
- Queue integration for digests
"""

import json
import uuid
from datetime import datetime, timedelta
from typing import List, Dict, Any
from unittest.mock import AsyncMock, MagicMock, patch, Mock, call

import pytest
import pytest_asyncio

from alerts.models import (
    Alert,
    AlertChannel,
    AlertResult,
    AlertStatus,
    UserAlertConfig,
    TrendForAlert,
    Tier,
    BatchType,
    DigestEntry,
)


# =============================================================================
# Fixtures
# =============================================================================

@pytest.fixture
def mock_db_pool():
    """Mock database pool with tracking."""
    pool = AsyncMock()
    pool.fetch = AsyncMock(return_value=[])
    pool.fetchrow = AsyncMock(return_value=None)
    
    # Track all database calls
    pool.call_history = []
    
    async def track_fetch(*args, **kwargs):
        pool.call_history.append(("fetch", args, kwargs))
        return pool.fetch.return_value
    
    async def track_fetchrow(*args, **kwargs):
        pool.call_history.append(("fetchrow", args, kwargs))
        return pool.fetchrow.return_value
    
    pool.fetch.side_effect = track_fetch
    pool.fetchrow.side_effect = track_fetchrow
    
    return pool


@pytest.fixture
def mock_redis():
    """Mock Redis client with storage simulation."""
    redis = MagicMock()
    
    # Simulate Redis storage
    redis._storage = {}
    redis._lists = {}
    
    async def mock_rpush(key, value):
        if key not in redis._lists:
            redis._lists[key] = []
        redis._lists[key].append(value)
        return len(redis._lists[key])
    
    async def mock_lrange(key, start, end):
        lst = redis._lists.get(key, [])
        if end == -1:
            return lst[start:]
        return lst[start:end+1]
    
    async def mock_llen(key):
        return len(redis._lists.get(key, []))
    
    async def mock_delete(key):
        deleted = 0
        if key in redis._storage:
            del redis._storage[key]
            deleted += 1
        if key in redis._lists:
            del redis._lists[key]
            deleted += 1
        return deleted
    
    async def mock_get(key):
        return redis._storage.get(key)
    
    async def mock_setex(key, ttl, value):
        redis._storage[key] = value
        return True
    
    async def mock_expire(key, ttl):
        return True
    
    async def mock_scan_iter(match=None):
        prefix = match.replace("*", "") if match else ""
        for key in list(redis._lists.keys()):
            if key.startswith(prefix):
                yield key.encode()
    
    redis.rpush = AsyncMock(side_effect=mock_rpush)
    redis.lrange = AsyncMock(side_effect=mock_lrange)
    redis.llen = AsyncMock(side_effect=mock_llen)
    redis.delete = AsyncMock(side_effect=mock_delete)
    redis.get = AsyncMock(side_effect=mock_get)
    redis.setex = AsyncMock(side_effect=mock_setex)
    redis.expire = AsyncMock(side_effect=mock_expire)
    redis.scan_iter = mock_scan_iter
    redis.set = AsyncMock(return_value=True)
    
    return redis


@pytest.fixture
def mock_slack_service():
    """Mock Slack service."""
    service = AsyncMock()
    service.send_trend_alert = AsyncMock(return_value=True)
    service.send_digest = AsyncMock(return_value=True)
    return service


@pytest.fixture
def mock_email_service():
    """Mock email service."""
    service = AsyncMock()
    service.send_trend_alert = AsyncMock(return_value=True)
    service.send_digest = AsyncMock(return_value=True)
    return service


@pytest.fixture
def sample_trend():
    """Create a high-velocity trend for testing."""
    return TrendForAlert(
        id=uuid.uuid4(),
        type="sound",
        name="Viral Sound Effect",
        velocity_score=88,
        saturation_percent=20,
        video_count_current=2500,
        growth_rate=150.0,
        niche_name="Music & Audio",
        status="trending",
        window_hours="4-6"
    )


@pytest.fixture
def sample_trends_batch() -> List[TrendForAlert]:
    """Create a batch of trends for testing."""
    return [
        TrendForAlert(
            id=uuid.uuid4(),
            type="sound",
            name="Trending Sound 1",
            velocity_score=92,
            saturation_percent=15,
            video_count_current=5000,
            growth_rate=200.0,
            niche_name="Music",
            window_hours="4-6"
        ),
        TrendForAlert(
            id=uuid.uuid4(),
            type="hashtag",
            name="#ViralChallenge",
            velocity_score=85,
            saturation_percent=25,
            video_count_current=3000,
            growth_rate=120.0,
            niche_name="Challenges",
            window_hours="6-8"
        ),
        TrendForAlert(
            id=uuid.uuid4(),
            type="format",
            name="Duet Format",
            velocity_score=78,
            saturation_percent=35,
            video_count_current=1800,
            growth_rate=90.0,
            niche_name="Formats",
            window_hours="8-10"
        ),
    ]


@pytest.fixture
def create_user_config():
    """Factory for creating user configurations."""
    def _create(
        tier: Tier = Tier.SOLO,
        velocity_threshold: int = 50,
        email_notifications: bool = True,
        integration_type: str = None,
        integration_config: Dict = None
    ):
        return UserAlertConfig(
            user_id=uuid.uuid4(),
            email=f"user_{tier.value}@example.com",
            tier=tier,
            email_notifications=email_notifications,
            niche_id=uuid.uuid4(),
            alert_enabled=True,
            velocity_threshold=velocity_threshold,
            integration_id=uuid.uuid4() if integration_type else None,
            integration_type=integration_type,
            integration_config=integration_config
        )
    return _create


@pytest_asyncio.fixture
async def alert_pipeline(mock_db_pool, mock_redis, mock_slack_service, mock_email_service):
    """Create an AlertPipeline with mocked dependencies."""
    from alerts.pipeline import AlertPipeline
    from alerts.tier_router import TierRouter
    
    # Create real tier router
    tier_config = {
        "free": {"delay_seconds": 86400, "is_immediate": False, "batch_type": "daily"},
        "solo": {"delay_seconds": 7200, "is_immediate": False, "batch_type": "hourly"},
        "agency": {"delay_seconds": 1800, "is_immediate": False, "batch_type": "hourly"},
        "enterprise": {"delay_seconds": 0, "is_immediate": True, "batch_type": "realtime"},
    }
    
    class MockTierRouter:
        def get_routing(self, tier: str):
            config = tier_config.get(tier, tier_config["free"])
            return MagicMock(
                is_immediate=config["is_immediate"],
                delay_seconds=config["delay_seconds"],
                batch_type=BatchType(config["batch_type"]),
                max_alerts_per_batch=10
            )
    
    with patch("alerts.pipeline.DeduplicationService") as mock_dedup_class:
        with patch("alerts.pipeline.ThrottlingService") as mock_throttle_class:
            mock_dedup = AsyncMock()
            mock_dedup.is_duplicate = AsyncMock(return_value=False)
            mock_dedup.mark_sent = AsyncMock(return_value=True)
            mock_dedup.get_stats = AsyncMock(return_value={"window_hours": 1, "entries": 0})
            
            mock_throttle = AsyncMock()
            mock_throttle.should_throttle = AsyncMock(return_value=False)
            mock_throttle.increment_counters = AsyncMock(return_value=True)
            mock_throttle.get_stats = AsyncMock(return_value={"throttled_count": 0})
            
            mock_dedup_class.return_value = mock_dedup
            mock_throttle_class.return_value = mock_throttle
            
            pipeline = AlertPipeline(
                db_pool=mock_db_pool,
                redis_client=mock_redis,
                slack_service=mock_slack_service,
                email_service=mock_email_service,
                tier_router=MockTierRouter()
            )
            
            yield pipeline


@pytest_asyncio.fixture
async def digest_worker(mock_redis, mock_slack_service, mock_email_service):
    """Create a DigestWorker with mocked dependencies."""
    from alerts.digest_worker import DigestWorker
    
    worker = DigestWorker(
        redis_client=mock_redis,
        slack_service=mock_slack_service,
        email_service=mock_email_service
    )
    
    return worker


# =============================================================================
# Full Pipeline Tests
# =============================================================================

class TestFullPipeline:
    """Tests for complete Trend → Alert → Digest flow."""

    @pytest.mark.asyncio
    async def test_full_pipeline_free_tier(
        self, alert_pipeline, mock_db_pool, mock_redis, sample_trend, create_user_config
    ):
        """Test full pipeline flow for Free tier user."""
        # Setup: Free tier user
        free_user = create_user_config(Tier.FREE, velocity_threshold=50)
        niche_id = free_user.niche_id
        
        mock_db_pool.fetch.return_value = [
            {
                "user_id": free_user.user_id,
                "email": free_user.email,
                "tier": free_user.tier.value,
                "email_notifications": free_user.email_notifications,
                "niche_id": niche_id,
                "alert_enabled": True,
                "velocity_threshold": free_user.velocity_threshold,
                "integration_id": None,
                "integration_type": None,
                "integration_config": None
            }
        ]
        
        alert_id = uuid.uuid4()
        mock_db_pool.fetchrow.return_value = {
            "id": alert_id,
            "user_id": free_user.user_id,
            "trend_id": sample_trend.id,
            "channel": "email",
            "status": "pending",
            "created_at": datetime.utcnow()
        }
        
        # Execute: Process trend
        results = await alert_pipeline.process_trend_alert(sample_trend, niche_id)
        
        # Verify: Alert queued for digest (not sent immediately)
        assert len(results) == 1
        assert results[0].alert_id == alert_id
        assert results[0].queued is True
        assert results[0].sent is False
        
        # Verify: Alert stored in Redis queue
        queue_key = f"digest:user:{free_user.user_id}"
        assert queue_key in mock_redis._lists
        assert len(mock_redis._lists[queue_key]) == 1
        
        # Verify: Alert persisted in database
        mock_db_pool.fetchrow.assert_called()

    @pytest.mark.asyncio
    async def test_full_pipeline_enterprise_tier(
        self, alert_pipeline, mock_db_pool, mock_slack_service, sample_trend, create_user_config
    ):
        """Test full pipeline flow for Enterprise tier user."""
        # Setup: Enterprise tier user with Slack
        enterprise_user = create_user_config(
            Tier.ENTERPRISE,
            velocity_threshold=30,
            integration_type="slack",
            integration_config={"webhook_url": "https://hooks.slack.com/enterprise"}
        )
        niche_id = enterprise_user.niche_id
        
        mock_db_pool.fetch.return_value = [
            {
                "user_id": enterprise_user.user_id,
                "email": enterprise_user.email,
                "tier": enterprise_user.tier.value,
                "email_notifications": True,
                "niche_id": niche_id,
                "alert_enabled": True,
                "velocity_threshold": enterprise_user.velocity_threshold,
                "integration_id": enterprise_user.integration_id,
                "integration_type": "slack",
                "integration_config": enterprise_user.integration_config
            }
        ]
        
        alert_id = uuid.uuid4()
        mock_db_pool.fetchrow.return_value = {
            "id": alert_id,
            "user_id": enterprise_user.user_id,
            "trend_id": sample_trend.id,
            "channel": "slack",
            "status": "pending",
            "created_at": datetime.utcnow()
        }
        
        # Execute: Process trend
        results = await alert_pipeline.process_trend_alert(sample_trend, niche_id)
        
        # Verify: Alert sent immediately via Slack
        assert len(results) == 1
        assert results[0].alert_id == alert_id
        assert results[0].sent is True
        assert results[0].queued is False
        
        # Verify: Slack was called
        mock_slack_service.send_trend_alert.assert_called_once()
        call_args = mock_slack_service.send_trend_alert.call_args
        assert call_args[1]["webhook_url"] == "https://hooks.slack.com/enterprise"

    @pytest.mark.asyncio
    async def test_full_pipeline_solo_tier_batch(
        self, alert_pipeline, mock_db_pool, mock_redis, sample_trends_batch, create_user_config
    ):
        """Test batch processing for Solo tier."""
        # Setup: Solo tier user
        solo_user = create_user_config(Tier.SOLO, velocity_threshold=50)
        niche_id = solo_user.niche_id
        
        mock_db_pool.fetch.return_value = [
            {
                "user_id": solo_user.user_id,
                "email": solo_user.email,
                "tier": solo_user.tier.value,
                "email_notifications": True,
                "niche_id": niche_id,
                "alert_enabled": True,
                "velocity_threshold": solo_user.velocity_threshold,
                "integration_id": None,
                "integration_type": None,
                "integration_config": None
            }
        ]
        
        alert_ids = [uuid.uuid4() for _ in sample_trends_batch]
        
        async def mock_fetchrow(*args, **kwargs):
            idx = len([c for c in mock_db_pool.call_history if c[0] == "fetchrow"])
            return {
                "id": alert_ids[idx % len(alert_ids)],
                "user_id": solo_user.user_id,
                "trend_id": sample_trends_batch[idx % len(sample_trends_batch)].id,
                "channel": "email",
                "status": "pending",
                "created_at": datetime.utcnow()
            }
        
        mock_db_pool.fetchrow.side_effect = mock_fetchrow
        
        # Execute: Process multiple trends
        all_results = []
        for trend in sample_trends_batch:
            results = await alert_pipeline.process_trend_alert(trend, niche_id)
            all_results.extend(results)
        
        # Verify: All alerts queued
        assert len(all_results) == len(sample_trends_batch)
        assert all(r.queued for r in all_results)
        
        # Verify: All alerts in Redis queue
        queue_key = f"digest:user:{solo_user.user_id}"
        assert len(mock_redis._lists.get(queue_key, [])) == len(sample_trends_batch)

    @pytest.mark.asyncio
    async def test_full_pipeline_trend_to_digest_delivery(
        self, alert_pipeline, digest_worker, mock_db_pool, mock_redis, 
        mock_email_service, sample_trends_batch, create_user_config
    ):
        """Test complete flow from trend detection to digest delivery."""
        # Setup: Free tier user
        free_user = create_user_config(Tier.FREE, velocity_threshold=50)
        niche_id = free_user.niche_id
        
        mock_db_pool.fetch.return_value = [
            {
                "user_id": free_user.user_id,
                "email": free_user.email,
                "tier": free_user.tier.value,
                "email_notifications": True,
                "niche_id": niche_id,
                "alert_enabled": True,
                "velocity_threshold": free_user.velocity_threshold,
                "integration_id": None,
                "integration_type": None,
                "integration_config": None
            }
        ]
        
        alert_ids = [uuid.uuid4() for _ in sample_trends_batch]
        alert_idx = [0]
        
        async def mock_fetchrow(*args, **kwargs):
            idx = alert_idx[0]
            alert_idx[0] += 1
            return {
                "id": alert_ids[idx],
                "user_id": free_user.user_id,
                "trend_id": sample_trends_batch[idx].id,
                "channel": "email",
                "status": "pending",
                "created_at": datetime.utcnow()
            }
        
        mock_db_pool.fetchrow.side_effect = mock_fetchrow
        
        # Step 1: Queue trends for digest
        for trend in sample_trends_batch:
            await alert_pipeline.process_trend_alert(trend, niche_id)
        
        # Verify: Trends queued
        queue_key = f"digest:user:{free_user.user_id}"
        assert len(mock_redis._lists.get(queue_key, [])) == len(sample_trends_batch)
        
        # Step 2: Process digest
        with patch.object(alert_pipeline.digest, '_process_user_digest', return_value=len(sample_trends_batch)):
            stats = await alert_pipeline.trigger_digest_processing("daily")
        
        # Verify digest was triggered
        assert stats is not None


# =============================================================================
# Multi-Tier Routing Tests
# =============================================================================

class TestMultiTierRouting:
    """Tests for multi-tier routing behavior."""

    @pytest.mark.asyncio
    async def test_all_tiers_same_niche(
        self, alert_pipeline, mock_db_pool, mock_redis, 
        sample_trend, create_user_config
    ):
        """Test all tiers receiving alerts for the same niche."""
        niche_id = uuid.uuid4()
        
        # Create users for each tier
        users = {
            Tier.FREE: create_user_config(Tier.FREE, velocity_threshold=60),
            Tier.SOLO: create_user_config(Tier.SOLO, velocity_threshold=50),
            Tier.AGENCY: create_user_config(Tier.AGENCY, velocity_threshold=40),
            Tier.ENTERPRISE: create_user_config(
                Tier.ENTERPRISE, 
                velocity_threshold=30,
                integration_type="slack",
                integration_config={"webhook_url": "https://hooks.slack.com/ent"}
            ),
        }
        
        # All users subscribed to same niche
        mock_db_pool.fetch.return_value = [
            {
                "user_id": user.user_id,
                "email": user.email,
                "tier": tier.value,
                "email_notifications": True,
                "niche_id": niche_id,
                "alert_enabled": True,
                "velocity_threshold": user.velocity_threshold,
                "integration_id": user.integration_id,
                "integration_type": user.integration_type,
                "integration_config": user.integration_config
            }
            for tier, user in users.items()
        ]
        
        alert_ids = {tier: uuid.uuid4() for tier in users.keys()}
        
        async def mock_fetchrow(*args, **kwargs):
            # Return appropriate alert ID based on user
            return {
                "id": uuid.uuid4(),
                "user_id": uuid.uuid4(),  # Will vary
                "trend_id": sample_trend.id,
                "channel": "email",
                "status": "pending",
                "created_at": datetime.utcnow()
            }
        
        mock_db_pool.fetchrow.side_effect = mock_fetchrow
        
        # Execute: Process trend
        results = await alert_pipeline.process_trend_alert(sample_trend, niche_id)
        
        # Verify: All users received alerts
        assert len(results) == 4
        
        # Verify: Enterprise tier sent immediately
        enterprise_results = [r for r in results if r.sent]
        assert len(enterprise_results) >= 1
        
        # Verify: Other tiers queued
        queued_results = [r for r in results if r.queued]
        assert len(queued_results) >= 1

    @pytest.mark.asyncio
    async def test_tier_velocity_filtering(
        self, alert_pipeline, mock_db_pool, create_user_config
    ):
        """Test that velocity thresholds are applied per tier."""
        niche_id = uuid.uuid4()
        
        # Create trends at different velocities
        low_velocity_trend = TrendForAlert(
            id=uuid.uuid4(),
            type="sound",
            name="Low Velocity",
            velocity_score=45,  # Below some thresholds
            saturation_percent=30,
            video_count_current=500,
            growth_rate=30.0
        )
        
        # Users with different thresholds
        high_threshold_user = create_user_config(Tier.SOLO, velocity_threshold=70)
        low_threshold_user = create_user_config(Tier.FREE, velocity_threshold=40)
        
        mock_db_pool.fetch.return_value = [
            {
                "user_id": high_threshold_user.user_id,
                "email": high_threshold_user.email,
                "tier": high_threshold_user.tier.value,
                "email_notifications": True,
                "niche_id": niche_id,
                "alert_enabled": True,
                "velocity_threshold": high_threshold_user.velocity_threshold,
                "integration_id": None,
                "integration_type": None,
                "integration_config": None
            },
            {
                "user_id": low_threshold_user.user_id,
                "email": low_threshold_user.email,
                "tier": low_threshold_user.tier.value,
                "email_notifications": True,
                "niche_id": niche_id,
                "alert_enabled": True,
                "velocity_threshold": low_threshold_user.velocity_threshold,
                "integration_id": None,
                "integration_type": None,
                "integration_config": None
            }
        ]
        
        alert_id = uuid.uuid4()
        mock_db_pool.fetchrow.return_value = {
            "id": alert_id,
            "user_id": low_threshold_user.user_id,
            "trend_id": low_velocity_trend.id,
            "channel": "email",
            "status": "pending",
            "created_at": datetime.utcnow()
        }
        
        # Execute: Process low velocity trend
        results = await alert_pipeline.process_trend_alert(low_velocity_trend, niche_id)
        
        # Verify: High threshold user skipped, low threshold user alerted
        assert len(results) == 2
        skipped = [r for r in results if r.skipped]
        not_skipped = [r for r in results if not r.skipped]
        
        assert len(skipped) == 1
        assert skipped[0].skip_reason == "velocity_below_threshold"
        assert len(not_skipped) == 1

    @pytest.mark.asyncio
    async def test_enterprise_immediate_vs_free_daily(
        self, alert_pipeline, mock_db_pool, mock_redis, mock_slack_service,
        sample_trend, create_user_config
    ):
        """Test Enterprise immediate vs Free daily digest behavior."""
        niche_id = uuid.uuid4()
        
        enterprise_user = create_user_config(
            Tier.ENTERPRISE,
            velocity_threshold=30,
            integration_type="slack",
            integration_config={"webhook_url": "https://hooks.slack.com/ent"}
        )
        free_user = create_user_config(Tier.FREE, velocity_threshold=50)
        
        mock_db_pool.fetch.return_value = [
            {
                "user_id": enterprise_user.user_id,
                "email": enterprise_user.email,
                "tier": Tier.ENTERPRISE.value,
                "email_notifications": True,
                "niche_id": niche_id,
                "alert_enabled": True,
                "velocity_threshold": enterprise_user.velocity_threshold,
                "integration_id": enterprise_user.integration_id,
                "integration_type": "slack",
                "integration_config": enterprise_user.integration_config
            },
            {
                "user_id": free_user.user_id,
                "email": free_user.email,
                "tier": Tier.FREE.value,
                "email_notifications": True,
                "niche_id": niche_id,
                "alert_enabled": True,
                "velocity_threshold": free_user.velocity_threshold,
                "integration_id": None,
                "integration_type": None,
                "integration_config": None
            }
        ]
        
        async def mock_fetchrow(*args, **kwargs):
            return {
                "id": uuid.uuid4(),
                "user_id": uuid.uuid4(),
                "trend_id": sample_trend.id,
                "channel": "email",
                "status": "pending",
                "created_at": datetime.utcnow()
            }
        
        mock_db_pool.fetchrow.side_effect = mock_fetchrow
        
        # Execute: Process trend
        results = await alert_pipeline.process_trend_alert(sample_trend, niche_id)
        
        # Verify: Enterprise sent immediately
        enterprise_result = [r for r in results if r.sent]
        assert len(enterprise_result) == 1
        
        # Verify: Free tier queued
        free_result = [r for r in results if r.queued]
        assert len(free_result) == 1
        
        # Verify: Enterprise received Slack alert
        mock_slack_service.send_trend_alert.assert_called_once()
        
        # Verify: Free tier has entry in Redis queue
        free_queue_key = f"digest:user:{free_user.user_id}"
        assert len(mock_redis._lists.get(free_queue_key, [])) == 1

    @pytest.mark.asyncio
    async def test_solo_vs_agency_hourly_batching(
        self, alert_pipeline, mock_db_pool, mock_redis, 
        sample_trends_batch, create_user_config
    ):
        """Test Solo vs Agency tier batching behavior."""
        niche_id = uuid.uuid4()
        
        solo_user = create_user_config(Tier.SOLO, velocity_threshold=50)
        agency_user = create_user_config(
            Tier.AGENCY,
            velocity_threshold=40,
            integration_type="slack",
            integration_config={"webhook_url": "https://hooks.slack.com/agency"}
        )
        
        mock_db_pool.fetch.return_value = [
            {
                "user_id": solo_user.user_id,
                "email": solo_user.email,
                "tier": Tier.SOLO.value,
                "email_notifications": True,
                "niche_id": niche_id,
                "alert_enabled": True,
                "velocity_threshold": solo_user.velocity_threshold,
                "integration_id": None,
                "integration_type": None,
                "integration_config": None
            },
            {
                "user_id": agency_user.user_id,
                "email": agency_user.email,
                "tier": Tier.AGENCY.value,
                "email_notifications": True,
                "niche_id": niche_id,
                "alert_enabled": True,
                "velocity_threshold": agency_user.velocity_threshold,
                "integration_id": agency_user.integration_id,
                "integration_type": "slack",
                "integration_config": agency_user.integration_config
            }
        ]
        
        async def mock_fetchrow(*args, **kwargs):
            return {
                "id": uuid.uuid4(),
                "user_id": uuid.uuid4(),
                "trend_id": uuid.uuid4(),
                "channel": "email",
                "status": "pending",
                "created_at": datetime.utcnow()
            }
        
        mock_db_pool.fetchrow.side_effect = mock_fetchrow
        
        # Process all trends
        for trend in sample_trends_batch:
            await alert_pipeline.process_trend_alert(trend, niche_id)
        
        # Verify: Both users have queued alerts
        solo_queue = mock_redis._lists.get(f"digest:user:{solo_user.user_id}", [])
        agency_queue = mock_redis._lists.get(f"digest:user:{agency_user.user_id}", [])
        
        assert len(solo_queue) == len(sample_trends_batch)
        assert len(agency_queue) == len(sample_trends_batch)


# =============================================================================
# Database Persistence Tests
# =============================================================================

class TestDatabasePersistence:
    """Tests for database persistence of alerts."""

    @pytest.mark.asyncio
    async def test_alert_persisted_to_database(
        self, alert_pipeline, mock_db_pool, sample_trend, create_user_config
    ):
        """Test alert is persisted to database."""
        user = create_user_config(Tier.SOLO)
        niche_id = user.niche_id
        alert_id = uuid.uuid4()
        
        mock_db_pool.fetch.return_value = [
            {
                "user_id": user.user_id,
                "email": user.email,
                "tier": user.tier.value,
                "email_notifications": True,
                "niche_id": niche_id,
                "alert_enabled": True,
                "velocity_threshold": user.velocity_threshold,
                "integration_id": None,
                "integration_type": None,
                "integration_config": None
            }
        ]
        
        mock_db_pool.fetchrow.return_value = {
            "id": alert_id,
            "user_id": user.user_id,
            "trend_id": sample_trend.id,
            "channel": "email",
            "status": "pending",
            "created_at": datetime.utcnow()
        }
        
        # Execute
        results = await alert_pipeline.process_trend_alert(sample_trend, niche_id)
        
        # Verify: Database insert was called
        mock_db_pool.fetchrow.assert_called()
        call_args = mock_db_pool.fetchrow.call_args
        assert "INSERT INTO alerts" in call_args[0][0]
        
        # Verify: Alert ID returned
        assert results[0].alert_id == alert_id

    @pytest.mark.asyncio
    async def test_multiple_alerts_persisted(
        self, alert_pipeline, mock_db_pool, sample_trends_batch, create_user_config
    ):
        """Test multiple alerts are persisted for batch trends."""
        user = create_user_config(Tier.FREE)
        niche_id = user.niche_id
        
        mock_db_pool.fetch.return_value = [
            {
                "user_id": user.user_id,
                "email": user.email,
                "tier": user.tier.value,
                "email_notifications": True,
                "niche_id": niche_id,
                "alert_enabled": True,
                "velocity_threshold": user.velocity_threshold,
                "integration_id": None,
                "integration_type": None,
                "integration_config": None
            }
        ]
        
        call_count = [0]
        
        async def mock_fetchrow(*args, **kwargs):
            call_count[0] += 1
            return {
                "id": uuid.uuid4(),
                "user_id": user.user_id,
                "trend_id": uuid.uuid4(),
                "channel": "email",
                "status": "pending",
                "created_at": datetime.utcnow()
            }
        
        mock_db_pool.fetchrow.side_effect = mock_fetchrow
        
        # Execute: Process multiple trends
        for trend in sample_trends_batch:
            await alert_pipeline.process_trend_alert(trend, niche_id)
        
        # Verify: One insert per trend
        assert call_count[0] == len(sample_trends_batch)

    @pytest.mark.asyncio
    async def test_database_error_handled(
        self, alert_pipeline, mock_db_pool, sample_trend, create_user_config
    ):
        """Test database error is handled gracefully."""
        user = create_user_config(Tier.SOLO)
        niche_id = user.niche_id
        
        mock_db_pool.fetch.return_value = [
            {
                "user_id": user.user_id,
                "email": user.email,
                "tier": user.tier.value,
                "email_notifications": True,
                "niche_id": niche_id,
                "alert_enabled": True,
                "velocity_threshold": user.velocity_threshold,
                "integration_id": None,
                "integration_type": None,
                "integration_config": None
            }
        ]
        
        # Simulate database error
        mock_db_pool.fetchrow.side_effect = Exception("Database connection failed")
        
        # Execute: Should not raise exception
        results = await alert_pipeline.process_trend_alert(sample_trend, niche_id)
        
        # Verify: Alert failed gracefully
        assert len(results) == 1
        # The alert should either be skipped or have an error
        assert results[0].skipped or results[0].error is not None

    @pytest.mark.asyncio
    async def test_alert_confidence_score_stored(
        self, alert_pipeline, mock_db_pool, sample_trend, create_user_config
    ):
        """Test confidence score is stored in database."""
        user = create_user_config(Tier.SOLO)
        niche_id = user.niche_id
        
        mock_db_pool.fetch.return_value = [
            {
                "user_id": user.user_id,
                "email": user.email,
                "tier": user.tier.value,
                "email_notifications": True,
                "niche_id": niche_id,
                "alert_enabled": True,
                "velocity_threshold": user.velocity_threshold,
                "integration_id": None,
                "integration_type": None,
                "integration_config": None
            }
        ]
        
        captured_args = []
        async def capture_fetchrow(*args, **kwargs):
            captured_args.append(args)
            return {
                "id": uuid.uuid4(),
                "user_id": user.user_id,
                "trend_id": sample_trend.id,
                "channel": "email",
                "status": "pending",
                "created_at": datetime.utcnow()
            }
        
        mock_db_pool.fetchrow.side_effect = capture_fetchrow
        
        # Execute
        await alert_pipeline.process_trend_alert(sample_trend, niche_id)
        
        # Verify: Confidence score based on velocity
        assert len(captured_args) > 0
        # The velocity_score / 100.0 should be in the args
        insert_args = captured_args[0]
        expected_confidence = sample_trend.velocity_score / 100.0
        assert expected_confidence in insert_args or any(
            isinstance(arg, float) and abs(arg - expected_confidence) < 0.01 
            for arg in insert_args
        )


# =============================================================================
# Queue Integration Tests
# =============================================================================

class TestQueueIntegration:
    """Tests for Redis queue integration."""

    @pytest.mark.asyncio
    async def test_alert_queued_in_redis(
        self, alert_pipeline, mock_db_pool, mock_redis, sample_trend, create_user_config
    ):
        """Test alert is properly queued in Redis."""
        free_user = create_user_config(Tier.FREE)
        niche_id = free_user.niche_id
        
        mock_db_pool.fetch.return_value = [
            {
                "user_id": free_user.user_id,
                "email": free_user.email,
                "tier": Tier.FREE.value,
                "email_notifications": True,
                "niche_id": niche_id,
                "alert_enabled": True,
                "velocity_threshold": free_user.velocity_threshold,
                "integration_id": None,
                "integration_type": None,
                "integration_config": None
            }
        ]
        
        mock_db_pool.fetchrow.return_value = {
            "id": uuid.uuid4(),
            "user_id": free_user.user_id,
            "trend_id": sample_trend.id,
            "channel": "email",
            "status": "pending",
            "created_at": datetime.utcnow()
        }
        
        # Execute
        await alert_pipeline.process_trend_alert(sample_trend, niche_id)
        
        # Verify: Redis queue has entry
        queue_key = f"digest:user:{free_user.user_id}"
        assert queue_key in mock_redis._lists
        assert len(mock_redis._lists[queue_key]) == 1
        
        # Verify: Entry is valid JSON with trend data
        entry_json = mock_redis._lists[queue_key][0]
        entry = json.loads(entry_json)
        assert entry["trend_id"] == str(sample_trend.id)
        assert entry["trend_name"] == sample_trend.name
        assert entry["velocity_score"] == sample_trend.velocity_score

    @pytest.mark.asyncio
    async def test_multiple_alerts_queued_sequentially(
        self, alert_pipeline, mock_db_pool, mock_redis, 
        sample_trends_batch, create_user_config
    ):
        """Test multiple alerts are queued sequentially."""
        user = create_user_config(Tier.FREE)
        niche_id = user.niche_id
        
        mock_db_pool.fetch.return_value = [
            {
                "user_id": user.user_id,
                "email": user.email,
                "tier": Tier.FREE.value,
                "email_notifications": True,
                "niche_id": niche_id,
                "alert_enabled": True,
                "velocity_threshold": user.velocity_threshold,
                "integration_id": None,
                "integration_type": None,
                "integration_config": None
            }
        ]
        
        async def mock_fetchrow(*args, **kwargs):
            return {
                "id": uuid.uuid4(),
                "user_id": user.user_id,
                "trend_id": uuid.uuid4(),
                "channel": "email",
                "status": "pending",
                "created_at": datetime.utcnow()
            }
        
        mock_db_pool.fetchrow.side_effect = mock_fetchrow
        
        # Execute: Queue multiple trends
        for trend in sample_trends_batch:
            await alert_pipeline.process_trend_alert(trend, niche_id)
        
        # Verify: All alerts in queue in order
        queue_key = f"digest:user:{user.user_id}"
        queue = mock_redis._lists.get(queue_key, [])
        assert len(queue) == len(sample_trends_batch)
        
        # Verify: Order preserved
        for i, trend in enumerate(sample_trends_batch):
            entry = json.loads(queue[i])
            assert entry["trend_name"] == trend.name

    @pytest.mark.asyncio
    async def test_queue_cleared_after_digest_sent(
        self, digest_worker, mock_redis, mock_email_service, sample_digest_entries
    ):
        """Test queue is cleared after digest is sent."""
        user_id = uuid.uuid4()
        
        # Setup: Add entries to queue
        queue_key = f"digest:user:{user_id}"
        for entry in sample_digest_entries:
            await mock_redis.rpush(queue_key, entry.model_dump_json())
        
        assert len(mock_redis._lists.get(queue_key, [])) == len(sample_digest_entries)
        
        # Setup: User config
        user_config = UserAlertConfig(
            user_id=user_id,
            email="test@example.com",
            tier=Tier.FREE,
            email_notifications=True,
            niche_id=uuid.uuid4()
        )
        
        mock_email_service.send_digest.return_value = True
        
        # Execute: Process digest
        count = await digest_worker._process_user_digest(
            user_id, BatchType.DAILY, user_config
        )
        
        # Verify: Digest sent
        assert count == len(sample_digest_entries)
        
        # Verify: Queue cleared
        assert len(mock_redis._lists.get(queue_key, [])) == 0

    @pytest.mark.asyncio
    async def test_queue_preserved_on_delivery_failure(
        self, digest_worker, mock_redis, mock_email_service, sample_digest_entries
    ):
        """Test queue is preserved if delivery fails."""
        user_id = uuid.uuid4()
        
        # Setup: Add entries to queue
        queue_key = f"digest:user:{user_id}"
        for entry in sample_digest_entries:
            await mock_redis.rpush(queue_key, entry.model_dump_json())
        
        initial_count = len(mock_redis._lists.get(queue_key, []))
        
        # Setup: User config
        user_config = UserAlertConfig(
            user_id=user_id,
            email="test@example.com",
            tier=Tier.FREE,
            email_notifications=True,
            niche_id=uuid.uuid4()
        )
        
        # Delivery fails
        mock_email_service.send_digest.return_value = False
        
        # Execute: Process digest
        count = await digest_worker._process_user_digest(
            user_id, BatchType.DAILY, user_config
        )
        
        # Verify: No digest sent
        assert count == 0
        
        # Verify: Queue preserved
        assert len(mock_redis._lists.get(queue_key, [])) == initial_count

    @pytest.mark.asyncio
    async def test_digest_processing_from_queue(
        self, digest_worker, mock_redis, mock_email_service, sample_digest_entries
    ):
        """Test digest processing reads from queue."""
        user_ids = [uuid.uuid4() for _ in range(2)]
        
        # Setup: Add entries to queues
        for user_id in user_ids:
            queue_key = f"digest:user:{user_id}"
            for entry in sample_digest_entries:
                await mock_redis.rpush(queue_key, entry.model_dump_json())
        
        # Setup: User configs for email delivery
        def create_config(user_id):
            return UserAlertConfig(
                user_id=user_id,
                email=f"user_{user_id}@example.com",
                tier=Tier.FREE,
                email_notifications=True,
                niche_id=uuid.uuid4()
            )
        
        mock_email_service.send_digest.return_value = True
        
        # Patch _process_user_digest to simulate processing with config
        original_process = digest_worker._process_user_digest
        async def patched_process(user_id, batch_type, user_config=None):
            # Simulate processing with config
            config = create_config(user_id)
            return await original_process(user_id, batch_type, config)
        
        with patch.object(digest_worker, '_process_user_digest', side_effect=patched_process):
            # Execute: Process hourly digests
            stats = await digest_worker.process_hourly_digests()
            
            # Verify: All users processed
            assert stats["users_processed"] == 2
            assert stats["alerts_sent"] == len(sample_digest_entries) * 2


# =============================================================================
# End-to-End Flow Tests
# =============================================================================

class TestEndToEndFlow:
    """End-to-end integration tests."""

    @pytest.mark.asyncio
    async def test_complete_alert_lifecycle(
        self, alert_pipeline, digest_worker, mock_db_pool, mock_redis,
        mock_slack_service, mock_email_service, sample_trend, create_user_config
    ):
        """Test complete alert lifecycle from trend to delivery."""
        # Setup: Multiple users across tiers
        enterprise_user = create_user_config(
            Tier.ENTERPRISE,
            velocity_threshold=30,
            integration_type="slack",
            integration_config={"webhook_url": "https://hooks.slack.com/e"}
        )
        solo_user = create_user_config(Tier.SOLO, velocity_threshold=50)
        free_user = create_user_config(Tier.FREE, velocity_threshold=70)
        
        niche_id = uuid.uuid4()
        
        mock_db_pool.fetch.return_value = [
            {
                "user_id": enterprise_user.user_id,
                "email": enterprise_user.email,
                "tier": Tier.ENTERPRISE.value,
                "email_notifications": True,
                "niche_id": niche_id,
                "alert_enabled": True,
                "velocity_threshold": enterprise_user.velocity_threshold,
                "integration_id": enterprise_user.integration_id,
                "integration_type": "slack",
                "integration_config": enterprise_user.integration_config
            },
            {
                "user_id": solo_user.user_id,
                "email": solo_user.email,
                "tier": Tier.SOLO.value,
                "email_notifications": True,
                "niche_id": niche_id,
                "alert_enabled": True,
                "velocity_threshold": solo_user.velocity_threshold,
                "integration_id": None,
                "integration_type": None,
                "integration_config": None
            },
            {
                "user_id": free_user.user_id,
                "email": free_user.email,
                "tier": Tier.FREE.value,
                "email_notifications": True,
                "niche_id": niche_id,
                "alert_enabled": True,
                "velocity_threshold": free_user.velocity_threshold,
                "integration_id": None,
                "integration_type": None,
                "integration_config": None
            }
        ]
        
        async def mock_fetchrow(*args, **kwargs):
            return {
                "id": uuid.uuid4(),
                "user_id": uuid.uuid4(),
                "trend_id": sample_trend.id,
                "channel": "email",
                "status": "pending",
                "created_at": datetime.utcnow()
            }
        
        mock_db_pool.fetchrow.side_effect = mock_fetchrow
        
        # Step 1: Trend detected, alerts triggered
        results = await alert_pipeline.process_trend_alert(sample_trend, niche_id)
        
        # Verify: 3 results (one per user)
        assert len(results) == 3
        
        # Verify: Enterprise sent immediately
        sent_count = len([r for r in results if r.sent])
        assert sent_count == 1
        mock_slack_service.send_trend_alert.assert_called_once()
        
        # Verify: Solo and Free queued
        queued_count = len([r for r in results if r.queued])
        assert queued_count == 2
        
        # Verify: Queues populated
        assert len(mock_redis._lists.get(f"digest:user:{solo_user.user_id}", [])) == 1
        assert len(mock_redis._lists.get(f"digest:user:{free_user.user_id}", [])) == 1

    @pytest.mark.asyncio
    async def test_concurrent_trends_same_niche(
        self, alert_pipeline, mock_db_pool, mock_redis, 
        sample_trends_batch, create_user_config
    ):
        """Test concurrent trends for the same niche."""
        user = create_user_config(Tier.SOLO)
        niche_id = user.niche_id
        
        mock_db_pool.fetch.return_value = [
            {
                "user_id": user.user_id,
                "email": user.email,
                "tier": Tier.SOLO.value,
                "email_notifications": True,
                "niche_id": niche_id,
                "alert_enabled": True,
                "velocity_threshold": user.velocity_threshold,
                "integration_id": None,
                "integration_type": None,
                "integration_config": None
            }
        ]
        
        async def mock_fetchrow(*args, **kwargs):
            return {
                "id": uuid.uuid4(),
                "user_id": user.user_id,
                "trend_id": uuid.uuid4(),
                "channel": "email",
                "status": "pending",
                "created_at": datetime.utcnow()
            }
        
        mock_db_pool.fetchrow.side_effect = mock_fetchrow
        
        # Process multiple trends concurrently (sequentially in test)
        all_results = []
        for trend in sample_trends_batch:
            results = await alert_pipeline.process_trend_alert(trend, niche_id)
            all_results.extend(results)
        
        # Verify: All trends processed
        assert len(all_results) == len(sample_trends_batch)
        
        # Verify: All queued
        assert all(r.queued for r in all_results)
        
        # Verify: Queue has all entries
        queue_key = f"digest:user:{user.user_id}"
        assert len(mock_redis._lists.get(queue_key, [])) == len(sample_trends_batch)

    @pytest.mark.asyncio
    async def test_pipeline_stats_integration(
        self, alert_pipeline, mock_db_pool, mock_redis, sample_trend, create_user_config
    ):
        """Test pipeline stats integration."""
        # Process some alerts first
        user = create_user_config(Tier.FREE)
        niche_id = user.niche_id
        
        mock_db_pool.fetch.return_value = [
            {
                "user_id": user.user_id,
                "email": user.email,
                "tier": Tier.FREE.value,
                "email_notifications": True,
                "niche_id": niche_id,
                "alert_enabled": True,
                "velocity_threshold": user.velocity_threshold,
                "integration_id": None,
                "integration_type": None,
                "integration_config": None
            }
        ]
        
        mock_db_pool.fetchrow.return_value = {
            "id": uuid.uuid4(),
            "user_id": user.user_id,
            "trend_id": sample_trend.id,
            "channel": "email",
            "status": "pending",
            "created_at": datetime.utcnow()
        }
        
        await alert_pipeline.process_trend_alert(sample_trend, niche_id)
        
        # Get stats
        stats = await alert_pipeline.get_pipeline_stats()
        
        # Verify: Stats structure
        assert "deduplication" in stats
        assert "throttling" in stats
        assert "digest" in stats
        assert "timestamp" in stats

    @pytest.mark.asyncio
    async def test_error_recovery_flow(
        self, alert_pipeline, mock_db_pool, mock_redis, sample_trend, create_user_config
    ):
        """Test error recovery in pipeline flow."""
        user1 = create_user_config(Tier.SOLO)
        user2 = create_user_config(Tier.FREE)
        niche_id = uuid.uuid4()
        
        mock_db_pool.fetch.return_value = [
            {
                "user_id": user1.user_id,
                "email": user1.email,
                "tier": Tier.SOLO.value,
                "email_notifications": True,
                "niche_id": niche_id,
                "alert_enabled": True,
                "velocity_threshold": user1.velocity_threshold,
                "integration_id": None,
                "integration_type": None,
                "integration_config": None
            },
            {
                "user_id": user2.user_id,
                "email": user2.email,
                "tier": Tier.FREE.value,
                "email_notifications": True,
                "niche_id": niche_id,
                "alert_enabled": True,
                "velocity_threshold": user2.velocity_threshold,
                "integration_id": None,
                "integration_type": None,
                "integration_config": None
            }
        ]
        
        call_count = [0]
        
        async def mock_fetchrow_with_failure(*args, **kwargs):
            call_count[0] += 1
            if call_count[0] == 1:
                # First call fails
                raise Exception("Database error")
            return {
                "id": uuid.uuid4(),
                "user_id": user2.user_id,
                "trend_id": sample_trend.id,
                "channel": "email",
                "status": "pending",
                "created_at": datetime.utcnow()
            }
        
        mock_db_pool.fetchrow.side_effect = mock_fetchrow_with_failure
        
        # Execute: Processing continues despite first user failure
        results = await alert_pipeline.process_trend_alert(sample_trend, niche_id)
        
        # Verify: Both users have results (one failed, one succeeded)
        assert len(results) == 2
        
        # Verify: Second user alert was queued
        success_results = [r for r in results if not r.skipped and not r.error]
        assert len(success_results) == 1


# =============================================================================
# Performance & Scale Tests
# =============================================================================

class TestPerformanceAndScale:
    """Tests for performance and scale scenarios."""

    @pytest.mark.asyncio
    async def test_many_users_same_niche(
        self, alert_pipeline, mock_db_pool, mock_redis, sample_trend
    ):
        """Test pipeline with many users subscribed to same niche."""
        niche_id = uuid.uuid4()
        num_users = 10
        
        # Create many users
        users = []
        for i in range(num_users):
            tier = [Tier.FREE, Tier.SOLO, Tier.AGENCY, Tier.ENTERPRISE][i % 4]
            user_id = uuid.uuid4()
            users.append({
                "user_id": user_id,
                "email": f"user{i}@example.com",
                "tier": tier.value,
                "email_notifications": True,
                "niche_id": niche_id,
                "alert_enabled": True,
                "velocity_threshold": 50,
                "integration_id": None,
                "integration_type": None,
                "integration_config": None
            })
        
        mock_db_pool.fetch.return_value = users
        
        async def mock_fetchrow(*args, **kwargs):
            return {
                "id": uuid.uuid4(),
                "user_id": uuid.uuid4(),
                "trend_id": sample_trend.id,
                "channel": "email",
                "status": "pending",
                "created_at": datetime.utcnow()
            }
        
        mock_db_pool.fetchrow.side_effect = mock_fetchrow
        
        # Execute
        results = await alert_pipeline.process_trend_alert(sample_trend, niche_id)
        
        # Verify: All users processed
        assert len(results) == num_users
        
        # Verify: Enterprise users sent immediately, others queued
        enterprise_count = sum(1 for u in users if u["tier"] == Tier.ENTERPRISE.value)
        sent_count = len([r for r in results if r.sent])
        queued_count = len([r for r in results if r.queued])
        
        assert sent_count == enterprise_count
        assert queued_count == num_users - enterprise_count

    @pytest.mark.asyncio
    async def test_batch_digest_delivery(
        self, digest_worker, mock_redis, mock_email_service
    ):
        """Test batch digest delivery to multiple users."""
        num_users = 5
        alerts_per_user = 3
        
        # Setup: Create queues for multiple users
        user_configs = []
        for i in range(num_users):
            user_id = uuid.uuid4()
            user_configs.append(UserAlertConfig(
                user_id=user_id,
                email=f"user{i}@example.com",
                tier=Tier.FREE,
                email_notifications=True,
                niche_id=uuid.uuid4()
            ))
            
            queue_key = f"digest:user:{user_id}"
            for j in range(alerts_per_user):
                entry = DigestEntry(
                    trend_id=str(uuid.uuid4()),
                    trend_name=f"Trend {j} for User {i}",
                    velocity_score=70 + j,
                    saturation_percent=30,
                    growth_rate=80.0,
                    niche_name="Test Niche",
                    queued_at=datetime.utcnow()
                )
                await mock_redis.rpush(queue_key, entry.model_dump_json())
        
        mock_email_service.send_digest.return_value = True
        
        # Patch _process_user_digest
        config_iter = iter(user_configs)
        async def patched_process(user_id, batch_type, user_config=None):
            config = user_config or next((c for c in user_configs if c.user_id == user_id), None)
            if config:
                return await digest_worker._process_user_digest(user_id, batch_type, config)
            return 0
        
        with patch.object(digest_worker, '_process_user_digest', side_effect=patched_process):
            # Execute: Process daily digests
            stats = await digest_worker.process_daily_digests()
            
            # Verify: All users processed
            assert stats["users_processed"] == num_users
            assert stats["alerts_sent"] == num_users * alerts_per_user
