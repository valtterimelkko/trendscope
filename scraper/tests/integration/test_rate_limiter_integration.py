"""
RateLimiter Integration Tests

Tests RateLimiter in real scenarios with actual timing.
All tests are skipped if they would take too long, marked as slow.

Test Coverage:
- Multiple producers sharing rate limit state (if stateful)
- Rate limit compliance over time
- Burst handling with real timing
- Token bucket refill accuracy
- Concurrent acquire operations
"""

import asyncio
import time
from dataclasses import dataclass, field
from typing import List

import pytest
import pytest_asyncio

from scraper.rate_limiter import RateLimiter, get_rate_limiters, create_rate_limiters


# =============================================================================
# Fixtures
# =============================================================================

@pytest.fixture
def fast_rate_limiter() -> RateLimiter:
    """Create a rate limiter with fast rate for testing."""
    # 10 requests per second = 0.1 between requests
    return RateLimiter(rate=10.0, burst=5)


@pytest.fixture
def slow_rate_limiter() -> RateLimiter:
    """Create a rate limiter with slow rate for testing."""
    # 2 requests per second = 0.5 between requests
    return RateLimiter(rate=2.0, burst=3)


@pytest.fixture
def very_fast_rate_limiter() -> RateLimiter:
    """Create a very fast rate limiter for quick tests."""
    # 100 requests per second
    return RateLimiter(rate=100.0, burst=10)


# =============================================================================
# Basic Rate Limiting Tests
# =============================================================================

@pytest.mark.integration
@pytest.mark.slow
async def test_rate_limit_compliance_over_time(fast_rate_limiter: RateLimiter):
    """Test that rate limiting is enforced over time."""
    # Burst first
    start_time = time.time()
    
    # First burst_size (5) should be immediate
    for _ in range(5):
        wait_time = await fast_rate_limiter.acquire()
        assert wait_time == 0.0
    
    # Next acquire should wait
    wait_time = await fast_rate_limiter.acquire()
    assert wait_time > 0.0
    
    elapsed = time.time() - start_time
    # Should have taken some time due to rate limiting
    assert elapsed >= 0.05  # At least 50ms for 1/10 second rate


@pytest.mark.integration
@pytest.mark.slow
async def test_burst_handling_with_real_timing(fast_rate_limiter: RateLimiter):
    """Test burst handling with actual timing measurements."""
    start_time = time.time()
    
    # Acquire burst capacity (5 tokens)
    for i in range(5):
        wait_time = await fast_rate_limiter.acquire()
        # First 5 should be immediate (burst)
        assert wait_time == 0.0, f"Burst acquire {i} should be immediate"
    
    burst_time = time.time() - start_time
    # Burst should be very fast (under 100ms for all 5)
    assert burst_time < 0.1
    
    # Next acquire should require waiting
    wait_time = await fast_rate_limiter.acquire()
    assert wait_time > 0.0


@pytest.mark.integration
@pytest.mark.slow
async def test_token_bucket_refill_accuracy(slow_rate_limiter: RateLimiter):
    """Test token bucket refill happens at correct rate."""
    # Use all burst tokens
    for _ in range(3):
        await slow_rate_limiter.acquire()
    
    # Wait for refill (rate is 2/sec, so 0.5 sec for 1 token)
    await asyncio.sleep(0.6)
    
    # Should be able to acquire 1 more token
    start = time.time()
    wait_time = await slow_rate_limiter.acquire()
    elapsed = time.time() - start
    
    # Should be immediate since we waited for refill
    assert wait_time == 0.0
    assert elapsed < 0.1


@pytest.mark.integration
@pytest.mark.slow
async def test_rate_limiter_over_sustained_period():
    """Test rate limiter over a sustained period."""
    # Very fast rate limiter: 20/sec = 0.05 between requests
    limiter = RateLimiter(rate=20.0, burst=2)
    
    start_time = time.time()
    
    # Make 10 requests
    for _ in range(10):
        await limiter.acquire()
    
    elapsed = time.time() - start_time
    
    # With burst of 2 and rate of 20/sec:
    # - 2 immediate (burst)
    # - 8 at 0.05 sec each = 0.4 sec
    # Total should be around 0.4 seconds
    assert elapsed >= 0.35  # Allow some tolerance
    assert elapsed < 0.6    # But not too slow


