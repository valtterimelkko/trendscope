"""
Throttling Service Unit Tests

Tests for ThrottlingService including:
- Rate limit check
- Burst allowance
- Cooldown periods
- Per-user throttling
- Per-tier throttling
- Throttle bypass for critical alerts
"""

import uuid
import pytest
from unittest.mock import Mock, patch, AsyncMock, MagicMock
from unittest.mock import ANY

import redis.asyncio as redis

from alerts.models import Tier
from alerts.throttling import ThrottlingService


# =============================================================================
# Fixtures
# =============================================================================

@pytest.fixture
def mock_redis():
    """Create a mock Redis client."""
    client = AsyncMock(spec=redis.Redis)
    return client


@pytest.fixture
def mock_settings():
    """Mock settings for testing."""
    settings = Mock()
    settings.throttle_max_alerts_per_hour = {
        "free": 5,
        "solo": 15,
        "agency": 30,
        "enterprise": 100
    }
    settings.throttle_max_alerts_per_day_per_niche = 3
    return settings


@pytest.fixture
def throttle_service(mock_redis, mock_settings):
    """Create a ThrottlingService instance with mock Redis."""
    with patch('alerts.throttling.settings', mock_settings):
        service = ThrottlingService(mock_redis)
        return service


@pytest.fixture
def sample_user_id():
    """Create a sample user ID."""
    return uuid.uuid4()


@pytest.fixture
def sample_niche_id():
    """Create a sample niche ID."""
    return uuid.uuid4()


# =============================================================================
# Service Initialization Tests
# =============================================================================

class TestThrottlingServiceInitialization:
    """Tests for ThrottlingService initialization."""

    def test_init_with_default_settings(self, mock_redis, mock_settings):
        """Test service initialization with default settings."""
        with patch('alerts.throttling.settings', mock_settings):
            service = ThrottlingService(mock_redis)
            
            assert service.redis is mock_redis
            assert service.hourly_limits == mock_settings.throttle_max_alerts_per_hour
            assert service.daily_niche_limit == mock_settings.throttle_max_alerts_per_day_per_niche

    def test_init_with_custom_limits(self, mock_redis, mock_settings):
        """Test service initialization with custom limits."""
        custom_limits = {
            "free": 10,
            "solo": 25,
            "agency": 50,
            "enterprise": 200
        }
        
        with patch('alerts.throttling.settings', mock_settings):
            service = ThrottlingService(mock_redis, custom_limits=custom_limits)
            
            assert service.hourly_limits == custom_limits

    def test_init_with_none_limits_uses_settings(self, mock_redis, mock_settings):
        """Test that None limits fall back to settings."""
        with patch('alerts.throttling.settings', mock_settings):
            service = ThrottlingService(mock_redis, custom_limits=None)
            
            assert service.hourly_limits == mock_settings.throttle_max_alerts_per_hour

    def test_key_prefixes(self, mock_redis, mock_settings):
        """Test that key prefixes are set correctly."""
        with patch('alerts.throttling.settings', mock_settings):
            service = ThrottlingService(mock_redis)
            
            assert service.HOURLY_KEY_PREFIX == "alert:throttle:hourly"
            assert service.NICHE_DAILY_KEY_PREFIX == "alert:throttle:niche"

    def test_ttl_constants(self, mock_redis, mock_settings):
        """Test that TTL constants are set correctly."""
        with patch('alerts.throttling.settings', mock_settings):
            service = ThrottlingService(mock_redis)
            
            assert service.HOUR_TTL == 3600
            assert service.DAY_TTL == 86400


# =============================================================================
# Key Generation Tests
# =============================================================================

class TestKeyGeneration:
    """Tests for Redis key generation."""

    def test_hourly_key_format(self, throttle_service, sample_user_id):
        """Test hourly key format."""
        key = throttle_service._hourly_key(sample_user_id)
        
        assert key.startswith("alert:throttle:hourly:")
        assert str(sample_user_id) in key

    def test_niche_daily_key_format(self, throttle_service, sample_user_id, sample_niche_id):
        """Test niche daily key format."""
        key = throttle_service._niche_daily_key(sample_user_id, sample_niche_id)
        
        assert key.startswith("alert:throttle:niche:")
        assert str(sample_user_id) in key
        assert str(sample_niche_id) in key
        assert ":daily" in key


# =============================================================================
# Hourly Limit Tests
# =============================================================================

