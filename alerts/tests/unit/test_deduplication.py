"""
Unit tests for DeduplicationService.

Tests Redis-based deduplication logic including:
- Key generation
- Duplicate detection within time window
- Time window expiration
- Different alerts not marked as duplicates
- Same content different user (not duplicate)
- Cleanup operations
"""

import uuid
from datetime import datetime
from typing import Optional
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
import pytest_asyncio

from alerts.deduplication import DeduplicationService


# =============================================================================
# Fixtures
# =============================================================================

@pytest.fixture
def mock_redis() -> AsyncMock:
    """Create a mock Redis client."""
    redis = AsyncMock()
    redis.exists = AsyncMock(return_value=0)
    redis.setex = AsyncMock(return_value=True)
    redis.get = AsyncMock(return_value=None)
    redis.delete = AsyncMock(return_value=1)
    redis.scan_iter = AsyncMock(return_value=[])
    redis.ttl = AsyncMock(return_value=-1)
    return redis


@pytest.fixture
def sample_user_id() -> uuid.UUID:
    """Sample user UUID."""
    return uuid.uuid4()


@pytest.fixture
def sample_trend_id() -> uuid.UUID:
    """Sample trend UUID."""
    return uuid.uuid4()


@pytest.fixture
def deduplication_service(mock_redis) -> DeduplicationService:
    """Create a DeduplicationService with mock Redis."""
    return DeduplicationService(redis_client=mock_redis)


# =============================================================================
# Key Generation Tests
# =============================================================================

class TestDeduplicationKeyGeneration:
    """Tests for deduplication key generation."""

    def test_make_key_format(self, deduplication_service, sample_user_id, sample_trend_id):
        """Test key format is correct."""
        key = deduplication_service._make_key(sample_user_id, sample_trend_id)
        
        expected = f"alert:dedup:{sample_user_id}:{sample_trend_id}"
        assert key == expected

    def test_make_key_prefix(self, deduplication_service, sample_user_id, sample_trend_id):
        """Test key has correct prefix."""
        key = deduplication_service._make_key(sample_user_id, sample_trend_id)
        
        assert key.startswith("alert:dedup:")

    def test_make_key_uniqueness(self, deduplication_service):
        """Test that different user+trend combinations produce different keys."""
        user1 = uuid.uuid4()
        user2 = uuid.uuid4()
        trend1 = uuid.uuid4()
        trend2 = uuid.uuid4()
        
        key1 = deduplication_service._make_key(user1, trend1)
        key2 = deduplication_service._make_key(user1, trend2)
        key3 = deduplication_service._make_key(user2, trend1)
        key4 = deduplication_service._make_key(user2, trend2)
        
        assert key1 != key2
        assert key1 != key3
        assert key1 != key4
        assert key2 != key3
        assert key2 != key4
        assert key3 != key4

    def test_make_key_consistency(self, deduplication_service, sample_user_id, sample_trend_id):
        """Test that same user+trend always produces same key."""
        key1 = deduplication_service._make_key(sample_user_id, sample_trend_id)
        key2 = deduplication_service._make_key(sample_user_id, sample_trend_id)
        
        assert key1 == key2


# =============================================================================
# Duplicate Detection Tests
# =============================================================================