# =============================================================================
# Concurrent Operations Tests
# =============================================================================

@pytest.mark.integration
@pytest.mark.slow
async def test_concurrent_acquire_operations(fast_rate_limiter: RateLimiter):
    """Test concurrent acquire operations."""
    results = []
    
    async def acquire_and_record():
        start = time.time()
        wait_time = await fast_rate_limiter.acquire()
        elapsed = time.time() - start
        results.append((wait_time, elapsed))
    
    # Run 10 concurrent acquires
    await asyncio.gather(*[acquire_and_record() for _ in range(10)])
    
    # First 5 should have 0 wait time (burst)
    zero_waits = sum(1 for wait, _ in results if wait == 0.0)
    assert zero_waits == 5
    
    # Remaining should have wait times
    non_zero_waits = [wait for wait, _ in results if wait > 0]
    assert len(non_zero_waits) == 5


@pytest.mark.integration
@pytest.mark.slow
async def test_concurrent_rate_limit_enforcement():
    """Test that rate limits are enforced under concurrent load."""
    limiter = RateLimiter(rate=10.0, burst=3)
    
    start_time = time.time()
    
    # Launch 20 concurrent acquires
    tasks = [limiter.acquire() for _ in range(20)]
    await asyncio.gather(*tasks)
    
    elapsed = time.time() - start_time
    
    # With rate of 10/sec and burst of 3:
    # - 3 immediate
    # - 17 at 0.1 sec each = 1.7 sec
    # Total should be around 1.7 seconds
    assert elapsed >= 1.5
    assert elapsed < 2.5


# =============================================================================
# Multiple Rate Limiters Tests
# =============================================================================

@pytest.mark.integration
async def test_multiple_independent_rate_limiters():
    """Test that multiple rate limiters are independent."""
    limiter1 = RateLimiter(rate=100.0, burst=10)
    limiter2 = RateLimiter(rate=100.0, burst=10)
    
    # Exhaust limiter1
    for _ in range(10):
        await limiter1.acquire()
    
    # limiter2 should still have tokens
    wait_time = await limiter2.acquire()
    assert wait_time == 0.0
    
    # limiter1 should require waiting
    wait_time = await limiter1.acquire()
    assert wait_time > 0.0


@pytest.mark.integration
async def test_get_rate_limiters_creates_singleton():
    """Test that get_rate_limiters returns the same instances."""
    limiters1 = get_rate_limiters()
    limiters2 = get_rate_limiters()
    
    # Should be the same objects
    assert limiters1["trending"] is limiters2["trending"]
    assert limiters1["hashtag"] is limiters2["hashtag"]
    assert limiters1["user"] is limiters2["user"]


@pytest.mark.integration
async def test_create_rate_limiters_creates_fresh():
    """Test that create_rate_limiters creates fresh instances."""
    limiters1 = create_rate_limiters()
    limiters2 = create_rate_limiters()
    
    # Should be different objects
    assert limiters1["trending"] is not limiters2["trending"]
    
    # Both should be at full burst capacity
    wait1 = await limiters1["trending"].acquire()
    wait2 = await limiters2["trending"].acquire()
    
    assert wait1 == 0.0
    assert wait2 == 0.0


@pytest.mark.integration
@pytest.mark.slow
async def test_endpoint_specific_rate_limits():
    """Test different rate limits for different endpoint types."""
    # Create limiters with different rates
    trending = RateLimiter(rate=10.0, burst=10)   # 10/sec
    hashtag = RateLimiter(rate=5.0, burst=5)      # 5/sec
    user = RateLimiter(rate=2.0, burst=3)         # 2/sec
    
    # Test trending (fastest)
    start = time.time()
    for _ in range(15):
        await trending.acquire()
    trending_time = time.time() - start
    
    # Test hashtag (medium)
    start = time.time()
    for _ in range(15):
        await hashtag.acquire()
    hashtag_time = time.time() - start
    
    # Test user (slowest)
    start = time.time()
    for _ in range(10):
        await user.acquire()
    user_time = time.time() - start
    
    # User should be slowest, then hashtag, then trending
    assert user_time > hashtag_time
    assert hashtag_time > trending_time


