"""
Unit tests for the CircuitBreaker class.

Tests state transitions, failure counting, recovery logic,
and thread safety for the circuit breaker implementation.
"""

import asyncio
import pytest
import time
from unittest.mock import AsyncMock

from scraper.circuit_breaker import (
    CircuitBreaker,
    CircuitState,
    CircuitOpenError,
    with_circuit_breaker,
    get_circuit_breaker,
)


class TestCircuitBreakerInitialization:
    """Test CircuitBreaker initialization."""

    def test_initial_state_is_closed(self):
        """Initial state should be CLOSED."""
        cb = CircuitBreaker()
        assert cb.state == CircuitState.CLOSED

    def test_initial_failure_count_is_zero(self):
        """Initial failure count should be 0."""
        cb = CircuitBreaker()
        assert cb.failure_count == 0

    def test_initial_success_count_is_zero(self):
        """Initial success count should be 0."""
        cb = CircuitBreaker()
        assert cb.success_count == 0

    def test_initial_last_failure_time_is_none(self):
        """Initial last_failure_time should be None."""
        cb = CircuitBreaker()
        assert cb.last_failure_time is None

    def test_custom_threshold_values(self):
        """Circuit breaker should accept custom threshold values."""
        cb = CircuitBreaker(failure_threshold=3, recovery_timeout=10, half_open_max_calls=2)
        assert cb.failure_threshold == 3
        assert cb.recovery_timeout == 10
        assert cb.half_open_max_calls == 2

    def test_metrics_initialized_to_zero(self):
        """Metrics should be initialized to zero."""
        cb = CircuitBreaker()
        assert cb.total_calls == 0
        assert cb.total_failures == 0
        assert cb.total_rejects == 0
        assert cb.state_changes == 0


class TestCircuitBreakerSuccessCalls:
    """Test successful calls behavior."""

    @pytest.mark.asyncio
    async def test_success_call_returns_result(self):
        """Successful call should return function result."""
        cb = CircuitBreaker()
        
        async def success_func():
            return "success"
        
        result = await cb.call(success_func)
        
        assert result == "success"

    @pytest.mark.asyncio
    async def test_success_does_not_change_state(self):
        """Success calls should not change circuit state."""
        cb = CircuitBreaker()
        
        async def success_func():
            return "success"
        
        await cb.call(success_func)
        
        assert cb.state == CircuitState.CLOSED

    @pytest.mark.asyncio
    async def test_success_resets_failure_count(self):
        """Success should reset failure count to 0."""
        cb = CircuitBreaker()
        cb.failure_count = 2  # Simulate some failures
        
        async def success_func():
            return "success"
        
        await cb.call(success_func)
        
        assert cb.failure_count == 0

    @pytest.mark.asyncio
    async def test_success_increments_total_calls(self):
        """Success should increment total_calls metric."""
        cb = CircuitBreaker()
        
        async def success_func():
            return "success"
        
        await cb.call(success_func)
        
        assert cb.total_calls == 1

    @pytest.mark.asyncio
    async def test_success_with_args_and_kwargs(self):
        """Success call should pass args and kwargs to function."""
        cb = CircuitBreaker()
        
        async def func_with_args(a, b, c=None):
            return (a, b, c)
        
        result = await cb.call(func_with_args, 1, 2, c=3)
        
        assert result == (1, 2, 3)