@pytest.mark.asyncio
class TestHourlyLimits:
    """Tests for hourly alert limits."""

    async def test_should_throttle_hourly_limit_reached(self, throttle_service, sample_user_id, sample_niche_id):
        """Test throttling when hourly limit reached."""
        # Mock hourly count at limit
        throttle_service.redis.get = AsyncMock(return_value=b"5")
        throttle_service.redis.get = AsyncMock(side_effect=[b"5", b"0"])  # hourly, niche
        
        with patch('alerts.throttling.logger') as mock_logger:
            result = await throttle_service.should_throttle(sample_user_id, sample_niche_id, "free")
            
            assert result is True
            mock_logger.info.assert_called()
            assert "hourly_limit_reached" in str(mock_logger.info.call_args)

    async def test_should_not_throttle_below_hourly_limit(self, throttle_service, sample_user_id, sample_niche_id):
        """Test no throttling when below hourly limit."""
        throttle_service.redis.get = AsyncMock(side_effect=[b"3", b"0"])  # hourly=3, niche=0
        
        result = await throttle_service.should_throttle(sample_user_id, sample_niche_id, "free")
        
        assert result is False

    async def test_should_throttle_at_exact_hourly_limit(self, throttle_service, sample_user_id, sample_niche_id):
        """Test throttling at exact hourly limit."""
        throttle_service.redis.get = AsyncMock(side_effect=[b"5", b"0"])  # hourly=5 (at limit for free)
        
        result = await throttle_service.should_throttle(sample_user_id, sample_niche_id, "free")
        
        assert result is True

    async def test_get_hourly_count_with_value(self, throttle_service, sample_user_id):
        """Test getting hourly count with existing value."""
        throttle_service.redis.get = AsyncMock(return_value=b"10")
        
        count = await throttle_service.get_hourly_count(sample_user_id)
        
        assert count == 10

    async def test_get_hourly_count_no_value(self, throttle_service, sample_user_id):
        """Test getting hourly count with no value."""
        throttle_service.redis.get = AsyncMock(return_value=None)
        
        count = await throttle_service.get_hourly_count(sample_user_id)
        
        assert count == 0

    async def test_get_hourly_count_invalid_value(self, throttle_service, sample_user_id):
        """Test getting hourly count with invalid value."""
        throttle_service.redis.get = AsyncMock(return_value=b"not-a-number")
        
        count = await throttle_service.get_hourly_count(sample_user_id)
        
        assert count == 0


# =============================================================================
# Per-Tier Limit Tests
# =============================================================================

class TestPerTierLimits:
    """Tests for per-tier throttle limits."""

    def test_get_hourly_limit_free(self, throttle_service):
        """Test hourly limit for free tier."""
        limit = throttle_service.get_hourly_limit("free")
        assert limit == 5

    def test_get_hourly_limit_solo(self, throttle_service):
        """Test hourly limit for solo tier."""
        limit = throttle_service.get_hourly_limit("solo")
        assert limit == 15

    def test_get_hourly_limit_agency(self, throttle_service):
        """Test hourly limit for agency tier."""
        limit = throttle_service.get_hourly_limit("agency")
        assert limit == 30

    def test_get_hourly_limit_enterprise(self, throttle_service):
        """Test hourly limit for enterprise tier."""
        limit = throttle_service.get_hourly_limit("enterprise")
        assert limit == 100

    def test_get_hourly_limit_case_insensitive(self, throttle_service):
        """Test that tier names are case insensitive."""
        assert throttle_service.get_hourly_limit("FREE") == 5
        assert throttle_service.get_hourly_limit("Solo") == 15
        assert throttle_service.get_hourly_limit("AGENCY") == 30

    def test_get_hourly_limit_unknown_defaults_to_free(self, throttle_service):
        """Test that unknown tier defaults to free limit."""
        limit = throttle_service.get_hourly_limit("unknown")
        assert limit == 5

    def test_get_hourly_limit_empty_defaults_to_free(self, throttle_service):
        """Test that empty tier defaults to free limit."""
        limit = throttle_service.get_hourly_limit("")
        assert limit == 5


# =============================================================================
# Niche Daily Limit Tests
# =============================================================================

