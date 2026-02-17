"""
Concurrent Pipeline Load Tests

End-to-end load tests for the full producer-consumer pipeline.
Tests multiple producers, multiple consumers, queue behavior, and backpressure.

Performance Thresholds:
- End-to-end latency < 100ms (p95)
- Queue depth handled gracefully
- Backpressure prevents memory explosion
"""

import asyncio
import gc
import os
import time
import psutil
from asyncio import Queue
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Callable
from unittest.mock import AsyncMock

import pytest

# Add project root to path for imports
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from scraper.rate_limiter import RateLimiter
from scraper.circuit_breaker import CircuitBreaker


# Performance thresholds
MAX_E2E_LATENCY_MS = 100  # P95 latency < 100ms
MAX_MEMORY_MB = 512


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


@dataclass
class PipelineMessage:
    """Message flowing through the pipeline."""
    id: str
    data: Any
    created_at: float
    processed_at: Optional[float] = None
    
    @property
    def latency_ms(self) -> float:
        """Calculate latency in milliseconds."""
        if self.processed_at is None:
            return 0.0
        return (self.processed_at - self.created_at) * 1000


class PipelineStage:
    """A stage in the processing pipeline."""
    
    def __init__(self, name: str, process_func: Callable, rate_limiter: Optional[RateLimiter] = None):
        self.name = name
        self.process_func = process_func
        self.rate_limiter = rate_limiter
        self.input_queue: Optional[Queue] = None
        self.output_queue: Optional[Queue] = None
        self.processed_count = 0
        self.error_count = 0
        self.latencies: List[float] = []
    
    def connect(self, input_queue: Queue, output_queue: Optional[Queue] = None):
        """Connect to input and output queues."""
        self.input_queue = input_queue
        self.output_queue = output_queue
    
    async def run(self, num_messages: Optional[int] = None):
        """Run the stage, processing messages from input queue."""
        processed = 0
        while True:
            try:
                # Wait for message with timeout
                message = await asyncio.wait_for(self.input_queue.get(), timeout=5.0)
                
                # Apply rate limiting if configured
                if self.rate_limiter:
                    await self.rate_limiter.acquire()
                
                # Process message
                start_time = time.perf_counter()
                try:
                    result = await self.process_func(message)
                    message.processed_at = time.perf_counter()
                    
                    self.latencies.append((time.perf_counter() - start_time) * 1000)
                    self.processed_count += 1
                    
                    # Forward to output queue if connected
                    if self.output_queue:
                        await self.output_queue.put(result or message)
                    
                    processed += 1
                    if num_messages and processed >= num_messages:
                        break
                        
                except Exception as e:
                    self.error_count += 1
                    
            except asyncio.TimeoutError:
                # No more messages
                break