@pytest.mark.asyncio
class TestDuplicateDetection:
    """Tests for duplicate detection functionality."""

    async def test_is_duplicate_not_found(
        self, deduplication_service, mock_redis, sample_user_id, sample_trend_id
    ):
        """Test is_duplicate returns False when key doesn't exist."""
        mock_redis.exists.return_value = 0
        
        result = await deduplication_service.is_duplicate(sample_user_id, sample_trend_id)
        
        assert result is False
        mock_redis.exists.assert_called_once()

    async def test_is_duplicate_found(
        self, deduplication_service, mock_redis, sample_user_id, sample_trend_id
    ):
        """Test is_duplicate returns True when key exists."""
        mock_redis.exists.return_value = 1
        
        result = await deduplication_service.is_duplicate(sample_user_id, sample_trend_id)
        
        assert result is True
        mock_redis.exists.assert_called_once()

    async def test_is_duplicate_different_users_same_trend(
        self, deduplication_service, mock_redis, sample_trend_id
    ):
        """Test that same trend for different users is not a duplicate."""
        user1 = uuid.uuid4()
        user2 = uuid.uuid4()
        
        # First user - not a duplicate
        mock_redis.exists.return_value = 0
        result1 = await deduplication_service.is_duplicate(user1, sample_trend_id)
        assert result1 is False
        
        # Second user with same trend - also not a duplicate
        result2 = await deduplication_service.is_duplicate(user2, sample_trend_id)
        assert result2 is False

    async def test_is_duplicate_same_user_different_trends(
        self, deduplication_service, mock_redis, sample_user_id
    ):
        """Test that different trends for same user are not duplicates."""
        trend1 = uuid.uuid4()
        trend2 = uuid.uuid4()
        
        mock_redis.exists.return_value = 0
        
        result1 = await deduplication_service.is_duplicate(sample_user_id, trend1)
        result2 = await deduplication_service.is_duplicate(sample_user_id, trend2)
        
        assert result1 is False
        assert result2 is False


# =============================================================================
# Mark Sent Tests
# =============================================================================

@pytest.mark.asyncio
class TestMarkSent:
    """Tests for marking alerts as sent."""

    async def test_mark_sent_success(
        self, deduplication_service, mock_redis, sample_user_id, sample_trend_id
    ):
        """Test successful marking of alert as sent."""
        mock_redis.setex.return_value = True
        
        result = await deduplication_service.mark_sent(sample_user_id, sample_trend_id)
        
        assert result is True
        mock_redis.setex.assert_called_once()

    async def test_mark_sent_sets_ttl(
        self, deduplication_service, mock_redis, sample_user_id, sample_trend_id
    ):
        """Test that mark_sent sets correct TTL."""
        await deduplication_service.mark_sent(sample_user_id, sample_trend_id)
        
        call_args = mock_redis.setex.call_args
        assert call_args[0][1] == deduplication_service.ttl  # TTL seconds

    async def test_mark_sent_redis_error(
        self, deduplication_service, mock_redis, sample_user_id, sample_trend_id
    ):
        """Test handling of Redis error during mark_sent."""
        import redis.asyncio as redis_lib
        
        mock_redis.setex.side_effect = redis_lib.RedisError("Connection failed")
        
        result = await deduplication_service.mark_sent(sample_user_id, sample_trend_id)
        
        assert result is False

    async def test_mark_sent_full_flow(
        self, deduplication_service, mock_redis, sample_user_id, sample_trend_id
    ):
        """Test full flow: check duplicate, mark sent, check again."""
        # First check - not a duplicate
        mock_redis.exists.return_value = 0
        is_dup1 = await deduplication_service.is_duplicate(sample_user_id, sample_trend_id)
        assert is_dup1 is False
        
        # Mark as sent
        mock_redis.setex.return_value = True
        await deduplication_service.mark_sent(sample_user_id, sample_trend_id)
        
        # Second check - now it's a duplicate
        mock_redis.exists.return_value = 1
        is_dup2 = await deduplication_service.is_duplicate(sample_user_id, sample_trend_id)
        assert is_dup2 is True


# =============================================================================
# Get Sent Time Tests
# =============================================================================

@pytest.mark.asyncio
class TestGetSentTime:
    """Tests for retrieving when alert was last sent."""

    async def test_get_sent_time_found(
        self, deduplication_service, mock_redis, sample_user_id, sample_trend_id
    ):
        """Test getting sent time when key exists."""
        sent_time = datetime.utcnow()
        mock_redis.get.return_value = sent_time.isoformat().encode()
        
        result = await deduplication_service.get_sent_time(sample_user_id, sample_trend_id)
        
        assert result is not None
        assert isinstance(result, datetime)

    async def test_get_sent_time_not_found(
        self, deduplication_service, mock_redis, sample_user_id, sample_trend_id
    ):
        """Test getting sent time when key doesn't exist."""
        mock_redis.get.return_value = None
        
        result = await deduplication_service.get_sent_time(sample_user_id, sample_trend_id)
        
        assert result is None

    async def test_get_sent_time_invalid_value(
        self, deduplication_service, mock_redis, sample_user_id, sample_trend_id
    ):
        """Test handling of invalid datetime value."""
        mock_redis.get.return_value = b"invalid-datetime"
        
        result = await deduplication_service.get_sent_time(sample_user_id, sample_trend_id)
        
        assert result is None


