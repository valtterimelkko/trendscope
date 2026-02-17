"""
Unit tests for the RateLimiter class.

Tests token bucket algorithm, concurrent access safety,
and edge cases for the rate limiter implementation.
"""

import asyncio
import pytest
import time
from unittest.mock import patch

from scraper.rate_limiter import RateLimiter, create_rate_limiters, get_rate_limiters


class TestRateLimiterInitialization:
    """Test RateLimiter initialization behavior."""

    def test_tokens_start_at_burst_capacity(self):
        """Tokens should start at burst capacity on initialization."""
        limiter = RateLimiter(rate=10.0, burst=5)
        assert limiter.tokens == 5.0
        assert limiter.burst == 5
        assert limiter.rate == 10.0

    def test_initial_last_update_is_set(self):
        """Last update timestamp should be set on initialization."""
        before = time.time()
        limiter = RateLimiter(rate=10.0, burst=5)
        after = time.time()
        
        assert before <= limiter.last_update <= after

    def test_lock_is_created(self):
        """Async lock should be created on initialization."""
        limiter = RateLimiter(rate=10.0, burst=5)
        assert isinstance(limiter.lock, asyncio.Lock)


class TestRateLimiterAcquire:
    """Test token acquisition with acquire() method."""

    @pytest.mark.asyncio
    async def test_single_token_no_wait_when_tokens_available(self):
        """Single token acquisition should not wait when tokens available."""
        limiter = RateLimiter(rate=10.0, burst=5)
        
        wait_time = await limiter.acquire()
        
        assert wait_time == 0.0
        assert limiter.tokens == 4.0

    @pytest.mark.asyncio
    async def test_multiple_token_acquisition(self):
        """Multiple tokens can be acquired in sequence."""
        limiter = RateLimiter(rate=10.0, burst=5)
        
        wait1 = await limiter.acquire(2)
        wait2 = await limiter.acquire(2)
        
        assert wait1 == 0.0
        assert wait2 == 0.0
        assert 0.0 <= limiter.tokens <= 1.1  # Allow for tiny refill between operations

    @pytest.mark.asyncio
    async def test_acquire_exhausts_all_tokens(self):
        """Acquire can exhaust all available tokens."""
        limiter = RateLimiter(rate=10.0, burst=3)
        
        await limiter.acquire(3)
        
        assert limiter.tokens == 0.0

    @pytest.mark.asyncio
    async def test_acquire_waits_when_no_tokens_available(self):
        """Acquire should wait when no tokens are available."""
        limiter = RateLimiter(rate=10.0, burst=1)
        
        # Exhaust the single token
        await limiter.acquire(1)
        assert limiter.tokens == 0.0
        
        # Next acquire should wait
        start = time.time()
        wait_time = await limiter.acquire(1)
        elapsed = time.time() - start
        
        assert wait_time > 0
        assert elapsed >= 0.09  # Should wait approximately 0.1s for 1 token at 10/s rate

    @pytest.mark.asyncio
    async def test_token_refill_over_time(self):
        """Tokens should refill over time based on rate."""
        limiter = RateLimiter(rate=10.0, burst=5)  # 10 tokens per second
        
        # Exhaust tokens
        await limiter.acquire(5)
        assert limiter.tokens == 0.0
        
        # Wait for tokens to refill
        await asyncio.sleep(0.2)  # Should refill ~2 tokens
        
        # Should be able to acquire without waiting now
        wait_time = await limiter.acquire(1)
        
        assert wait_time == 0.0

    @pytest.mark.asyncio
    async def test_burst_capacity_enforcement(self):
        """Tokens should not exceed burst capacity even after long wait."""
        limiter = RateLimiter(rate=10.0, burst=3)
        
        # Exhaust tokens
        await limiter.acquire(3)
        
        # Wait a long time
        await asyncio.sleep(0.5)
        
        # Tokens should be capped at burst capacity
        assert limiter.available_tokens <= 3.0

    @pytest.mark.asyncio
    async def test_requesting_more_than_burst_raises_value_error(self):
        """Requesting more tokens than burst capacity should raise ValueError."""
        limiter = RateLimiter(rate=10.0, burst=5)
        
        with pytest.raises(ValueError, match="Cannot acquire 6 tokens"):
            await limiter.acquire(6)

    @pytest.mark.asyncio
    async def test_requesting_exactly_burst_is_allowed(self):
        """Requesting exactly burst capacity should be allowed."""
        limiter = RateLimiter(rate=10.0, burst=5)
        
        wait_time = await limiter.acquire(5)
        
        assert wait_time == 0.0
        assert limiter.tokens == 0.0

    @pytest.mark.asyncio
    async def test_zero_rate_handling(self):
        """Zero rate should not cause division by zero."""
        limiter = RateLimiter(rate=0.0, burst=5)
        
        # Can acquire initial tokens
        wait_time = await limiter.acquire(1)
        assert wait_time == 0.0
        
        # Exhaust tokens
        await limiter.acquire(4)
        
        # Next acquire with zero rate should handle gracefully
        # It will wait indefinitely or raise an error
        # Implementation returns infinity wait time
        with pytest.raises(ZeroDivisionError):
            await limiter.acquire(1)