class TestCircuitBreakerFailureCounting:
    """Test failure counting behavior."""

    @pytest.mark.asyncio
    async def test_failure_increments_count(self):
        """Failure should increment failure_count."""
        cb = CircuitBreaker()
        
        async def fail_func():
            raise ValueError("error")
        
        with pytest.raises(ValueError):
            await cb.call(fail_func)
        
        assert cb.failure_count == 1

    @pytest.mark.asyncio
    async def test_multiple_failures_increment_count(self):
        """Multiple failures should increment failure_count."""
        cb = CircuitBreaker()
        
        async def fail_func():
            raise ValueError("error")
        
        for _ in range(3):
            with pytest.raises(ValueError):
                await cb.call(fail_func)
        
        assert cb.failure_count == 3

    @pytest.mark.asyncio
    async def test_failure_records_last_failure_time(self):
        """Failure should record last_failure_time."""
        cb = CircuitBreaker()
        
        async def fail_func():
            raise ValueError("error")
        
        before = time.time()
        with pytest.raises(ValueError):
            await cb.call(fail_func)
        after = time.time()
        
        assert before <= cb.last_failure_time <= after

    @pytest.mark.asyncio
    async def test_failure_increments_total_failures(self):
        """Failure should increment total_failures metric."""
        cb = CircuitBreaker()
        
        async def fail_func():
            raise ValueError("error")
        
        with pytest.raises(ValueError):
            await cb.call(fail_func)
        
        assert cb.total_failures == 1


class TestCircuitBreakerOpenState:
    """Test OPEN state behavior."""

    @pytest.mark.asyncio
    async def test_circuit_opens_after_failure_threshold(self):
        """Circuit should open after failure_threshold failures."""
        cb = CircuitBreaker(failure_threshold=3)
        
        async def fail_func():
            raise ValueError("error")
        
        # Trigger 3 failures
        for _ in range(3):
            with pytest.raises(ValueError):
                await cb.call(fail_func)
        
        assert cb.state == CircuitState.OPEN
        assert cb.state_changes >= 1

    @pytest.mark.asyncio
    async def test_open_circuit_raises_circuit_open_error(self):
        """Open circuit should raise CircuitOpenError on call."""
        cb = CircuitBreaker()
        cb.state = CircuitState.OPEN
        cb.last_failure_time = time.time()
        
        async def any_func():
            return "result"
        
        with pytest.raises(CircuitOpenError):
            await cb.call(any_func)

    @pytest.mark.asyncio
    async def test_open_circuit_increments_total_rejects(self):
        """Open circuit should increment total_rejects metric."""
        cb = CircuitBreaker()
        cb.state = CircuitState.OPEN
        cb.last_failure_time = time.time()
        
        async def any_func():
            return "result"
        
        with pytest.raises(CircuitOpenError):
            await cb.call(any_func)
        
        assert cb.total_rejects == 1

    @pytest.mark.asyncio
    async def test_circuit_open_error_message(self):
        """CircuitOpenError should have descriptive message."""
        cb = CircuitBreaker(recovery_timeout=300)
        cb.state = CircuitState.OPEN
        cb.last_failure_time = time.time()
        
        async def any_func():
            return "result"
        
        with pytest.raises(CircuitOpenError) as exc_info:
            await cb.call(any_func)
        
        assert "OPEN" in str(exc_info.value)
        assert "retry" in str(exc_info.value).lower()


class TestCircuitBreakerRecovery:
    """Test recovery and HALF_OPEN state."""

    @pytest.mark.asyncio
    async def test_recovery_timeout_transitions_to_half_open(self):
        """After recovery_timeout, circuit should transition to HALF_OPEN."""
        cb = CircuitBreaker(recovery_timeout=0.1)
        cb.state = CircuitState.OPEN
        cb.last_failure_time = time.time()
        
        # Wait for recovery timeout
        await asyncio.sleep(0.15)
        
        # Trigger state check by calling
        async def any_func():
            return "result"
        
        result = await cb.call(any_func)
        
        assert cb.state == CircuitState.HALF_OPEN
        assert result == "result"

    @pytest.mark.asyncio
    async def test_half_open_success_counting(self):
        """Success in HALF_OPEN should increment success_count."""
        cb = CircuitBreaker(half_open_max_calls=3)
        cb.state = CircuitState.HALF_OPEN
        
        async def success_func():
            return "success"
        
        await cb.call(success_func)
        
        assert cb.success_count == 1

    @pytest.mark.asyncio
    async def test_half_open_closes_after_max_successes(self):
        """Circuit should close after half_open_max_calls successes."""
        cb = CircuitBreaker(half_open_max_calls=2)
        cb.state = CircuitState.HALF_OPEN
        
        async def success_func():
            return "success"
        
        await cb.call(success_func)
        await cb.call(success_func)
        
        assert cb.state == CircuitState.CLOSED
        assert cb.success_count == 0  # Reset after closing

    @pytest.mark.asyncio
    async def test_half_open_reopens_on_failure(self):
        """Failure in HALF_OPEN should reopen circuit."""
        cb = CircuitBreaker()
        cb.state = CircuitState.HALF_OPEN
        cb.success_count = 1
        
        async def fail_func():
            raise ValueError("error")
        
        with pytest.raises(ValueError):
            await cb.call(fail_func)
        
        assert cb.state == CircuitState.OPEN
        assert cb.success_count == 0