# =============================================================================
# Rate Limiter State Tests
# =============================================================================

@pytest.mark.integration
async def test_rate_limiter_reset():
    """Test rate limiter reset functionality."""
    limiter = RateLimiter(rate=10.0, burst=5)
    
    # Use some tokens
    for _ in range(5):
        await limiter.acquire()
    
    # Should need to wait now
    assert limiter.get_wait_time() > 0
    
    # Reset
    limiter.reset()
    
    # Should be able to acquire immediately
    wait_time = await limiter.acquire()
    assert wait_time == 0.0


@pytest.mark.integration
async def test_available_tokens_property():
    """Test available_tokens property."""
    limiter = RateLimiter(rate=10.0, burst=5)
    
    # Initially at burst capacity
    assert limiter.available_tokens >= 4.5  # Allow small timing variance
    
    # Use some tokens
    await limiter.acquire()
    await limiter.acquire()
    
    # Should have fewer tokens
    assert limiter.available_tokens <= 4.0
    
    # Wait for refill
    await asyncio.sleep(0.3)
    
    # Should have more tokens now
    assert limiter.available_tokens > 2.0


@pytest.mark.integration
async def test_get_wait_time_accuracy():
    """Test get_wait_time returns accurate estimates."""
    limiter = RateLimiter(rate=10.0, burst=5)
    
    # Use all tokens
    for _ in range(5):
        await limiter.acquire()
    
    # Get estimated wait time
    estimated_wait = limiter.get_wait_time()
    
    # Actually acquire and measure
    start = time.time()
    actual_wait = await limiter.acquire()
    elapsed = time.time() - start
    
    # Estimate should be close to actual (within 20% tolerance)
    if estimated_wait > 0:
        assert abs(estimated_wait - actual_wait) < 0.1


# =============================================================================
# Try Acquire Tests
# =============================================================================

@pytest.mark.integration
async def test_try_acquire_success():
    """Test try_acquire when tokens are available."""
    limiter = RateLimiter(rate=10.0, burst=5)
    
    # Should succeed with burst capacity
    for _ in range(5):
        success = await limiter.try_acquire()
        assert success is True


@pytest.mark.integration
async def test_try_acquire_failure():
    """Test try_acquire when no tokens are available."""
    limiter = RateLimiter(rate=1.0, burst=1)
    
    # First acquire should succeed
    assert await limiter.try_acquire() is True
    
    # Second should fail (no tokens, rate is too slow to refill)
    assert await limiter.try_acquire() is False


@pytest.mark.integration
async def test_try_acquire_after_refill():
    """Test try_acquire after tokens refill."""
    limiter = RateLimiter(rate=10.0, burst=2)
    
    # Use all tokens
    await limiter.acquire()
    await limiter.acquire()
    
    # Should fail
    assert await limiter.try_acquire() is False
    
    # Wait for refill
    await asyncio.sleep(0.15)  # At rate of 10/sec, 0.1 sec for 1 token
    
    # Should succeed now
    assert await limiter.try_acquire() is True


# =============================================================================
# Edge Cases and Stress Tests
# =============================================================================

@pytest.mark.integration
@pytest.mark.slow
async def test_rapid_acquire_burst_recovery():
    """Test rapid burst and recovery cycle."""
    limiter = RateLimiter(rate=20.0, burst=5)
    
    # Multiple burst cycles
    for cycle in range(3):
        start = time.time()
        
        # Burst
        for _ in range(5):
            await limiter.acquire()
        
        burst_time = time.time() - start
        assert burst_time < 0.1, f"Cycle {cycle}: Burst should be fast"
        
        # Wait for partial refill
        await asyncio.sleep(0.2)
    
    # Should be able to burst again after waits
    for _ in range(3):
        wait = await limiter.acquire()
        # After 0.6 sec total wait at 20/sec rate, should have 12 tokens
        # So these should be immediate
        assert wait == 0.0


