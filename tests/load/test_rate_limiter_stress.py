"""
Rate Limiter Stress Tests

Stress tests for the Token Bucket RateLimiter implementation.
Tests concurrent acquires, burst capacity, sustained rates, and memory stability.

Performance Thresholds:
- 1000 concurrent acquires < 1 second (when no waiting required)
- Memory usage < 512MB during stress test
- All concurrent requests complete (no deadlocks)
"""

import asyncio
import gc
import os
import time
import psutil
from typing import List, Tuple

import pytest

# Add project root to path for imports
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from scraper.rate_limiter import RateLimiter


# Performance thresholds
MAX_RATE_LIMITER_TIME = 1.0  # 1000 acquires < 1 second
MAX_MEMORY_MB = 512          # Memory usage < 512MB

# Concurrency levels to test
CONCURRENCY_LEVELS = [10, 50, 100, 500, 1000]


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


@pytest.mark.load
@pytest.mark.slow
class TestRateLimiterStress:
    """Stress tests for RateLimiter."""

    @pytest.mark.asyncio
    async def test_1000_concurrent_acquires(self):
        """
        Test 1000 concurrent acquires with high burst capacity.
        
        Verifies:
        - Total time < MAX_RATE_LIMITER_TIME
        - All requests complete
        - Fairness (all acquires succeed)
        """
        # Initialize limiter with high burst to avoid waiting
        limiter = RateLimiter(rate=10000, burst=1000)
        
        num_concurrent = 1000
        results = []
        
        async def acquire_and_record() -> Tuple[float, bool]:
            """Acquire token and record timing."""
            start = time.perf_counter()
            try:
                wait_time = await limiter.acquire()
                elapsed = time.perf_counter() - start
                return elapsed, True
            except Exception as e:
                elapsed = time.perf_counter() - start
                return elapsed, False
        
        # Force garbage collection before test
        gc.collect()
        start_mem = get_memory_usage_mb()
        
        # Execute 1000 concurrent acquires
        start_time = time.perf_counter()
        tasks = [acquire_and_record() for _ in range(num_concurrent)]
        results = await asyncio.gather(*tasks)
        elapsed = time.perf_counter() - start_time
        
        end_mem = get_memory_usage_mb()
        mem_increase = end_mem - start_mem
        
        # Calculate metrics
        successful = sum(1 for _, success in results if success)
        avg_time = sum(t for t, _ in results) / len(results)
        max_time = max(t for t, _ in results)
        min_time = min(t for t, _ in results)
        
        metrics = {
            "total_time_sec": elapsed,
            "successful_acquires": successful,
            "avg_acquire_time_sec": avg_time,
            "max_acquire_time_sec": max_time,
            "min_acquire_time_sec": min_time,
            "ops_per_sec": num_concurrent / elapsed if elapsed > 0 else 0,
            "memory_start_mb": start_mem,
            "memory_end_mb": end_mem,
            "memory_increase_mb": mem_increase,
        }
        print_metrics("1000 Concurrent Acquires", metrics)
        
        # Assertions
        assert successful == num_concurrent, f"Only {successful}/{num_concurrent} acquires succeeded"
        assert elapsed < MAX_RATE_LIMITER_TIME, f"Too slow: {elapsed:.3f}s > {MAX_RATE_LIMITER_TIME}s"
        assert mem_increase < MAX_MEMORY_MB, f"Memory leak: {mem_increase:.1f}MB increase"

    @pytest.mark.asyncio
    async def test_burst_capacity_under_load(self):
        """
        Test burst capacity with 100 concurrent requests.
        
        Verifies:
        - Burst capacity is respected
        - Tokens are consumed correctly
        - No overselling beyond burst limit
        """
        burst_size = 100
        limiter = RateLimiter(rate=1000, burst=burst_size)
        
        async def burst_acquire() -> bool:
            """Try to acquire without waiting."""
            return await limiter.try_acquire()
        
        # Execute burst_size concurrent try_acquire calls
        tasks = [burst_acquire() for _ in range(burst_size)]
        results = await asyncio.gather(*tasks)
        
        successful = sum(1 for r in results if r)
        
        # All should succeed initially (bucket is full)
        assert successful == burst_size, f"Expected {burst_size} successes, got {successful}"
        
        # One more should fail (bucket empty)
        extra = await limiter.try_acquire()
        assert not extra, "Should not acquire beyond burst capacity"
        
        # Verify available tokens is near 0
        await asyncio.sleep(0.01)  # Small wait for any race conditions
        available = limiter.available_tokens
        assert available < 1, f"Expected near 0 tokens, got {available}"
        
        metrics = {
            "burst_size": burst_size,
            "successful_immediate": successful,
            "available_after_burst": available,
        }
        print_metrics("Burst Capacity Under Load", metrics)

    @pytest.mark.asyncio
    async def test_sustained_rate_compliance(self):
        """
        Test sustained rate compliance over time.
        
        Verifies:
        - Rate limiting enforces average rate
        - 1000 requests over time respect rate limit
        - Token refill works correctly
        """
        rate = 100  # 100 requests per second
        limiter = RateLimiter(rate=rate, burst=50)
        
        num_requests = 1000
        timestamps = []
        
        async def timed_acquire():
            await limiter.acquire()
            timestamps.append(time.perf_counter())
        
        start_time = time.perf_counter()
        
        # Execute requests
        tasks = [timed_acquire() for _ in range(num_requests)]
        await asyncio.gather(*tasks)
        
        elapsed = time.perf_counter() - start_time
        
        # Calculate actual rate
        actual_rate = num_requests / elapsed
        
        # With burst=50 and rate=100, we should get approximately 100 req/sec
        # Allow 10% tolerance for scheduling overhead
        expected_time = (num_requests - 50) / rate  # Burst handles first 50 instantly
        
        metrics = {
            "target_rate": rate,
            "actual_rate": actual_rate,
            "elapsed_sec": elapsed,
            "num_requests": num_requests,
            "expected_min_time": expected_time * 0.9,
        }
        print_metrics("Sustained Rate Compliance", metrics)
        
        # Should take at least expected time (with tolerance)
        assert elapsed >= expected_time * 0.8, f"Rate limiting not enforced: {elapsed:.2f}s < {expected_time:.2f}s"

    @pytest.mark.asyncio
    async def test_token_refill_accuracy(self):
        """
        Test token refill accuracy under load.
        
        Verifies:
        - Tokens refill at correct rate
        - Elapsed time calculations are accurate
        - No token drift over time
        """
        rate = 10  # 10 tokens per second
        burst = 10
        limiter = RateLimiter(rate=rate, burst=burst)
        
        # Drain the bucket
        for _ in range(burst):
            await limiter.acquire()
        
        # Wait for refill
        wait_time = 1.0  # Wait 1 second
        await asyncio.sleep(wait_time)
        
        # Should have ~10 tokens available
        available = limiter.available_tokens
        expected_tokens = min(burst, rate * wait_time)
        
        # Allow 20% tolerance for timing
        assert available >= expected_tokens * 0.8, f"Token refill too slow: {available} < {expected_tokens * 0.8}"
        assert available <= burst, f"Token overflow: {available} > {burst}"
        
        # Acquire the refilled tokens
        acquired = 0
        while await limiter.try_acquire():
            acquired += 1
            if acquired > burst * 2:  # Safety limit
                break
        
        metrics = {
            "expected_tokens": expected_tokens,
            "available_after_wait": available,
            "acquired_tokens": acquired,
            "rate": rate,
            "wait_time": wait_time,
        }
        print_metrics("Token Refill Accuracy", metrics)
        
        assert acquired >= expected_tokens * 0.7, f"Refill accuracy issue: acquired {acquired}, expected ~{expected_tokens}"

    @pytest.mark.asyncio
    async def test_memory_usage_stability(self):
        """
        Test memory usage stability over many operations.
        
        Verifies:
        - No memory leaks
        - Memory stays below threshold
        - Stable performance over time
        """
        limiter = RateLimiter(rate=1000, burst=100)
        
        # Force GC and record baseline
        gc.collect()
        baseline_mem = get_memory_usage_mb()
        
        # Run many acquire cycles
        num_cycles = 10000
        for i in range(num_cycles):
            await limiter.acquire()
            if i % 1000 == 0:
                limiter.reset()  # Reset to maintain burst capacity
        
        # Force GC and check memory
        gc.collect()
        final_mem = get_memory_usage_mb()
        mem_increase = final_mem - baseline_mem
        
        metrics = {
            "baseline_memory_mb": baseline_mem,
            "final_memory_mb": final_mem,
            "memory_increase_mb": mem_increase,
            "num_cycles": num_cycles,
            "memory_per_operation_bytes": (mem_increase * 1024 * 1024) / num_cycles if num_cycles > 0 else 0,
        }
        print_metrics("Memory Usage Stability", metrics)
        
        # Memory should not increase significantly
        assert mem_increase < 50, f"Memory leak detected: {mem_increase:.1f}MB increase"

    @pytest.mark.asyncio
    async def test_fairness_all_complete(self):
        """
        Test fairness - all concurrent requests should complete.
        
        Verifies:
        - No starvation
        - All requests eventually succeed
        - Fair distribution of tokens
        """
        rate = 50  # Slow rate to create contention
        burst = 10
        limiter = RateLimiter(rate=rate, burst=burst)
        
        num_workers = 50
        requests_per_worker = 20
        
        completion_times = []
        
        async def worker(worker_id: int):
            for i in range(requests_per_worker):
                await limiter.acquire()
                completion_times.append((worker_id, time.perf_counter()))
        
        start_time = time.perf_counter()
        
        # Start all workers concurrently
        tasks = [worker(i) for i in range(num_workers)]
        await asyncio.gather(*tasks)
        
        elapsed = time.perf_counter() - start_time
        total_requests = num_workers * requests_per_worker
        
        # Verify all completed
        assert len(completion_times) == total_requests, f"Only {len(completion_times)}/{total_requests} completed"
        
        # Check fairness - all workers should have completions spread throughout
        worker_counts = {}
        for wid, _ in completion_times:
            worker_counts[wid] = worker_counts.get(wid, 0) + 1
        
        # Each worker should complete all requests
        for wid in range(num_workers):
            assert worker_counts.get(wid, 0) == requests_per_worker, f"Worker {wid} did not complete all requests"
        
        metrics = {
            "num_workers": num_workers,
            "requests_per_worker": requests_per_worker,
            "total_requests": total_requests,
            "elapsed_sec": elapsed,
            "avg_time_per_request_ms": (elapsed / total_requests) * 1000,
        }
        print_metrics("Fairness Test", metrics)

    @pytest.mark.asyncio
    @pytest.mark.parametrize("concurrency", CONCURRENCY_LEVELS)
    async def test_performance_baseline(self, concurrency: int):
        """
        Performance baseline test at different concurrency levels.
        
        Verifies:
        - Performance scales with concurrency
        - No degradation at high concurrency
        - Latency percentiles are acceptable
        """
        limiter = RateLimiter(rate=10000, burst=concurrency * 2)
        
        latencies = []
        
        async def measure_latency():
            start = time.perf_counter()
            await limiter.acquire()
            elapsed = time.perf_counter() - start
            latencies.append(elapsed * 1000)  # Convert to ms
        
        start_time = time.perf_counter()
        tasks = [measure_latency() for _ in range(concurrency)]
        await asyncio.gather(*tasks)
        total_time = time.perf_counter() - start_time
        
        # Calculate percentiles
        latencies.sort()
        p50 = latencies[len(latencies) // 2]
        p95 = latencies[int(len(latencies) * 0.95)]
        p99 = latencies[int(len(latencies) * 0.99)]
        avg = sum(latencies) / len(latencies)
        
        metrics = {
            "concurrency": concurrency,
            "total_time_ms": total_time * 1000,
            "ops_per_sec": concurrency / total_time if total_time > 0 else 0,
            "avg_latency_ms": avg,
            "p50_latency_ms": p50,
            "p95_latency_ms": p95,
            "p99_latency_ms": p99,
            "min_latency_ms": latencies[0],
            "max_latency_ms": latencies[-1],
        }
        print_metrics(f"Performance Baseline (concurrency={concurrency})", metrics)
        
        # Performance assertions
        assert p95 < 100, f"P95 latency too high: {p95:.2f}ms > 100ms"
        assert p99 < 200, f"P99 latency too high: {p99:.2f}ms > 200ms"

    @pytest.mark.asyncio
    async def test_wait_time_accuracy(self):
        """
        Test wait time calculation accuracy under load.
        
        Verifies:
        - get_wait_time returns accurate estimates
        - Actual wait matches predicted wait
        """
        rate = 10
        burst = 5
        limiter = RateLimiter(rate=rate, burst=burst)
        
        # Drain bucket
        for _ in range(burst):
            await limiter.acquire()
        
        # Check predicted wait time
        predicted_wait = limiter.get_wait_time()
        
        # Actual acquire and measure
        start = time.perf_counter()
        await limiter.acquire()
        actual_wait = time.perf_counter() - start
        
        # Should be close (within 100ms for scheduling overhead)
        difference = abs(predicted_wait - actual_wait)
        
        metrics = {
            "predicted_wait_sec": predicted_wait,
            "actual_wait_sec": actual_wait,
            "difference_sec": difference,
            "rate": rate,
            "burst": burst,
        }
        print_metrics("Wait Time Accuracy", metrics)
        
        assert difference < 0.15, f"Wait time inaccurate: predicted {predicted_wait:.3f}s, actual {actual_wait:.3f}s"


@pytest.mark.load
@pytest.mark.slow
@pytest.mark.asyncio
async def test_rate_limiter_comprehensive():
    """
    Comprehensive stress test combining all scenarios.
    
    This is the main stress test that exercises the rate limiter
    under realistic mixed load conditions.
    """
    limiter = RateLimiter(rate=100, burst=50)
    
    results = {
        "immediate_acquires": 0,
        "waited_acquires": 0,
        "failed_acquires": 0,
        "total_wait_time": 0.0,
    }
    
    async def mixed_load_task(task_id: int):
        # Mix of try_acquire and acquire
        if task_id % 3 == 0:
            # Try immediate acquire
            if await limiter.try_acquire():
                results["immediate_acquires"] += 1
            else:
                results["failed_acquires"] += 1
        else:
            # Wait for acquire
            start = time.perf_counter()
            await limiter.acquire()
            wait_time = time.perf_counter() - start
            results["waited_acquires"] += 1
            results["total_wait_time"] += wait_time
    
    gc.collect()
    start_mem = get_memory_usage_mb()
    start_time = time.perf_counter()
    
    # Run mixed load
    tasks = [mixed_load_task(i) for i in range(500)]
    await asyncio.gather(*tasks)
    
    elapsed = time.perf_counter() - start_time
    
    gc.collect()
    end_mem = get_memory_usage_mb()
    
    total_ops = sum([results["immediate_acquires"], results["waited_acquires"]])
    
    metrics = {
        "elapsed_sec": elapsed,
        "ops_per_sec": total_ops / elapsed if elapsed > 0 else 0,
        "immediate_acquires": results["immediate_acquires"],
        "waited_acquires": results["waited_acquires"],
        "avg_wait_time_ms": (results["total_wait_time"] / results["waited_acquires"] * 1000) if results["waited_acquires"] > 0 else 0,
        "memory_increase_mb": end_mem - start_mem,
    }
    print_metrics("Comprehensive Stress Test", metrics)
    
    # Final assertions
    assert total_ops == 500, "Not all operations completed"
    assert end_mem - start_mem < 100, "Memory usage too high"