class TestCircuitBreakerStateHelpers:
    """Test state helper methods."""

    def test_is_closed_returns_true_when_closed(self):
        """is_closed should return True when state is CLOSED."""
        cb = CircuitBreaker()
        cb.state = CircuitState.CLOSED
        assert cb.is_closed() is True

    def test_is_closed_returns_false_when_open(self):
        """is_closed should return False when state is OPEN."""
        cb = CircuitBreaker()
        cb.state = CircuitState.OPEN
        assert cb.is_closed() is False

    def test_is_open_returns_true_when_open(self):
        """is_open should return True when state is OPEN."""
        cb = CircuitBreaker()
        cb.state = CircuitState.OPEN
        assert cb.is_open() is True

    def test_is_open_returns_false_when_closed(self):
        """is_open should return False when state is CLOSED."""
        cb = CircuitBreaker()
        cb.state = CircuitState.CLOSED
        assert cb.is_open() is False

    def test_is_half_open_returns_true_when_half_open(self):
        """is_half_open should return True when state is HALF_OPEN."""
        cb = CircuitBreaker()
        cb.state = CircuitState.HALF_OPEN
        assert cb.is_half_open() is True

    def test_is_half_open_returns_false_when_closed(self):
        """is_half_open should return False when state is CLOSED."""
        cb = CircuitBreaker()
        cb.state = CircuitState.CLOSED
        assert cb.is_half_open() is False


class TestCircuitBreakerGetState:
    """Test get_state() method."""

    def test_get_state_returns_dict(self):
        """get_state should return dictionary."""
        cb = CircuitBreaker()
        state = cb.get_state()
        
        assert isinstance(state, dict)

    def test_get_state_contains_required_fields(self):
        """get_state should contain all required fields."""
        cb = CircuitBreaker()
        state = cb.get_state()
        
        assert "state" in state
        assert "failure_count" in state
        assert "success_count" in state
        assert "last_failure_time" in state
        assert "seconds_until_retry" in state
        assert "total_calls" in state
        assert "total_failures" in state
        assert "total_rejects" in state
        assert "state_changes" in state

    def test_get_state_state_is_string(self):
        """State value should be string representation."""
        cb = CircuitBreaker()
        state = cb.get_state()
        
        assert isinstance(state["state"], str)
        assert state["state"] == "closed"

    def test_seconds_until_retry_zero_when_closed(self):
        """seconds_until_retry should be 0 when circuit is closed."""
        cb = CircuitBreaker()
        state = cb.get_state()
        
        assert state["seconds_until_retry"] == 0

    def test_seconds_until_retry_when_open(self):
        """seconds_until_retry should be calculated when open."""
        cb = CircuitBreaker(recovery_timeout=300)
        cb.state = CircuitState.OPEN
        cb.last_failure_time = time.time()
        
        state = cb.get_state()
        
        assert state["seconds_until_retry"] > 0
        assert state["seconds_until_retry"] <= 300