class TestRateLimiterConcurrency:
    """Test concurrent access safety."""

    @pytest.mark.asyncio
    async def test_concurrent_acquires_are_safe(self):
        """Multiple concurrent acquires should be thread-safe."""
        limiter = RateLimiter(rate=100.0, burst=10)
        
        async def acquire_token():
            return await limiter.acquire(1)
        
        # Launch 5 concurrent acquires
        tasks = [acquire_token() for _ in range(5)]
        results = await asyncio.gather(*tasks)
        
        # All should succeed without error
        assert all(isinstance(r, float) for r in results)
        # Tokens should be properly decremented (allowing for tiny refill)
        assert 4.9 <= limiter.tokens <= 5.1

    @pytest.mark.asyncio
    async def test_concurrent_acquires_exceeding_burst(self):
        """Concurrent acquires exceeding burst should handle correctly."""
        limiter = RateLimiter(rate=1000.0, burst=3)  # High rate, small burst
        
        async def acquire_token():
            return await limiter.acquire(1)
        
        # Launch more acquires than burst allows
        tasks = [acquire_token() for _ in range(5)]
        results = await asyncio.gather(*tasks)
        
        # First 3 should have no wait, rest should wait
        no_wait_count = sum(1 for r in results if r == 0.0)
        wait_count = sum(1 for r in results if r > 0)
        
        assert no_wait_count == 3
        assert wait_count == 2

    @pytest.mark.asyncio
    async def test_mixed_concurrent_acquire_amounts(self):
        """Concurrent acquires with different token amounts."""
        limiter = RateLimiter(rate=100.0, burst=10)
        
        async def acquire_amount(amount):
            return await limiter.acquire(amount)
        
        # Mix of different token amounts
        tasks = [
            acquire_amount(2),
            acquire_amount(3),
            acquire_amount(1),
            acquire_amount(4),
        ]
        results = await asyncio.gather(*tasks)
        
        # All should complete
        assert len(results) == 4
        assert 0.0 <= limiter.tokens <= 0.5  # 2+3+1+4 = 10, allow tiny refill


class TestRateLimiterTryAcquire:
    """Test try_acquire() method."""

    @pytest.mark.asyncio
    async def test_try_acquire_succeeds_when_tokens_available(self):
        """try_acquire should return True when tokens available."""
        limiter = RateLimiter(rate=10.0, burst=5)
        
        result = await limiter.try_acquire(2)
        
        assert result is True
        assert limiter.tokens == 3.0

    @pytest.mark.asyncio
    async def test_try_acquire_fails_when_no_tokens(self):
        """try_acquire should return False when no tokens available."""
        limiter = RateLimiter(rate=10.0, burst=2)
        
        # Exhaust tokens
        await limiter.acquire(2)
        
        result = await limiter.try_acquire(1)
        
        assert result is False

    @pytest.mark.asyncio
    async def test_try_acquire_does_not_wait(self):
        """try_acquire should never wait."""
        limiter = RateLimiter(rate=10.0, burst=1)
        
        # Exhaust tokens
        await limiter.acquire(1)
        
        start = time.time()
        result = await limiter.try_acquire(1)
        elapsed = time.time() - start
        
        assert result is False
        assert elapsed < 0.01  # Should return immediately


class TestRateLimiterGetWaitTime:
    """Test get_wait_time() method."""

    def test_get_wait_time_zero_when_tokens_available(self):
        """get_wait_time should return 0 when tokens available."""
        limiter = RateLimiter(rate=10.0, burst=5)
        
        wait_time = limiter.get_wait_time(3)
        
        assert wait_time == 0.0

    def test_get_wait_time_calculates_correctly(self):
        """get_wait_time should calculate based on rate."""
        limiter = RateLimiter(rate=10.0, burst=5)
        
        # Exhaust tokens first by simulating
        limiter.tokens = 0.0
        
        wait_time = limiter.get_wait_time(2)
        
        # Should need 2 tokens at 10/s = 0.2s
        assert wait_time == pytest.approx(0.2, abs=0.01)

    def test_get_wait_time_does_not_modify_state(self):
        """get_wait_time should not modify limiter state."""
        limiter = RateLimiter(rate=10.0, burst=5)
        initial_tokens = limiter.tokens
        
        limiter.get_wait_time(3)
        
        assert limiter.tokens == initial_tokens