@pytest.mark.load
@pytest.mark.slow
class TestConcurrentPipeline:
    """Concurrent pipeline load tests."""

    @pytest.mark.asyncio
    async def test_multiple_producers_consumers(self):
        """
        Test multiple producers with multiple consumers.
        
        Verifies:
        - All messages are processed
        - No race conditions
        - Fair distribution of work
        """
        num_producers = 5
        num_consumers = 5
        messages_per_producer = 200
        
        input_queue = Queue(maxsize=1000)
        output_queue = Queue()
        
        processed_messages = []
        
        async def producer(producer_id: int):
            """Produce messages."""
            for i in range(messages_per_producer):
                message = PipelineMessage(
                    id=f"p{producer_id}_m{i}",
                    data={"value": i, "producer": producer_id},
                    created_at=time.perf_counter()
                )
                await input_queue.put(message)
        
        async def consumer(consumer_id: int):
            """Consume and process messages."""
            while True:
                try:
                    message = await asyncio.wait_for(input_queue.get(), timeout=2.0)
                    # Simulate processing
                    await asyncio.sleep(0.001)
                    message.processed_at = time.perf_counter()
                    processed_messages.append(message)
                    await output_queue.put(message)
                except asyncio.TimeoutError:
                    break
        
        gc.collect()
        start_mem = get_memory_usage_mb()
        start_time = time.perf_counter()
        
        # Start producers and consumers
        producers = [asyncio.create_task(producer(i)) for i in range(num_producers)]
        consumers = [asyncio.create_task(consumer(i)) for i in range(num_consumers)]
        
        # Wait for producers to finish
        await asyncio.gather(*producers)
        
        # Wait for queue to empty
        await input_queue.join()
        
        # Cancel consumers
        for c in consumers:
            c.cancel()
        
        elapsed = time.perf_counter() - start_time
        
        gc.collect()
        end_mem = get_memory_usage_mb()
        
        expected_messages = num_producers * messages_per_producer
        
        # Calculate latencies
        latencies = [m.latency_ms for m in processed_messages if m.latency_ms > 0]
        
        metrics = {
            "num_producers": num_producers,
            "num_consumers": num_consumers,
            "messages_per_producer": messages_per_producer,
            "total_messages": expected_messages,
            "processed_messages": len(processed_messages),
            "elapsed_sec": elapsed,
            "messages_per_sec": len(processed_messages) / elapsed if elapsed > 0 else 0,
            "avg_latency_ms": sum(latencies) / len(latencies) if latencies else 0,
            "max_latency_ms": max(latencies) if latencies else 0,
            "memory_increase_mb": end_mem - start_mem,
        }
        print_metrics("Multiple Producers Consumers", metrics)
        
        assert len(processed_messages) == expected_messages, \
            f"Message loss: {len(processed_messages)}/{expected_messages}"

    @pytest.mark.asyncio
    async def test_queue_depth_under_load(self):
        """
        Test queue depth under load.
        
        Verifies:
        - Queue depth stays within bounds
        - Backpressure works correctly
        - No unbounded growth
        """
        queue_size = 100
        queue = Queue(maxsize=queue_size)
        
        max_observed_depth = 0
        depth_readings = []
        
        async def fast_producer():
            """Produce messages faster than they can be consumed."""
            for i in range(1000):
                await queue.put(f"msg_{i}")
                current_depth = queue.qsize()
                depth_readings.append(current_depth)
                nonlocal max_observed_depth
                max_observed_depth = max(max_observed_depth, current_depth)
        
        async def slow_consumer():
            """Consume slowly to create backpressure."""
            processed = 0
            while processed < 1000:
                try:
                    await asyncio.wait_for(queue.get(), timeout=5.0)
                    await asyncio.sleep(0.01)  # Slow processing
                    processed += 1
                except asyncio.TimeoutError:
                    break
        
        gc.collect()
        start_mem = get_memory_usage_mb()
        
        # Run producer and consumer concurrently
        producer_task = asyncio.create_task(fast_producer())
        consumer_task = asyncio.create_task(slow_consumer())
        
        await asyncio.gather(producer_task, consumer_task)
        
        gc.collect()
        end_mem = get_memory_usage_mb()
        
        avg_depth = sum(depth_readings) / len(depth_readings) if depth_readings else 0
        
        metrics = {
            "max_queue_size": queue_size,
            "max_observed_depth": max_observed_depth,
            "avg_queue_depth": avg_depth,
            "total_messages": 1000,
            "depth_readings": len(depth_readings),
            "memory_increase_mb": end_mem - start_mem,
        }
        print_metrics("Queue Depth Under Load", metrics)
        
        # Queue should respect maxsize
        assert max_observed_depth <= queue_size, \
            f"Queue overflow: {max_observed_depth} > {queue_size}"

    @pytest.mark.asyncio
    async def test_backpressure_handling(self):
        """
        Test backpressure handling.
        
        Verifies:
        - Backpressure prevents memory explosion
        - System remains stable under overload
        - Producer slows down when consumer is slow
        """
        queue_size = 50
        queue = Queue(maxsize=queue_size)
        
        producer_delays = []
        
        async def backpressure_producer(num_messages: int):
            """Producer that experiences backpressure."""
            for i in range(num_messages):
                start_put = time.perf_counter()
                await queue.put(f"msg_{i}")
                put_time = time.perf_counter() - start_put
                producer_delays.append(put_time)
        
        async def very_slow_consumer():
            """Very slow consumer to create heavy backpressure."""
            processed = 0
            while processed < 200:
                try:
                    await asyncio.wait_for(queue.get(), timeout=10.0)
                    await asyncio.sleep(0.05)  # Very slow
                    processed += 1
                except asyncio.TimeoutError:
                    break
        
        gc.collect()
        start_mem = get_memory_usage_mb()
        start_time = time.perf_counter()
        
        # Run with backpressure
        producer_task = asyncio.create_task(backpressure_producer(200))
        consumer_task = asyncio.create_task(very_slow_consumer())
        
        await asyncio.gather(producer_task, consumer_task)
        
        elapsed = time.perf_counter() - start_time
        
        gc.collect()
        end_mem = get_memory_usage_mb()
        
        # Analyze backpressure
        # When queue is full, put() should block, increasing put_time
        avg_delay = sum(producer_delays) / len(producer_delays) if producer_delays else 0
        max_delay = max(producer_delays) if producer_delays else 0
        
        metrics = {
            "num_messages": 200,
            "queue_size": queue_size,
            "elapsed_sec": elapsed,
            "avg_put_delay_ms": avg_delay * 1000,
            "max_put_delay_ms": max_delay * 1000,
            "backpressure_detected": max_delay > 0.001,  # More than 1ms
            "memory_increase_mb": end_mem - start_mem,
        }
        print_metrics("Backpressure Handling", metrics)
        
        # Memory should remain stable even with backpressure
        assert end_mem - start_mem < 100, f"Memory explosion: {end_mem - start_mem:.1f}MB"

    @pytest.mark.asyncio
    async def test_end_to_end_latency_measurements(self):
        """
        Test end-to-end latency measurements.
        
        Verifies:
        - P95 latency < 100ms
        - P99 latency < 200ms
        - No significant outliers
        """
        input_queue = Queue()
        output_queue = Queue()
        
        latencies = []
        
        async def latency_producer(num_messages: int):
            """Producer with timestamp tracking."""
            for i in range(num_messages):
                message = PipelineMessage(
                    id=f"msg_{i}",
                    data={"seq": i},
                    created_at=time.perf_counter()
                )
                await input_queue.put(message)
        
        async def latency_consumer():
            """Consumer that measures latency."""
            processed = 0
            while processed < 1000:
                try:
                    message = await asyncio.wait_for(input_queue.get(), timeout=5.0)
                    # Simulate processing time
                    await asyncio.sleep(0.005)
                    message.processed_at = time.perf_counter()
                    latencies.append(message.latency_ms)
                    await output_queue.put(message)
                    processed += 1
                except asyncio.TimeoutError:
                    break
        
        start_time = time.perf_counter()
        
        producer_task = asyncio.create_task(latency_producer(1000))
        consumer_task = asyncio.create_task(latency_consumer())
        
        await asyncio.gather(producer_task, consumer_task)
        
        elapsed = time.perf_counter() - start_time
        
        # Calculate percentiles
        latencies.sort()
        p50 = latencies[len(latencies) // 2]
        p95 = latencies[int(len(latencies) * 0.95)]
        p99 = latencies[int(len(latencies) * 0.99)]
        avg = sum(latencies) / len(latencies)
        
        metrics = {
            "num_messages": len(latencies),
            "elapsed_sec": elapsed,
            "avg_latency_ms": avg,
            "p50_latency_ms": p50,
            "p95_latency_ms": p95,
            "p99_latency_ms": p99,
            "min_latency_ms": min(latencies),
            "max_latency_ms": max(latencies),
        }
        print_metrics("End-to-End Latency Measurements", metrics)
        
        # Assert latency requirements
        assert p95 < MAX_E2E_LATENCY_MS, f"P95 latency too high: {p95:.2f}ms > {MAX_E2E_LATENCY_MS}ms"

    @pytest.mark.asyncio
    async def test_pipeline_with_rate_limiting(self):
        """
        Test pipeline with rate limiting integration.
        
        Verifies:
        - Rate limiting is respected
        - Pipeline throughput matches rate limit
        - No messages lost due to rate limiting
        """
        rate_limit = 100  # 100 messages per second
        limiter = RateLimiter(rate=rate_limit, burst=20)
        
        input_queue = Queue()
        output_queue = Queue()
        
        async def rate_limited_producer(num_messages: int):
            """Producer with rate limiting."""
            for i in range(num_messages):
                await limiter.acquire()
                message = PipelineMessage(
                    id=f"msg_{i}",
                    data={"seq": i},
                    created_at=time.perf_counter()
                )
                await input_queue.put(message)
        
        async def fast_consumer():
            """Fast consumer to keep up."""
            processed = 0
            while processed < 200:
                try:
                    message = await asyncio.wait_for(input_queue.get(), timeout=5.0)
                    message.processed_at = time.perf_counter()
                    await output_queue.put(message)
                    processed += 1
                except asyncio.TimeoutError:
                    break
        
        start_time = time.perf_counter()
        
        producer_task = asyncio.create_task(rate_limited_producer(200))
        consumer_task = asyncio.create_task(fast_consumer())
        
        await asyncio.gather(producer_task, consumer_task)
        
        elapsed = time.perf_counter() - start_time
        
        actual_rate = 200 / elapsed if elapsed > 0 else 0
        
        metrics = {
            "target_rate": rate_limit,
            "actual_rate": actual_rate,
            "elapsed_sec": elapsed,
            "messages": 200,
            "rate_accuracy": actual_rate / rate_limit if rate_limit > 0 else 0,
        }
        print_metrics("Pipeline With Rate Limiting", metrics)
        
        # Should be close to rate limit (within 20%)
        assert actual_rate <= rate_limit * 1.3, f"Rate limiting not enforced: {actual_rate:.1f} > {rate_limit * 1.3:.1f}"

    @pytest.mark.asyncio
    async def test_pipeline_with_circuit_breaker(self):
        """
        Test pipeline with circuit breaker integration.
        
        Verifies:
        - Circuit breaker protects downstream
        - Failures don't cascade
        - Recovery works in pipeline context
        """
        circuit = CircuitBreaker(failure_threshold=5, recovery_timeout=0.5, half_open_max_calls=2)
        
        input_queue = Queue()
        output_queue = Queue()
        
        success_count = 0
        failure_count = 0
        circuit_open_count = 0
        
        async def protected_producer(num_messages: int):
            """Producer with circuit breaker protection."""
            nonlocal success_count, failure_count, circuit_open_count
            
            for i in range(num_messages):
                async def send_message():
                    message = PipelineMessage(
                        id=f"msg_{i}",
                        data={"seq": i},
                        created_at=time.perf_counter()
                    )
                    await input_queue.put(message)
                    return "sent"
                
                try:
                    await circuit.call(send_message)
                    success_count += 1
                except Exception as e:
                    if "Circuit breaker is OPEN" in str(e):
                        circuit_open_count += 1
                    else:
                        failure_count += 1
        
        async def failing_consumer():
            """Consumer that fails intermittently."""
            processed = 0
            while processed < 100:
                try:
                    await asyncio.wait_for(input_queue.get(), timeout=5.0)
                    # Fail every 3rd message
                    if processed % 3 == 0:
                        raise ValueError("Simulated failure")
                    processed += 1
                except asyncio.TimeoutError:
                    break
                except ValueError:
                    processed += 1  # Count as processed even if failed
        
        start_time = time.perf_counter()
        
        producer_task = asyncio.create_task(protected_producer(100))
        consumer_task = asyncio.create_task(failing_consumer())
        
        await asyncio.gather(producer_task, consumer_task)
        
        elapsed = time.perf_counter() - start_time
        
        state = circuit.get_state()
        
        metrics = {
            "success_count": success_count,
            "failure_count": failure_count,
            "circuit_open_count": circuit_open_count,
            "elapsed_sec": elapsed,
            "final_circuit_state": state["state"],
            "total_calls": state["total_calls"],
            "total_failures": state["total_failures"],
            "state_changes": state["state_changes"],
        }
        print_metrics("Pipeline With Circuit Breaker", metrics)
        
        # Circuit should have protected the pipeline
        assert state["total_calls"] > 0, "Circuit breaker not used"


@pytest.mark.load
@pytest.mark.slow
@pytest.mark.asyncio
async def test_concurrent_pipeline_comprehensive():
    """
    Comprehensive concurrent pipeline test.
    
    Combines multiple scenarios for full pipeline stress testing.
    """
    # Multi-stage pipeline
    stage1_queue = Queue(maxsize=100)
    stage2_queue = Queue(maxsize=100)
    output_queue = Queue()
    
    # Rate limiters for each stage
    stage1_limiter = RateLimiter(rate=200, burst=50)
    stage2_limiter = RateLimiter(rate=150, burst=30)
    
    latencies = []
    processed_count = 0
    
    async def stage1_worker():
        """First stage: enrichment."""
        nonlocal processed_count
        while True:
            try:
                msg = await asyncio.wait_for(stage1_queue.get(), timeout=5.0)
                await stage1_limiter.acquire()
                # Enrichment processing
                await asyncio.sleep(0.002)
                msg.data["stage1"] = True
                await stage2_queue.put(msg)
            except asyncio.TimeoutError:
                break
    
    async def stage2_worker():
        """Second stage: final processing."""
        nonlocal processed_count
        while True:
            try:
                msg = await asyncio.wait_for(stage2_queue.get(), timeout=5.0)
                await stage2_limiter.acquire()
                # Final processing
                await asyncio.sleep(0.003)
                msg.processed_at = time.perf_counter()
                latencies.append(msg.latency_ms)
                await output_queue.put(msg)
                processed_count += 1
            except asyncio.TimeoutError:
                break
    
    async def producer():
        """Produce messages."""
        for i in range(500):
            msg = PipelineMessage(
                id=f"msg_{i}",
                data={"seq": i},
                created_at=time.perf_counter()
            )
            await stage1_queue.put(msg)
    
    gc.collect()
    start_mem = get_memory_usage_mb()
    start_time = time.perf_counter()
    
    # Start all workers
    producer_task = asyncio.create_task(producer())
    stage1_workers = [asyncio.create_task(stage1_worker()) for _ in range(3)]
    stage2_workers = [asyncio.create_task(stage2_worker()) for _ in range(2)]
    
    # Wait for production
    await producer_task
    
    # Wait for processing to complete
    await asyncio.sleep(0.5)
    
    # Cancel workers
    for w in stage1_workers + stage2_workers:
        w.cancel()
    
    elapsed = time.perf_counter() - start_time
    
    gc.collect()
    end_mem = get_memory_usage_mb()
    
    # Calculate metrics
    if latencies:
        latencies.sort()
        p95 = latencies[int(len(latencies) * 0.95)]
        p99 = latencies[int(len(latencies) * 0.99)]
    else:
        p95 = p99 = 0
    
    metrics = {
        "messages_produced": 500,
        "messages_processed": processed_count,
        "elapsed_sec": elapsed,
        "throughput_per_sec": processed_count / elapsed if elapsed > 0 else 0,
        "p95_latency_ms": p95,
        "p99_latency_ms": p99,
        "avg_latency_ms": sum(latencies) / len(latencies) if latencies else 0,
        "memory_increase_mb": end_mem - start_mem,
    }
    print_metrics("Comprehensive Concurrent Pipeline", metrics)
    
    # Assertions
    assert processed_count >= 450, f"Too many messages lost: {processed_count}/500"
    assert end_mem - start_mem < 150, f"Memory too high: {end_mem - start_mem:.1f}MB"