class TestCircuitBreakerReset:
    """Test reset() method."""

    def test_reset_sets_state_to_closed(self):
        """reset should set state to CLOSED."""
        cb = CircuitBreaker()
        cb.state = CircuitState.OPEN
        
        cb.reset()
        
        assert cb.state == CircuitState.CLOSED

    def test_reset_clears_failure_count(self):
        """reset should clear failure_count."""
        cb = CircuitBreaker()
        cb.failure_count = 5
        
        cb.reset()
        
        assert cb.failure_count == 0

    def test_reset_clears_success_count(self):
        """reset should clear success_count."""
        cb = CircuitBreaker()
        cb.success_count = 2
        
        cb.reset()
        
        assert cb.success_count == 0

    def test_reset_clears_last_failure_time(self):
        """reset should clear last_failure_time."""
        cb = CircuitBreaker()
        cb.last_failure_time = time.time()
        
        cb.reset()
        
        assert cb.last_failure_time is None


class TestCircuitBreakerConcurrency:
    """Test concurrent access safety."""

    @pytest.mark.asyncio
    async def test_concurrent_calls_are_safe(self):
        """Multiple concurrent calls should be thread-safe."""
        cb = CircuitBreaker()
        
        async def success_func():
            await asyncio.sleep(0.01)
            return "success"
        
        # Launch concurrent calls
        tasks = [cb.call(success_func) for _ in range(10)]
        results = await asyncio.gather(*tasks)
        
        assert all(r == "success" for r in results)
        assert cb.total_calls == 10

    @pytest.mark.asyncio
    async def test_concurrent_failures_count_correctly(self):
        """Concurrent failures should be counted correctly."""
        cb = CircuitBreaker(failure_threshold=10)
        
        async def fail_func():
            raise ValueError("error")
        
        # Launch concurrent failures
        tasks = [cb.call(fail_func) for _ in range(5)]
        
        for task in tasks:
            with pytest.raises(ValueError):
                await task
        
        assert cb.failure_count == 5

    @pytest.mark.asyncio
    async def test_concurrent_mixed_results(self):
        """Concurrent mixed success/failure should handle correctly."""
        cb = CircuitBreaker()
        counter = 0
        
        async def mixed_func():
            nonlocal counter
            counter += 1
            if counter % 2 == 0:
                return "success"
            raise ValueError("error")
        
        tasks = [cb.call(mixed_func) for _ in range(6)]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        successes = sum(1 for r in results if r == "success")
        failures = sum(1 for r in results if isinstance(r, ValueError))
        
        assert successes == 3
        assert failures == 3


class TestCircuitBreakerDecorator:
    """Test with_circuit_breaker decorator."""

    @pytest.mark.asyncio
    async def test_decorator_wraps_function(self):
        """Decorator should wrap async function with circuit breaker."""
        cb = CircuitBreaker()
        
        @with_circuit_breaker(cb)
        async def protected_func():
            return "protected"
        
        result = await protected_func()
        
        assert result == "protected"
        assert cb.total_calls == 1

    @pytest.mark.asyncio
    async def test_decorator_preserves_function_args(self):
        """Decorator should preserve function arguments."""
        cb = CircuitBreaker()
        
        @with_circuit_breaker(cb)
        async def func_with_args(a, b, c=None):
            return (a, b, c)
        
        result = await func_with_args(1, 2, c=3)
        
        assert result == (1, 2, 3)

    @pytest.mark.asyncio
    async def test_decorator_propagates_exceptions(self):
        """Decorator should propagate exceptions from wrapped function."""
        cb = CircuitBreaker()
        
        @with_circuit_breaker(cb)
        async def failing_func():
            raise ValueError("decorated error")
        
        with pytest.raises(ValueError, match="decorated error"):
            await failing_func()

    @pytest.mark.asyncio
    async def test_decorator_raises_circuit_open_error(self):
        """Decorator should raise CircuitOpenError when circuit is open."""
        cb = CircuitBreaker()
        cb.state = CircuitState.OPEN
        cb.last_failure_time = time.time()
        
        @with_circuit_breaker(cb)
        async def any_func():
            return "result"
        
        with pytest.raises(CircuitOpenError):
            await any_func()