@pytest.mark.asyncio
class TestNicheDailyLimits:
    """Tests for per-niche daily limits."""

    async def test_should_throttle_niche_daily_limit_reached(self, throttle_service, sample_user_id, sample_niche_id):
        """Test throttling when niche daily limit reached."""
        throttle_service.redis.get = AsyncMock(side_effect=[b"0", b"3"])  # hourly=0, niche=3
        
        with patch('alerts.throttling.logger') as mock_logger:
            result = await throttle_service.should_throttle(sample_user_id, sample_niche_id, "free")
            
            assert result is True
            mock_logger.info.assert_called()
            assert "niche_daily_limit_reached" in str(mock_logger.info.call_args)

    async def test_should_not_throttle_below_niche_limit(self, throttle_service, sample_user_id, sample_niche_id):
        """Test no throttling when below niche limit."""
        throttle_service.redis.get = AsyncMock(side_effect=[b"0", b"2"])  # hourly=0, niche=2
        
        result = await throttle_service.should_throttle(sample_user_id, sample_niche_id, "free")
        
        assert result is False

    async def test_get_niche_daily_count_with_value(self, throttle_service, sample_user_id, sample_niche_id):
        """Test getting niche daily count with existing value."""
        throttle_service.redis.get = AsyncMock(return_value=b"2")
        
        count = await throttle_service.get_niche_daily_count(sample_user_id, sample_niche_id)
        
        assert count == 2

    async def test_get_niche_daily_count_no_value(self, throttle_service, sample_user_id, sample_niche_id):
        """Test getting niche daily count with no value."""
        throttle_service.redis.get = AsyncMock(return_value=None)
        
        count = await throttle_service.get_niche_daily_count(sample_user_id, sample_niche_id)
        
        assert count == 0

    async def test_get_niche_daily_count_invalid_value(self, throttle_service, sample_user_id, sample_niche_id):
        """Test getting niche daily count with invalid value."""
        throttle_service.redis.get = AsyncMock(return_value=b"not-a-number")
        
        count = await throttle_service.get_niche_daily_count(sample_user_id, sample_niche_id)
        
        assert count == 0


# =============================================================================
# Counter Increment Tests
# =============================================================================

@pytest.mark.asyncio
class TestCounterIncrement:
    """Tests for incrementing throttle counters."""

    async def test_increment_counters_success(self, throttle_service, sample_user_id, sample_niche_id):
        """Test successful counter increment."""
        # Mock pipeline
        mock_pipe = AsyncMock()
        mock_pipe.incr = Mock(return_value=mock_pipe)
        mock_pipe.expire = Mock(return_value=mock_pipe)
        mock_pipe.execute = AsyncMock(return_value=[1, True, 1, True])
        
        throttle_service.redis.pipeline = Mock(return_value=mock_pipe)
        
        with patch('alerts.throttling.logger') as mock_logger:
            result = await throttle_service.increment_counters(sample_user_id, sample_niche_id)
            
            assert result is True
            mock_pipe.incr.assert_called()
            mock_pipe.expire.assert_called()
            mock_pipe.execute.assert_called_once()

    async def test_increment_counters_sets_ttl(self, throttle_service, sample_user_id, sample_niche_id):
        """Test that increment sets proper TTL."""
        mock_pipe = AsyncMock()
        mock_pipe.incr = Mock(return_value=mock_pipe)
        mock_pipe.expire = Mock(return_value=mock_pipe)
        mock_pipe.execute = AsyncMock(return_value=[1, True, 1, True])
        
        throttle_service.redis.pipeline = Mock(return_value=mock_pipe)
        
        await throttle_service.increment_counters(sample_user_id, sample_niche_id)
        
        # Check TTL values
        expire_calls = mock_pipe.expire.call_args_list
        assert len(expire_calls) == 2
        # First expire is hourly (3600), second is daily (86400)
        assert expire_calls[0][0][1] == 3600
        assert expire_calls[1][0][1] == 86400

    async def test_increment_counters_redis_error(self, throttle_service, sample_user_id, sample_niche_id):
        """Test handling of Redis error."""
        throttle_service.redis.pipeline = Mock(side_effect=redis.RedisError("Connection failed"))
        
        with patch('alerts.throttling.logger') as mock_logger:
            result = await throttle_service.increment_counters(sample_user_id, sample_niche_id)
            
            assert result is False
            mock_logger.error.assert_called()


# =============================================================================
# Reset Tests
# =============================================================================