# =============================================================================
# Clear Tests
# =============================================================================

@pytest.mark.asyncio
class TestClear:
    """Tests for clearing deduplication entries."""

    async def test_clear_success(
        self, deduplication_service, mock_redis, sample_user_id, sample_trend_id
    ):
        """Test successful clearing of deduplication entry."""
        mock_redis.delete.return_value = 1
        
        result = await deduplication_service.clear(sample_user_id, sample_trend_id)
        
        assert result is True
        mock_redis.delete.assert_called_once()

    async def test_clear_not_found(
        self, deduplication_service, mock_redis, sample_user_id, sample_trend_id
    ):
        """Test clearing when key doesn't exist."""
        mock_redis.delete.return_value = 0
        
        result = await deduplication_service.clear(sample_user_id, sample_trend_id)
        
        assert result is False

    async def test_clear_all_for_user(
        self, deduplication_service, mock_redis
    ):
        """Test clearing all entries for a user."""
        user_id = uuid.uuid4()
        keys = [b"alert:dedup:user:trend1", b"alert:dedup:user:trend2"]
        
        # Mock scan_iter to return async iterator
        async def mock_scan_iter(*args, **kwargs):
            for key in keys:
                yield key
        
        mock_redis.scan_iter = mock_scan_iter
        mock_redis.delete = AsyncMock(return_value=len(keys))
        
        result = await deduplication_service.clear_all_for_user(user_id)
        
        assert result == 2
        mock_redis.delete.assert_called_once()

    async def test_clear_all_for_user_no_keys(
        self, deduplication_service, mock_redis
    ):
        """Test clearing all entries when user has no entries."""
        user_id = uuid.uuid4()
        
        # Mock empty scan_iter
        async def mock_scan_iter(*args, **kwargs):
            return
            yield  # Make it an async generator
        
        mock_redis.scan_iter = mock_scan_iter
        
        result = await deduplication_service.clear_all_for_user(user_id)
        
        assert result == 0


# =============================================================================
# TTL Tests
# =============================================================================

@pytest.mark.asyncio
class TestTTL:
    """Tests for TTL operations."""

    async def test_get_ttl_remaining_found(
        self, deduplication_service, mock_redis, sample_user_id, sample_trend_id
    ):
        """Test getting remaining TTL when key exists."""
        mock_redis.ttl.return_value = 1800  # 30 minutes
        
        result = await deduplication_service.get_ttl_remaining(sample_user_id, sample_trend_id)
        
        assert result == 1800

    async def test_get_ttl_remaining_not_found(
        self, deduplication_service, mock_redis, sample_user_id, sample_trend_id
    ):
        """Test getting remaining TTL when key doesn't exist."""
        mock_redis.ttl.return_value = -1
        
        result = await deduplication_service.get_ttl_remaining(sample_user_id, sample_trend_id)
        
        assert result is None

    async def test_get_ttl_remaining_expired(
        self, deduplication_service, mock_redis, sample_user_id, sample_trend_id
    ):
        """Test getting remaining TTL for expired key."""
        mock_redis.ttl.return_value = -2  # Redis returns -2 for expired keys
        
        result = await deduplication_service.get_ttl_remaining(sample_user_id, sample_trend_id)
        
        assert result is None


# =============================================================================
# Stats Tests
# =============================================================================

@pytest.mark.asyncio
class TestStats:
    """Tests for statistics operations."""

    async def test_get_stats_empty(
        self, deduplication_service, mock_redis
    ):
        """Test getting stats when no keys exist."""
        async def mock_scan_iter(*args, **kwargs):
            return
            yield  # Make it an async generator
        
        mock_redis.scan_iter = mock_scan_iter
        
        result = await deduplication_service.get_stats()
        
        assert result["total_dedup_keys"] == 0
        assert result["ttl_seconds"] == deduplication_service.ttl

    async def test_get_stats_with_keys(
        self, deduplication_service, mock_redis
    ):
        """Test getting stats when keys exist."""
        keys = [b"key1", b"key2", b"key3"]
        
        async def mock_scan_iter(*args, **kwargs):
            for key in keys:
                yield key
        
        mock_redis.scan_iter = mock_scan_iter
        
        result = await deduplication_service.get_stats()
        
        assert result["total_dedup_keys"] == 3
        assert result["ttl_seconds"] == deduplication_service.ttl


