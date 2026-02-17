"""
Circuit Breaker Pattern Implementation

Prevents cascading failures during TikTok outages or sustained blocks.
Implements the classic circuit breaker pattern with three states:
- CLOSED: Normal operation, requests pass through
- OPEN: Failing, reject all requests
- HALF_OPEN: Testing if recovered

Configuration (from config.py):
- failure_threshold: 5 consecutive failures before opening
- recovery_timeout: 300 seconds (5 minutes) before attempting recovery
- half_open_max_calls: 3 successful calls needed to close from half-open
"""

import asyncio
import time
from enum import Enum
from dataclasses import dataclass, field
from typing import Callable, Any, Optional, Awaitable
import logging
from functools import wraps

from .config import settings

logger = logging.getLogger(__name__)


class CircuitState(Enum):
    """Circuit breaker states."""

    CLOSED = "closed"        # Normal operation
    OPEN = "open"            # Failing, reject requests
    HALF_OPEN = "half_open"  # Testing if recovered


class CircuitOpenError(Exception):
    """Raised when circuit breaker is open and rejecting requests."""

    def __init__(self, message: str = "Circuit breaker is OPEN - TikTok API unavailable"):
        self.message = message
        super().__init__(self.message)


@dataclass
class CircuitBreaker:
    """Circuit breaker for protecting external API calls.

    The circuit breaker pattern prevents cascading failures by:
    1. Monitoring failure rates
    2. Opening the circuit after threshold failures
    3. Allowing recovery after a timeout period
    4. Testing recovery with limited requests in half-open state

    Attributes:
        failure_threshold: Number of failures before opening circuit
        recovery_timeout: Seconds before attempting recovery
        half_open_max_calls: Successful calls needed to close from half-open
        failure_count: Current consecutive failure count
        success_count: Current consecutive success count (in half-open)
        last_failure_time: Timestamp of last failure
        state: Current circuit state
        lock: Async lock for thread-safe state changes

    Example:
        circuit = CircuitBreaker(failure_threshold=5, recovery_timeout=300)

        async def safe_request():
            return await circuit.call(make_tiktok_request)
    """

    failure_threshold: int = field(default_factory=lambda: settings.circuit_failure_threshold)
    recovery_timeout: int = field(default_factory=lambda: settings.circuit_recovery_timeout)
    half_open_max_calls: int = field(default_factory=lambda: settings.circuit_half_open_max_calls)
    failure_count: int = field(default=0, init=False)
    success_count: int = field(default=0, init=False)
    last_failure_time: Optional[float] = field(default=None, init=False)
    state: CircuitState = field(default=CircuitState.CLOSED, init=False)
    lock: asyncio.Lock = field(default_factory=asyncio.Lock, init=False)

    # Metrics
    total_calls: int = field(default=0, init=False)
    total_failures: int = field(default=0, init=False)
    total_rejects: int = field(default=0, init=False)
    state_changes: int = field(default=0, init=False)

    async def call(
        self,
        func: Callable[..., Awaitable[Any]],
        *args,
        **kwargs
    ) -> Any:
        """Execute async function with circuit breaker protection.

        Args:
            func: Async function to execute
            *args: Positional arguments for func
            **kwargs: Keyword arguments for func

        Returns:
            Result of func(*args, **kwargs)

        Raises:
            CircuitOpenError: If circuit is open
            Exception: Any exception from func (after updating state)
        """
        async with self.lock:
            self.total_calls += 1
            await self._check_state_transition()

            if self.state == CircuitState.OPEN:
                self.total_rejects += 1
                logger.warning(
                    "circuit_breaker_rejected",
                    extra={
                        "state": self.state.value,
                        "failure_count": self.failure_count,
                        "seconds_until_retry": self._seconds_until_retry(),
                    }
                )
                raise CircuitOpenError(
                    f"Circuit breaker is OPEN - retry in {self._seconds_until_retry():.0f} seconds"
                )

        # Execute outside lock
        try:
            result = await func(*args, **kwargs)
            await self._on_success()
            return result
        except Exception as e:
            await self._on_failure()
            raise

    async def _check_state_transition(self) -> None:
        """Check and update circuit state based on time.

        Called internally before each request.
        """
        if self.state == CircuitState.OPEN:
            if self.last_failure_time is not None:
                elapsed = time.time() - self.last_failure_time
                if elapsed >= self.recovery_timeout:
                    old_state = self.state
                    self.state = CircuitState.HALF_OPEN
                    self.success_count = 0
                    self.state_changes += 1
                    logger.info(
                        "circuit_breaker_half_open",
                        extra={
                            "previous_state": old_state.value,
                            "new_state": self.state.value,
                            "recovery_timeout": self.recovery_timeout,
                        }
                    )

    async def _on_success(self) -> None:
        """Handle successful call - reset failure count, possibly close circuit."""
        async with self.lock:
            self.failure_count = 0

            if self.state == CircuitState.HALF_OPEN:
                self.success_count += 1
                if self.success_count >= self.half_open_max_calls:
                    old_state = self.state
                    self.state = CircuitState.CLOSED
                    self.success_count = 0
                    self.state_changes += 1
                    logger.info(
                        "circuit_breaker_recovered",
                        extra={
                            "previous_state": old_state.value,
                            "new_state": self.state.value,
                            "successful_calls": self.success_count,
                        }
                    )

    async def _on_failure(self) -> None:
        """Handle failed call - increment count, possibly open circuit."""
        async with self.lock:
            self.failure_count += 1
            self.total_failures += 1
            self.last_failure_time = time.time()

            if self.state == CircuitState.HALF_OPEN:
                # Failure in half-open immediately opens
                old_state = self.state
                self.state = CircuitState.OPEN
                self.success_count = 0
                self.state_changes += 1
                logger.warning(
                    "circuit_breaker_reopened",
                    extra={
                        "previous_state": old_state.value,
                        "new_state": self.state.value,
                        "failure_count": self.failure_count,
                    }
                )
            elif self.failure_count >= self.failure_threshold:
                old_state = self.state
                self.state = CircuitState.OPEN
                self.state_changes += 1
                logger.error(
                    "circuit_breaker_opened",
                    extra={
                        "previous_state": old_state.value,
                        "new_state": self.state.value,
                        "failure_count": self.failure_count,
                        "threshold": self.failure_threshold,
                    }
                )

    def _seconds_until_retry(self) -> float:
        """Calculate seconds until retry is possible."""
        if self.state != CircuitState.OPEN or self.last_failure_time is None:
            return 0.0
        elapsed = time.time() - self.last_failure_time
        remaining = self.recovery_timeout - elapsed
        return max(0.0, remaining)

    def get_state(self) -> dict:
        """Return current circuit breaker state for health checks.

        Returns:
            Dictionary with state information
        """
        return {
            "state": self.state.value,
            "failure_count": self.failure_count,
            "success_count": self.success_count,
            "last_failure_time": self.last_failure_time,
            "seconds_until_retry": self._seconds_until_retry() if self.state == CircuitState.OPEN else 0,
            "total_calls": self.total_calls,
            "total_failures": self.total_failures,
            "total_rejects": self.total_rejects,
            "state_changes": self.state_changes,
        }

    def is_closed(self) -> bool:
        """Check if circuit is closed (normal operation)."""
        return self.state == CircuitState.CLOSED

    def is_open(self) -> bool:
        """Check if circuit is open (rejecting requests)."""
        return self.state == CircuitState.OPEN

    def is_half_open(self) -> bool:
        """Check if circuit is half-open (testing recovery)."""
        return self.state == CircuitState.HALF_OPEN

    def reset(self) -> None:
        """Reset circuit breaker to initial state."""
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.success_count = 0
        self.last_failure_time = None
        logger.info("circuit_breaker_reset")


def with_circuit_breaker(circuit: CircuitBreaker):
    """Decorator to wrap async functions with circuit breaker protection.

    Args:
        circuit: CircuitBreaker instance to use

    Example:
        circuit = CircuitBreaker()

        @with_circuit_breaker(circuit)
        async def fetch_trending():
            ...
    """
    def decorator(func: Callable[..., Awaitable[Any]]) -> Callable[..., Awaitable[Any]]:
        @wraps(func)
        async def wrapper(*args, **kwargs) -> Any:
            return await circuit.call(func, *args, **kwargs)
        return wrapper
    return decorator


# Global circuit breaker instance (lazy initialization)
_circuit_breaker: Optional[CircuitBreaker] = None


def get_circuit_breaker() -> CircuitBreaker:
    """Get or create global circuit breaker instance.

    Returns:
        CircuitBreaker instance
    """
    global _circuit_breaker
    if _circuit_breaker is None:
        _circuit_breaker = CircuitBreaker()
    return _circuit_breaker
