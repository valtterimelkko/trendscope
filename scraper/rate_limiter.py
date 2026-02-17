"""
Token Bucket Rate Limiter

Implements smooth rate limiting using the token bucket algorithm.
This prevents sudden bursts that could trigger TikTok's anti-bot systems.

Rate Limits (per SELF_HOSTED.md):
- Trending: 10-20 req/min (0.17-0.33 req/sec)
- Hashtag: 5-10 req/min (0.08-0.17 req/sec)
- User: 2-5 req/min (0.03-0.08 req/sec)
"""

import asyncio
import time
from dataclasses import dataclass, field
from typing import Optional
import logging

from .config import settings

logger = logging.getLogger(__name__)


@dataclass
class RateLimiter:
    """Token bucket rate limiter for API calls.

    The token bucket algorithm allows for burst requests up to the bucket size
    while maintaining an average rate over time. This is ideal for scraping
    where we want to avoid sudden spikes while allowing some flexibility.

    Attributes:
        rate: Tokens added per second (requests/second)
        burst: Maximum tokens in bucket (maximum burst size)
        tokens: Current token count
        last_update: Timestamp of last token update
        lock: Async lock for thread-safe operations

    Example:
        # 10 requests per minute = 0.17 requests per second
        limiter = RateLimiter(rate=0.17, burst=5)
        await limiter.acquire()  # Will wait if necessary
    """

    rate: float  # Requests per second
    burst: int   # Maximum burst size
    tokens: float = field(default=0.0, init=False)
    last_update: float = field(default_factory=time.time, init=False)
    lock: asyncio.Lock = field(default_factory=asyncio.Lock, init=False)

    def __post_init__(self):
        """Initialize tokens to burst capacity."""
        self.tokens = float(self.burst)

    async def acquire(self, tokens: int = 1) -> float:
        """Acquire tokens, waiting if necessary.

        Args:
            tokens: Number of tokens to acquire (default: 1)

        Returns:
            Wait time in seconds (0 if no wait needed)

        Raises:
            ValueError: If requesting more tokens than burst capacity
        """
        if tokens > self.burst:
            raise ValueError(
                f"Cannot acquire {tokens} tokens; burst capacity is {self.burst}"
            )

        async with self.lock:
            now = time.time()
            elapsed = now - self.last_update

            # Refill tokens based on elapsed time
            self.tokens = min(
                float(self.burst),
                self.tokens + elapsed * self.rate
            )
            self.last_update = now

            wait_time = 0.0

            if self.tokens < tokens:
                # Calculate wait time needed
                needed = tokens - self.tokens
                wait_time = needed / self.rate

                # Wait outside the lock
                # (we'll release and re-acquire)
            else:
                # Deduct tokens immediately
                self.tokens -= tokens
                return 0.0

        # Wait outside the lock
        if wait_time > 0:
            logger.debug(
                "rate_limit_wait",
                extra={
                    "wait_seconds": wait_time,
                    "tokens_needed": tokens,
                    "current_tokens": self.tokens,
                }
            )
            await asyncio.sleep(wait_time)

            # Re-acquire tokens after waiting
            async with self.lock:
                now = time.time()
                elapsed = now - self.last_update
                self.tokens = min(
                    float(self.burst),
                    self.tokens + elapsed * self.rate
                )
                self.last_update = now
                self.tokens -= tokens

        return wait_time

    async def try_acquire(self, tokens: int = 1) -> bool:
        """Try to acquire tokens without waiting.

        Args:
            tokens: Number of tokens to acquire

        Returns:
            True if tokens were acquired, False if would need to wait
        """
        async with self.lock:
            now = time.time()
            elapsed = now - self.last_update

            # Refill tokens
            self.tokens = min(
                float(self.burst),
                self.tokens + elapsed * self.rate
            )
            self.last_update = now

            if self.tokens >= tokens:
                self.tokens -= tokens
                return True
            return False

    def get_wait_time(self, tokens: int = 1) -> float:
        """Get estimated wait time without acquiring.

        Args:
            tokens: Number of tokens needed

        Returns:
            Estimated wait time in seconds (0 if no wait needed)
        """
        now = time.time()
        elapsed = now - self.last_update

        # Calculate current tokens (don't modify state)
        current_tokens = min(
            float(self.burst),
            self.tokens + elapsed * self.rate
        )

        if current_tokens >= tokens:
            return 0.0

        needed = tokens - current_tokens
        return needed / self.rate

    @property
    def available_tokens(self) -> float:
        """Get current available tokens (approximate)."""
        now = time.time()
        elapsed = now - self.last_update
        return min(float(self.burst), self.tokens + elapsed * self.rate)

    def reset(self) -> None:
        """Reset limiter to full capacity."""
        self.tokens = float(self.burst)
        self.last_update = time.time()


# Pre-configured rate limiters per endpoint type
# These are created as factory functions to allow fresh instances
def create_rate_limiters() -> dict[str, RateLimiter]:
    """Create pre-configured rate limiters for each endpoint type.

    Returns:
        Dictionary mapping endpoint type to RateLimiter instance
    """
    return {
        "trending": RateLimiter(
            rate=settings.get_rate_limit_per_second("trending"),
            burst=10  # Allow some burst for efficiency
        ),
        "hashtag": RateLimiter(
            rate=settings.get_rate_limit_per_second("hashtag"),
            burst=5  # More conservative for hashtags
        ),
        "user": RateLimiter(
            rate=settings.get_rate_limit_per_second("user"),
            burst=3  # Most restrictive for user endpoints
        ),
    }


# Global rate limiters instance (lazy initialization)
_rate_limiters: Optional[dict[str, RateLimiter]] = None


def get_rate_limiters() -> dict[str, RateLimiter]:
    """Get or create global rate limiters.

    Returns:
        Dictionary of RateLimiter instances by endpoint type
    """
    global _rate_limiters
    if _rate_limiters is None:
        _rate_limiters = create_rate_limiters()
    return _rate_limiters


# Convenience accessors
RATE_LIMITS = {
    "trending": lambda: get_rate_limiters()["trending"],
    "hashtag": lambda: get_rate_limiters()["hashtag"],
    "user": lambda: get_rate_limiters()["user"],
}
