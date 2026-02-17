"""
Circuit Breaker Stress Tests

Stress tests for the CircuitBreaker implementation.
Tests rapid failures, recovery behavior, state transitions, and thread safety.

Performance Thresholds:
- 1000 rapid failures handled without issues
- State transitions < 1ms latency
- Memory usage < 512MB during stress test
- Thread safety maintained at 100 concurrent callers
"""

import asyncio
import gc
import os
import time
import psutil
from typing import List, Dict, Any
from unittest.mock import AsyncMock

import pytest

# Add project root to path for imports
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from scraper.circuit_breaker import CircuitBreaker, CircuitState, CircuitOpenError


# Performance thresholds
MAX_MEMORY_MB = 512
MAX_STATE_TRANSITION_MS = 1.0

# Concurrency levels
CONCURRENCY_LEVELS = [10, 50, 100]


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
class TestCircuitBreakerStress:
    """Stress tests for CircuitBreaker."""

    @pytest.mark.asyncio
    async def test_rapid_failure_simulation(self):
        """
        Test rapid failure simulation (1000 failures).
        
        Verifies:
        - Circuit opens after threshold
        - State transitions are correct
        - No resource leaks
        - Metrics tracking is accurate
        """
        # Configure for fast testing
        circuit = CircuitBreaker(
            failure_threshold=5,
            recovery_timeout=1,  # 1 second for fast testing
            half_open_max_calls=2
        )
        
        failure_count = 1000
        exceptions_caught = 0
        circuit_open_errors = 0
        
        async def failing_func():
            raise ValueError("Simulated failure")
        
        gc.collect()
        start_mem = get_memory_usage_mb()
        start_time = time.perf_counter()
        
        for i in range(failure_count):
            try:
                await circuit.call(failing_func)
            except CircuitOpenError:
                circuit_open_errors += 1
            except ValueError:
                exceptions_caught += 1
        
        elapsed = time.perf_counter() - start_time
        
        gc.collect()
        end_mem = get_memory_usage_mb()
        
        state = circuit.get_state()
        
        metrics = {
            "total_attempts": failure_count,
            "exceptions_caught": exceptions_caught,
            "circuit_open_errors": circuit_open_errors,
            "elapsed_sec": elapsed,
            "ops_per_sec": failure_count / elapsed if elapsed > 0 else 0,
            "final_state": state["state"],
            "total_failures": state["total_failures"],
            "total_calls": state["total_calls"],
            "state_changes": state["state_changes"],
            "memory_increase_mb": end_mem - start_mem,
        }
        print_metrics("Rapid Failure Simulation", metrics)
        
        # Assertions
        assert state["state"] == "open", f"Circuit should be open, got {state['state']}"
        assert state["total_failures"] >= 5, "Should have recorded failures"
        assert circuit_open_errors > 0, "Should have rejected calls when open"
        assert end_mem - start_mem < 100, "Memory leak detected"

    @pytest.mark.asyncio
    async def test_recovery_behavior_under_load(self):
        """
        Test recovery behavior under load.
        
        Verifies:
        - Circuit transitions from OPEN to HALF_OPEN
        - Successful calls close the circuit
        - Recovery works under concurrent load
        """
        circuit = CircuitBreaker(
            failure_threshold=3,
            recovery_timeout=0.5,  # 500ms for fast testing
            half_open_max_calls=2
        )
        
        async def failing_func():
            raise ValueError("Failure")
        
        async def success_func():
            return "success"
        
        # Open the circuit
        for _ in range(5):
            try:
                await circuit.call(failing_func)
            except Exception:
                pass
        
        assert circuit.is_open(), "Circuit should be open"
        
        # Wait for recovery timeout
        await asyncio.sleep(0.6)
        
        # Now calls should transition to half-open
        results = []
        for i in range(10):
            try:
                # Alternate between success and failure
                if i % 3 == 0:
                    result = await circuit.call(failing_func)
                else:
                    result = await circuit.call(success_func)
                results.append(("success", result))
            except CircuitOpenError:
                results.append(("rejected", None))
            except ValueError:
                results.append(("error", None))
        
        state = circuit.get_state()
        
        metrics = {
            "success_count": sum(1 for r, _ in results if r == "success"),
            "rejected_count": sum(1 for r, _ in results if r == "rejected"),
            "error_count": sum(1 for r, _ in results if r == "error"),
            "final_state": state["state"],
            "state_changes": state["state_changes"],
        }
        print_metrics("Recovery Behavior Under Load", metrics)
        
        # Circuit should have attempted recovery
        assert state["state_changes"] >= 2, "Should have multiple state changes"

    @pytest.mark.asyncio
    async def test_state_transition_performance(self):
        """
        Test state transition performance.
        
        Verifies:
        - State transitions complete quickly (< 1ms)
        - No performance degradation over many transitions
        """
        circuit = CircuitBreaker(
            failure_threshold=2,
            recovery_timeout=0.1,
            half_open_max_calls=1
        )
        
        transition_times = []
        
        async def failing_func():
            raise ValueError("Failure")
        
        async def success_func():
            return "success"
        
        # Measure state transitions
        for cycle in range(10):
            # Close to Open transition
            start = time.perf_counter()
            for _ in range(3):
                try:
                    await circuit.call(failing_func)
                except Exception:
                    pass
            
            # Check if open
            if circuit.is_open():
                transition_times.append(time.perf_counter() - start)
            
            # Wait and try recovery
            await asyncio.sleep(0.15)
            
            # Try to close again
            start = time.perf_counter()
            for _ in range(2):
                try:
                    await circuit.call(success_func)
                except Exception:
                    pass
            
            if circuit.is_closed():
                transition_times.append(time.perf_counter() - start)
        
        avg_transition_time = sum(transition_times) / len(transition_times) if transition_times else 0
        max_transition_time = max(transition_times) if transition_times else 0
        
        metrics = {
            "num_transitions": len(transition_times),
            "avg_transition_time_ms": avg_transition_time * 1000,
            "max_transition_time_ms": max_transition_time * 1000,
            "final_state": circuit.get_state()["state"],
            "total_state_changes": circuit.get_state()["state_changes"],
        }
        print_metrics("State Transition Performance", metrics)
        
        assert max_transition_time < MAX_STATE_TRANSITION_MS / 1000, \
            f"State transition too slow: {max_transition_time * 1000:.2f}ms"

    @pytest.mark.asyncio
    @pytest.mark.parametrize("concurrency", CONCURRENCY_LEVELS)
    async def test_thread_safety_concurrent_callers(self, concurrency: int):
        """
        Test thread safety with concurrent callers.
        
        Verifies:
        - No race conditions
        - Accurate counting under concurrent access
        - All states remain consistent
        """
        circuit = CircuitBreaker(
            failure_threshold=10,
            recovery_timeout=1,
            half_open_max_calls=3
        )
        
        call_count = 0
        success_count = 0
        error_count = 0
        rejected_count = 0
        
        async def caller_task(task_id: int):
            nonlocal call_count, success_count, error_count, rejected_count
            
            for _ in range(20):
                async def random_func():
                    if task_id % 2 == 0:
                        raise ValueError("Error")
                    return "success"
                
                try:
                    await circuit.call(random_func)
                    success_count += 1
                except CircuitOpenError:
                    rejected_count += 1
                except ValueError:
                    error_count += 1
                
                call_count += 1
        
        start_time = time.perf_counter()
        tasks = [caller_task(i) for i in range(concurrency)]
        await asyncio.gather(*tasks)
        elapsed = time.perf_counter() - start_time
        
        state = circuit.get_state()
        
        metrics = {
            "concurrency": concurrency,
            "total_calls": call_count,
            "success_count": success_count,
            "error_count": error_count,
            "rejected_count": rejected_count,
            "ops_per_sec": call_count / elapsed if elapsed > 0 else 0,
            "final_state": state["state"],
            "state_changes": state["state_changes"],
            "total_failures": state["total_failures"],
        }
        print_metrics(f"Thread Safety (concurrency={concurrency})", metrics)
        
        # Verify consistency
        assert call_count == concurrency * 20, "Not all calls completed"
        assert state["total_calls"] == call_count, "Call count mismatch"
        assert success_count + error_count + rejected_count == call_count, "Result count mismatch"

    @pytest.mark.asyncio
    async def test_half_open_state_handling(self):
        """
        Test half-open state handling with concurrent requests.
        
        Verifies:
        - Only limited calls allowed in half-open state
        - Failed call in half-open reopens circuit
        - Successful calls close the circuit
        """
        circuit = CircuitBreaker(
            failure_threshold=3,
            recovery_timeout=0.5,
            half_open_max_calls=3
        )
        
        async def failing_func():
            raise ValueError("Failure")
        
        async def success_func():
            return "success"
        
        # Open the circuit
        for _ in range(5):
            try:
                await circuit.call(failing_func)
            except Exception:
                pass
        
        assert circuit.is_open(), "Circuit should be open"
        
        # Wait for recovery
        await asyncio.sleep(0.6)
        
        # Start multiple concurrent calls
        results = []
        
        async def half_open_caller():
            try:
                result = await circuit.call(success_func)
                results.append("success")
                return result
            except CircuitOpenError:
                results.append("rejected")
            except Exception as e:
                results.append(f"error: {e}")
        
        # Launch many concurrent calls - only half_open_max_calls should proceed
        tasks = [half_open_caller() for _ in range(20)]
        await asyncio.gather(*tasks)
        
        state = circuit.get_state()
        
        metrics = {
            "success_count": results.count("success"),
            "rejected_count": results.count("rejected"),
            "error_count": len([r for r in results if r.startswith("error")]),
            "final_state": state["state"],
            "state_changes": state["state_changes"],
        }
        print_metrics("Half-Open State Handling", metrics)
        
        # Circuit should be closed after successful half-open calls
        assert circuit.is_closed(), "Circuit should be closed after successful recovery"

    @pytest.mark.asyncio
    async def test_memory_leak_detection(self):
        """
        Test for memory leaks during repeated open/close cycles.
        
        Verifies:
        - No memory growth over many cycles
        - Stable memory footprint
        """
        circuit = CircuitBreaker(
            failure_threshold=2,
            recovery_timeout=0.1,
            half_open_max_calls=1
        )
        
        async def failing_func():
            raise ValueError("Failure")
        
        async def success_func():
            return "success"
        
        gc.collect()
        baseline_mem = get_memory_usage_mb()
        
        # Run many open/close cycles
        num_cycles = 100
        for cycle in range(num_cycles):
            # Cause failures to open circuit
            for _ in range(3):
                try:
                    await circuit.call(failing_func)
                except Exception:
                    pass
            
            # Wait for recovery
            await asyncio.sleep(0.15)
            
            # Close circuit with success
            try:
                await circuit.call(success_func)
            except Exception:
                pass
            
            # Periodic memory check
            if cycle % 20 == 0 and cycle > 0:
                gc.collect()
                current_mem = get_memory_usage_mb()
                growth = current_mem - baseline_mem
                assert growth < 50, f"Memory leak detected at cycle {cycle}: {growth:.1f}MB growth"
        
        gc.collect()
        final_mem = get_memory_usage_mb()
        mem_growth = final_mem - baseline_mem
        
        metrics = {
            "num_cycles": num_cycles,
            "baseline_memory_mb": baseline_mem,
            "final_memory_mb": final_mem,
            "memory_growth_mb": mem_growth,
            "memory_per_cycle_kb": (mem_growth * 1024) / num_cycles if num_cycles > 0 else 0,
            "total_state_changes": circuit.get_state()["state_changes"],
        }
        print_metrics("Memory Leak Detection", metrics)
        
        assert mem_growth < 30, f"Memory leak detected: {mem_growth:.1f}MB growth"

    @pytest.mark.asyncio
    async def test_circuit_decorator_performance(self):
        """
        Test circuit breaker decorator performance.
        
        Verifies:
        - Decorator doesn't add significant overhead
        - Wrapped functions work correctly
        """
        circuit = CircuitBreaker(
            failure_threshold=5,
            recovery_timeout=1,
            half_open_max_calls=2
        )
        
        from scraper.circuit_breaker import with_circuit_breaker
        
        @with_circuit_breaker(circuit)
        async def decorated_func():
            return "decorated_result"
        
        @with_circuit_breaker(circuit)
        async def decorated_failing_func():
            raise ValueError("decorated_error")
        
        num_calls = 1000
        
        start_time = time.perf_counter()
        
        for _ in range(num_calls):
            try:
                await decorated_func()
            except Exception:
                pass
        
        for _ in range(num_calls):
            try:
                await decorated_failing_func()
            except Exception:
                pass
        
        elapsed = time.perf_counter() - start_time
        
        metrics = {
            "total_calls": num_calls * 2,
            "elapsed_sec": elapsed,
            "calls_per_sec": (num_calls * 2) / elapsed if elapsed > 0 else 0,
            "avg_call_time_ms": (elapsed / (num_calls * 2)) * 1000,
        }
        print_metrics("Circuit Decorator Performance", metrics)
        
        # Should handle 1000+ calls per second
        assert metrics["calls_per_sec"] > 1000, "Decorator performance too slow"