class TestCircuitBreakerFactory:
    """Test factory function."""

    def test_get_circuit_breaker_returns_instance(self):
        """get_circuit_breaker should return CircuitBreaker instance."""
        cb = get_circuit_breaker()
        
        assert isinstance(cb, CircuitBreaker)

    def test_get_circuit_breaker_caches_instance(self):
        """get_circuit_breaker should return same instance."""
        cb1 = get_circuit_breaker()
        cb2 = get_circuit_breaker()
        
        assert cb1 is cb2


class TestCircuitBreakerEdgeCases:
    """Test edge cases and boundary conditions."""

    @pytest.mark.asyncio
    async def test_exactly_at_failure_threshold(self):
        """Circuit should open exactly at failure_threshold."""
        cb = CircuitBreaker(failure_threshold=3)
        
        async def fail_func():
            raise ValueError("error")
        
        # First 2 failures - circuit still closed
        for _ in range(2):
            with pytest.raises(ValueError):
                await cb.call(fail_func)
        
        assert cb.state == CircuitState.CLOSED
        
        # 3rd failure - circuit opens
        with pytest.raises(ValueError):
            await cb.call(fail_func)
        
        assert cb.state == CircuitState.OPEN

    @pytest.mark.asyncio
    async def test_exactly_at_half_open_max(self):
        """Circuit should close exactly at half_open_max_calls."""
        cb = CircuitBreaker(half_open_max_calls=2)
        cb.state = CircuitState.HALF_OPEN
        
        async def success_func():
            return "success"
        
        # First success - still half open
        await cb.call(success_func)
        assert cb.state == CircuitState.HALF_OPEN
        assert cb.success_count == 1
        
        # Second success - closes
        await cb.call(success_func)
        assert cb.state == CircuitState.CLOSED
        assert cb.success_count == 0

    @pytest.mark.asyncio
    async def test_failure_after_recovery_timeout_expired(self):
        """Failure after recovery timeout should transition to half-open first."""
        cb = CircuitBreaker(recovery_timeout=0.1)
        cb.state = CircuitState.OPEN
        cb.last_failure_time = time.time() - 0.2  # Past timeout
        
        async def fail_func():
            raise ValueError("error")
        
        # Will go to half-open then fail
        with pytest.raises(ValueError):
            await cb.call(fail_func)
        
        assert cb.state == CircuitState.OPEN  # Reopens on failure

    def test_circuit_open_error_default_message(self):
        """CircuitOpenError should have default message."""
        error = CircuitOpenError()
        
        assert "OPEN" in error.message
        assert "TikTok API" in error.message

    def test_circuit_open_error_custom_message(self):
        """CircuitOpenError should accept custom message."""
        error = CircuitOpenError("Custom error message")
        
        assert error.message == "Custom error message"
        assert str(error) == "Custom error message"

    def test_circuit_state_enum_values(self):
        """CircuitState enum should have correct values."""
        assert CircuitState.CLOSED.value == "closed"
        assert CircuitState.OPEN.value == "open"
        assert CircuitState.HALF_OPEN.value == "half_open"

    @pytest.mark.asyncio
    async def test_zero_recovery_timeout(self):
        """Zero recovery timeout should allow immediate recovery attempt."""
        cb = CircuitBreaker(recovery_timeout=0)
        cb.state = CircuitState.OPEN
        cb.last_failure_time = time.time()
        
        async def success_func():
            return "success"
        
        result = await cb.call(success_func)
        
        assert cb.state == CircuitState.HALF_OPEN
        assert result == "success"