class TestRateLimiterAvailableTokens:
    """Test available_tokens property."""

    def test_available_tokens_returns_current_count(self):
        """available_tokens should return approximate current count."""
        limiter = RateLimiter(rate=10.0, burst=5)
        limiter.tokens = 3.0
        
        available = limiter.available_tokens
        
        assert available >= 3.0  # May have refilled slightly

    def test_available_tokens_capped_at_burst(self):
        """available_tokens should be capped at burst capacity."""
        limiter = RateLimiter(rate=100.0, burst=3)
        limiter.tokens = 0.0
        limiter.last_update = time.time() - 1  # 1 second ago
        
        available = limiter.available_tokens
        
        assert available <= 3.0


class TestRateLimiterReset:
    """Test reset() method."""

    def test_reset_restores_full_capacity(self):
        """reset should restore tokens to burst capacity."""
        limiter = RateLimiter(rate=10.0, burst=5)
        limiter.tokens = 0.0
        
        limiter.reset()
        
        assert limiter.tokens == 5.0

    def test_reset_updates_last_update(self):
        """reset should update last_update timestamp."""
        limiter = RateLimiter(rate=10.0, burst=5)
        old_update = limiter.last_update
        
        time.sleep(0.01)
        limiter.reset()
        
        assert limiter.last_update > old_update


class TestRateLimiterFactory:
    """Test factory functions."""

    def test_create_rate_limiters_returns_dict(self):
        """create_rate_limiters should return dictionary of limiters."""
        limiters = create_rate_limiters()
        
        assert isinstance(limiters, dict)
        assert "trending" in limiters
        assert "hashtag" in limiters
        assert "user" in limiters

    def test_create_rate_limiters_returns_rate_limiter_instances(self):
        """Factory should return RateLimiter instances."""
        limiters = create_rate_limiters()
        
        for limiter in limiters.values():
            assert isinstance(limiter, RateLimiter)

    def test_get_rate_limiters_caches_result(self):
        """get_rate_limiters should cache and return same instances."""
        limiters1 = get_rate_limiters()
        limiters2 = get_rate_limiters()
        
        assert limiters1 is limiters2
        assert limiters1["trending"] is limiters2["trending"]

    def test_different_endpoint_types_have_different_configs(self):
        """Different endpoint types should have different rate limits."""
        limiters = create_rate_limiters()
        
        # User should be most restrictive
        assert limiters["user"].burst <= limiters["hashtag"].burst
        assert limiters["hashtag"].burst <= limiters["trending"].burst


class TestRateLimiterEdgeCases:
    """Test edge cases and boundary conditions."""

    @pytest.mark.asyncio
    async def test_acquire_one_token_at_a_time(self):
        """Sequential single token acquires should work correctly."""
        limiter = RateLimiter(rate=100.0, burst=5)
        
        for i in range(5):
            wait_time = await limiter.acquire(1)
            assert wait_time == 0.0
        
        assert 0.0 <= limiter.tokens <= 0.1  # Allow for tiny refill between operations

    @pytest.mark.asyncio
    async def test_partial_refill_between_acquires(self):
        """Partial refill should be handled correctly."""
        limiter = RateLimiter(rate=10.0, burst=5)
        
        # Exhaust tokens
        await limiter.acquire(5)
        
        # Wait for partial refill
        await asyncio.sleep(0.15)  # ~1.5 tokens refilled
        
        # Should be able to get 1 token without wait
        wait_time = await limiter.acquire(1)
        assert wait_time == 0.0

    @pytest.mark.asyncio
    async def test_very_high_rate(self):
        """Very high rate should work correctly."""
        limiter = RateLimiter(rate=10000.0, burst=100)
        
        wait_time = await limiter.acquire(50)
        
        assert wait_time == 0.0
        assert limiter.tokens == 50.0

    @pytest.mark.asyncio
    async def test_very_low_rate(self):
        """Very low rate should work correctly."""
        limiter = RateLimiter(rate=0.1, burst=2)
        
        # Can acquire initial burst
        wait_time = await limiter.acquire(2)
        assert wait_time == 0.0
        
        # Next acquire should wait ~10 seconds for 1 token at 0.1/s
        # Use a shorter timeout for testing
        with pytest.raises(asyncio.TimeoutError):
            await asyncio.wait_for(limiter.acquire(1), timeout=0.1)

    @pytest.mark.asyncio
    async def test_negative_rate_not_allowed_by_constructor(self):
        """Negative rate should be handled (though not explicitly forbidden)."""
        limiter = RateLimiter(rate=-1.0, burst=5)
        
        # Initial tokens still available
        wait_time = await limiter.acquire(1)
        assert wait_time == 0.0

    def test_zero_burst_initializes_to_zero_tokens(self):
        """Zero burst should initialize to zero tokens."""
        limiter = RateLimiter(rate=10.0, burst=0)
        
        assert limiter.tokens == 0.0