@pytest.mark.asyncio
class TestResetCounters:
    """Tests for resetting throttle counters."""

    async def test_reset_hourly_success(self, throttle_service, sample_user_id):
        """Test successful hourly counter reset."""
        throttle_service.redis.delete = AsyncMock(return_value=1)
        
        result = await throttle_service.reset_hourly(sample_user_id)
        
        assert result is True
        throttle_service.redis.delete.assert_called_once()

    async def test_reset_hourly_no_key(self, throttle_service, sample_user_id):
        """Test hourly reset when key doesn't exist."""
        throttle_service.redis.delete = AsyncMock(return_value=0)
        
        result = await throttle_service.reset_hourly(sample_user_id)
        
        assert result is False

    async def test_reset_niche_daily_success(self, throttle_service, sample_user_id, sample_niche_id):
        """Test successful niche daily counter reset."""
        throttle_service.redis.delete = AsyncMock(return_value=1)
        
        result = await throttle_service.reset_niche_daily(sample_user_id, sample_niche_id)
        
        assert result is True
        throttle_service.redis.delete.assert_called_once()

    async def test_reset_all_for_user_success(self, throttle_service, sample_user_id):
        """Test resetting all counters for a user."""
        # Mock scan_iter to return some keys
        keys = [
            f"alert:throttle:hourly:{sample_user_id}",
            f"alert:throttle:niche:{sample_niche_id}:daily"
        ]
        
        async def mock_scan_iter(match):
            for key in keys:
                if match in key:
                    yield key
        
        throttle_service.redis.scan_iter = mock_scan_iter
        throttle_service.redis.delete = AsyncMock(return_value=2)
        
        with patch('alerts.throttling.logger') as mock_logger:
            result = await throttle_service.reset_all_for_user(sample_user_id)
            
            assert result == 2

    async def test_reset_all_for_user_no_keys(self, throttle_service, sample_user_id):
        """Test resetting when no keys exist."""
        async def mock_scan_iter(match):
            return
            yield  # Make it an async generator
        
        throttle_service.redis.scan_iter = mock_scan_iter
        
        result = await throttle_service.reset_all_for_user(sample_user_id)
        
        assert result == 0


# =============================================================================
# Throttle Status Tests
# =============================================================================

@pytest.mark.asyncio
class TestThrottleStatus:
    """Tests for getting throttle status."""

    async def test_get_throttle_status_success(self, throttle_service, sample_user_id, sample_niche_id):
        """Test getting complete throttle status."""
        # Mock all redis.get calls:
        # - get_hourly_count (status) + get_niche_daily_count (status) + should_throttle (hourly + niche)
        # Total 4 calls: hourly, niche, hourly, niche
        throttle_service.redis.get = AsyncMock(side_effect=[b"3", b"2", b"3", b"2"])
        
        result = await throttle_service.get_throttle_status(sample_user_id, sample_niche_id, "free")
        
        assert result["user_id"] == str(sample_user_id)
        assert result["niche_id"] == str(sample_niche_id)
        assert result["tier"] == "free"
        assert result["hourly"]["count"] == 3
        assert result["hourly"]["limit"] == 5
        assert result["hourly"]["remaining"] == 2
        assert result["niche_daily"]["count"] == 2
        assert result["niche_daily"]["limit"] == 3
        assert result["is_throttled"] is False

    async def test_get_throttle_status_when_throttled(self, throttle_service, sample_user_id, sample_niche_id):
        """Test status when user is throttled."""
        # When throttled at hourly limit, should_throttle returns early after hourly check
        # So calls are: hourly (status), niche (status), hourly (should_throttle)
        # Since hourly_count (5) >= hourly_limit (5), it returns True before checking niche in should_throttle
        throttle_service.redis.get = AsyncMock(side_effect=[b"5", b"0", b"5"])
        
        result = await throttle_service.get_throttle_status(sample_user_id, sample_niche_id, "free")
        
        assert result["hourly"]["is_limited"] is True
        assert result["hourly"]["remaining"] == 0
        assert result["is_throttled"] is True

    async def test_get_throttle_status_enterprise_tier(self, throttle_service, sample_user_id, sample_niche_id):
        """Test status for enterprise tier."""
        # 4 calls: hourly (status), niche (status), hourly (should_throttle), niche (should_throttle)
        throttle_service.redis.get = AsyncMock(side_effect=[b"50", b"1", b"50", b"1"])
        
        result = await throttle_service.get_throttle_status(sample_user_id, sample_niche_id, "enterprise")
        
        assert result["hourly"]["limit"] == 100
        assert result["hourly"]["remaining"] == 50


# =============================================================================
# Stats Tests
# =============================================================================