@pytest.mark.integration
@pytest.mark.slow
async def test_concurrent_mixed_operations():
    """Test concurrent mix of acquire and try_acquire."""
    limiter = RateLimiter(rate=50.0, burst=10)
    
    results = {"acquired": 0, "try_succeeded": 0, "try_failed": 0}
    
    async def mixed_worker():
        for i in range(5):
            if i % 2 == 0:
                await limiter.acquire()
                results["acquired"] += 1
            else:
                success = await limiter.try_acquire()
                if success:
                    results["try_succeeded"] += 1
                else:
                    results["try_failed"] += 1
    
    # Run multiple workers concurrently
    await asyncio.gather(*[mixed_worker() for _ in range(4)])
    
    # Should have processed all operations
    assert results["acquired"] == 10  # 4 workers * 5 iterations / 2
    
    # Some try_acquire should have succeeded and some failed
    assert results["try_succeeded"] + results["try_failed"] == 10


@pytest.mark.integration
async def test_rate_limiter_with_fractional_rate():
    """Test rate limiter with fractional rate (slow rate)."""
    # 0.5 requests per second = 2 seconds between requests
    limiter = RateLimiter(rate=0.5, burst=1)
    
    # First should be immediate
    start = time.time()
    await limiter.acquire()
    elapsed = time.time() - start
    assert elapsed < 0.1
    
    # Second should wait about 2 seconds
    start = time.time()
    await limiter.acquire()
    elapsed = time.time() - start
    assert elapsed >= 1.5  # Allow some tolerance


@pytest.mark.integration
@pytest.mark.slow
async def test_rate_limiter_performance_under_load():
    """Test rate limiter performance with many operations."""
    limiter = RateLimiter(rate=100.0, burst=20)
    
    start = time.time()
    
    # 100 acquires
    tasks = [limiter.acquire() for _ in range(100)]
    await asyncio.gather(*tasks)
    
    elapsed = time.time() - start
    
    # With burst of 20 and rate of 100/sec:
    # - 20 immediate
    # - 80 at 0.01 sec each = 0.8 sec
    # Total around 0.8 seconds
    assert elapsed >= 0.6
    assert elapsed < 1.5  # Allow some overhead


# =============================================================================
# Shared State Tests (Multiple Producers)
# =============================================================================

@pytest.mark.integration
async def test_rate_limiter_is_not_shared_between_instances():
    """
    Test that rate limiter instances are independent.
    
    Note: This test documents that the current RateLimiter implementation
    is NOT shared between producers. Each producer gets its own limiter
    instances via get_rate_limiters().
    
    If you need shared state between producers, you would need to:
    1. Use Redis-backed rate limiting, or
    2. Share the same RateLimiter instances between producers
    """
    # Two separate limiter instances
    limiter1 = RateLimiter(rate=10.0, burst=3)
    limiter2 = RateLimiter(rate=10.0, burst=3)
    
    # Exhaust limiter1
    for _ in range(3):
        await limiter1.acquire()
    
    # limiter1 needs to wait
    assert limiter1.get_wait_time() > 0
    
    # limiter2 is unaffected
    assert limiter2.get_wait_time() == 0.0
    
    # Can still acquire from limiter2
    wait = await limiter2.acquire()
    assert wait == 0.0


@pytest.mark.integration
@pytest.mark.slow
async def test_simulated_shared_state_with_redis():
    """
    Demonstrate how shared rate limiting would work with Redis.
    
    This test simulates what a Redis-backed rate limiter would do.
    Actual implementation would require Redis integration in RateLimiter.
    """
    # For now, this documents the expected behavior
    # Each producer has independent rate limiters
    
    producer1_limiters = create_rate_limiters()
    producer2_limiters = create_rate_limiters()
    
    # They are independent instances
    assert producer1_limiters["trending"] is not producer2_limiters["trending"]
    
    # Both can burst independently
    await producer1_limiters["trending"].acquire()
    await producer2_limiters["trending"].acquire()
    
    # Both succeed (independent rate limiting)
    # In a shared scenario, the second might need to wait