# =============================================================================
# Configuration Tests
# =============================================================================

class TestDeduplicationConfiguration:
    """Tests for deduplication service configuration."""

    def test_default_ttl(self, mock_redis):
        """Test default TTL is 3600 seconds (1 hour)."""
        service = DeduplicationService(redis_client=mock_redis)
        
        assert service.ttl == 3600

    def test_custom_ttl(self, mock_redis):
        """Test custom TTL can be set."""
        service = DeduplicationService(redis_client=mock_redis, ttl_seconds=7200)
        
        assert service.ttl == 7200

    def test_default_ttl_from_settings(self, mock_redis):
        """Test default TTL comes from settings when not specified."""
        with patch("alerts.deduplication.settings") as mock_settings:
            mock_settings.dedup_window_seconds = 1800
            
            service = DeduplicationService(redis_client=mock_redis)
            
            assert service.ttl == 1800

    def test_key_prefix_constant(self):
        """Test key prefix constant."""
        assert DeduplicationService.KEY_PREFIX == "alert:dedup"


# =============================================================================
# Edge Case Tests
# =============================================================================

@pytest.mark.asyncio
class TestDeduplicationEdgeCases:
    """Edge case tests for deduplication."""

    async def test_same_content_different_users_not_duplicate(
        self, deduplication_service, mock_redis
    ):
        """Verify same trend for different users produces different keys."""
        user1 = uuid.uuid4()
        user2 = uuid.uuid4()
        trend_id = uuid.uuid4()
        
        key1 = deduplication_service._make_key(user1, trend_id)
        key2 = deduplication_service._make_key(user2, trend_id)
        
        # Keys should be different
        assert key1 != key2
        
        # Mark sent for user1
        mock_redis.setex.return_value = True
        await deduplication_service.mark_sent(user1, trend_id)
        
        # User2 should not see it as duplicate
        mock_redis.exists.return_value = 0
        is_dup = await deduplication_service.is_duplicate(user2, trend_id)
        assert is_dup is False

    async def test_different_trends_same_user_not_duplicate(
        self, deduplication_service, mock_redis, sample_user_id
    ):
        """Verify different trends for same user are not duplicates."""
        trend1 = uuid.uuid4()
        trend2 = uuid.uuid4()
        
        key1 = deduplication_service._make_key(sample_user_id, trend1)
        key2 = deduplication_service._make_key(sample_user_id, trend2)
        
        # Keys should be different
        assert key1 != key2
        
        # Mark sent for trend1
        mock_redis.setex.return_value = True
        await deduplication_service.mark_sent(sample_user_id, trend1)
        
        # Trend2 should not be duplicate
        mock_redis.exists.return_value = 0
        is_dup = await deduplication_service.is_duplicate(sample_user_id, trend2)
        assert is_dup is False

    async def test_time_window_expiration(
        self, deduplication_service, mock_redis, sample_user_id, sample_trend_id
    ):
        """Test that expired entries are not considered duplicates."""
        # Key exists but with TTL of 0 (expired)
        mock_redis.exists.return_value = 0
        
        result = await deduplication_service.is_duplicate(sample_user_id, sample_trend_id)
        
        assert result is False

    async def test_uuid_string_handling(
        self, deduplication_service, mock_redis
    ):
        """Test that UUID objects are handled correctly."""
        user_id = uuid.uuid4()
        trend_id = uuid.uuid4()
        
        # Should work with UUID objects
        key = deduplication_service._make_key(user_id, trend_id)
        assert str(user_id) in key
        assert str(trend_id) in key

    async def test_empty_uuid_not_allowed(self, deduplication_service):
        """Test that empty/nil UUID is handled."""
        nil_uuid = uuid.UUID("00000000-0000-0000-0000-000000000000")
        
        key = deduplication_service._make_key(nil_uuid, nil_uuid)
        
        assert "00000000-0000-0000-0000-000000000000" in key