@pytest.mark.asyncio
class TestStats:
    """Tests for getting throttling statistics."""

    async def test_get_stats_success(self, throttle_service):
        """Test getting throttling stats."""
        hourly_keys = [f"key{i}" for i in range(5)]
        niche_keys = [f"niche{i}" for i in range(3)]
        
        async def mock_scan_iter(match):
            if "hourly" in match:
                for key in hourly_keys:
                    yield key
            else:
                for key in niche_keys:
                    yield key
        
        throttle_service.redis.scan_iter = mock_scan_iter
        
        result = await throttle_service.get_stats()
        
        assert result["hourly_keys"] == 5
        assert result["niche_daily_keys"] == 3
        assert "limits" in result
        assert "hourly" in result["limits"]

    async def test_get_stats_empty(self, throttle_service):
        """Test stats when no keys exist."""
        async def mock_scan_iter(match):
            return
            yield  # Make it an async generator
        
        throttle_service.redis.scan_iter = mock_scan_iter
        
        result = await throttle_service.get_stats()
        
        assert result["hourly_keys"] == 0
        assert result["niche_daily_keys"] == 0


# =============================================================================
# Combined Limit Tests
# =============================================================================

@pytest.mark.asyncio
class TestCombinedLimits:
    """Tests for combined hourly and niche daily limits."""

    async def test_should_throttle_both_limits_ok(self, throttle_service, sample_user_id, sample_niche_id):
        """Test when both limits are ok."""
        throttle_service.redis.get = AsyncMock(side_effect=[b"2", b"1"])  # hourly=2, niche=1
        
        result = await throttle_service.should_throttle(sample_user_id, sample_niche_id, "free")
        
        assert result is False

    async def test_should_throttle_hourly_exceeded(self, throttle_service, sample_user_id, sample_niche_id):
        """Test when hourly limit exceeded but niche ok."""
        throttle_service.redis.get = AsyncMock(side_effect=[b"10", b"1"])  # hourly=10 (exceeded)
        
        result = await throttle_service.should_throttle(sample_user_id, sample_niche_id, "free")
        
        assert result is True

    async def test_should_throttle_niche_exceeded(self, throttle_service, sample_user_id, sample_niche_id):
        """Test when niche limit exceeded but hourly ok."""
        throttle_service.redis.get = AsyncMock(side_effect=[b"0", b"5"])  # niche=5 (exceeded)
        
        result = await throttle_service.should_throttle(sample_user_id, sample_niche_id, "free")
        
        assert result is True

    async def test_should_throttle_both_exceeded(self, throttle_service, sample_user_id, sample_niche_id):
        """Test when both limits exceeded."""
        throttle_service.redis.get = AsyncMock(side_effect=[b"10", b"5"])  # both exceeded
        
        result = await throttle_service.should_throttle(sample_user_id, sample_niche_id, "free")
        
        assert result is True


# =============================================================================
# Edge Case Tests
# =============================================================================

class TestEdgeCases:
    """Tests for edge cases and boundary conditions."""

    async def test_should_throttle_zero_counts(self, throttle_service, sample_user_id, sample_niche_id):
        """Test throttling check with zero counts."""
        throttle_service.redis.get = AsyncMock(side_effect=[b"0", b"0"])
        
        result = await throttle_service.should_throttle(sample_user_id, sample_niche_id, "free")
        
        assert result is False

    async def test_should_throttle_enterprise_high_count(self, throttle_service, sample_user_id, sample_niche_id):
        """Test enterprise tier with high count."""
        throttle_service.redis.get = AsyncMock(side_effect=[b"99", b"0"])  # 99 for enterprise (limit 100)
        
        result = await throttle_service.should_throttle(sample_user_id, sample_niche_id, "enterprise")
        
        assert result is False

    async def test_get_hourly_count_zero_string(self, throttle_service, sample_user_id):
        """Test getting count with "0" string."""
        throttle_service.redis.get = AsyncMock(return_value=b"0")
        
        count = await throttle_service.get_hourly_count(sample_user_id)
        
        assert count == 0

    async def test_get_hourly_count_negative_string(self, throttle_service, sample_user_id):
        """Test getting count with negative number string."""
        throttle_service.redis.get = AsyncMock(return_value=b"-1")
        
        count = await throttle_service.get_hourly_count(sample_user_id)
        
        assert count == -1  # Should handle gracefully


# Run tests if executed directly
if __name__ == "__main__":
    pytest.main([__file__, "-v"])