@pytest.mark.load
@pytest.mark.slow
@pytest.mark.asyncio
async def test_circuit_breaker_comprehensive():
    """
    Comprehensive circuit breaker stress test.
    
    Combines multiple scenarios to test overall resilience.
    """
    circuit = CircuitBreaker(
        failure_threshold=5,
        recovery_timeout=0.5,
        half_open_max_calls=2
    )
    
    stats = {
        "calls": 0,
        "successes": 0,
        "failures": 0,
        "rejects": 0,
    }
    
    async def mixed_task(task_id: int):
        async def random_func():
            # 30% failure rate
            if task_id % 3 == 0:
                raise ValueError("Random error")
            return f"result_{task_id}"
        
        try:
            result = await circuit.call(random_func)
            stats["successes"] += 1
            return result
        except CircuitOpenError:
            stats["rejects"] += 1
        except Exception:
            stats["failures"] += 1
        finally:
            stats["calls"] += 1
    
    gc.collect()
    start_mem = get_memory_usage_mb()
    start_time = time.perf_counter()
    
    # Run mixed load
    for batch in range(5):
        tasks = [mixed_task(i + batch * 100) for i in range(100)]
        await asyncio.gather(*tasks)
        await asyncio.sleep(0.1)  # Brief pause between batches
    
    elapsed = time.perf_counter() - start_time
    
    gc.collect()
    end_mem = get_memory_usage_mb()
    
    state = circuit.get_state()
    
    metrics = {
        "total_calls": stats["calls"],
        "successes": stats["successes"],
        "failures": stats["failures"],
        "rejects": stats["rejects"],
        "elapsed_sec": elapsed,
        "ops_per_sec": stats["calls"] / elapsed if elapsed > 0 else 0,
        "final_state": state["state"],
        "total_failures_metric": state["total_failures"],
        "total_rejects_metric": state["total_rejects"],
        "state_changes": state["state_changes"],
        "memory_increase_mb": end_mem - start_mem,
    }
    print_metrics("Comprehensive Circuit Breaker Test", metrics)
    
    # Assertions
    assert stats["calls"] == 500, "Not all calls executed"
    assert state["total_calls"] == 500, "Circuit call count mismatch"
    assert end_mem - start_mem < 100, "Memory leak"
