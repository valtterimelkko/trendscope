# Stage 03: Scraper Integration

**Status:** Planned
**Estimated Duration:** 8-10 hours
**Assigned Agent:** Unassigned
**Last Updated:** 2026-02-17

---

## 1. Overview

This stage implements the TikTok data collection infrastructure using a self-hosted TikTok-Api producer with IPRoyal rotating residential proxies. The scraper pushes video metadata to a Redis queue using a producer-consumer pattern, enabling decoupled data ingestion and processing. The implementation follows the architecture defined in `docs/Project-Technical-Architecture.md` Section 3.4 and the detailed guidance in `background_files/SELF_HOSTED.md`.

**Delivers:**
- TikTok-Api producer service with proxy rotation
- Redis queue producer-consumer pattern for video metadata
- Rate limiting per endpoint type (trending, hashtag, user)
- Retry logic with tenacity for transient failures
- Circuit breaker pattern for sustained failures
- Health monitoring endpoints
- Structured logging with correlation IDs

**Success Criteria:**
- [ ] Scraper runs continuously without blocks for 24+ hours
- [ ] Rate limits respected: trending (10-20 req/min), hashtag (5-10 req/min), user (2-5 req/min)
- [ ] Failed requests retry correctly with exponential backoff
- [ ] Circuit breaker opens after 5 consecutive failures, auto-recovers after 5 minutes
- [ ] Health check endpoint returns valid JSON status
- [ ] Video metadata successfully pushed to Redis queue
- [ ] 72-hour TTL enforced on hot cache entries

---

## 2. Dependencies

### Must Complete First
| Stage | Status | What We Need |
|-------|--------|--------------|
| Stage 01 | Planned | Database service layer for trend persistence |
| Redis | Required | Redis instance running (Upstash or local) |
| IPRoyal Proxy | Configured | Credentials in `.env` file at project root |
| Playwright | Required | Chromium browser installed |

### Can Run In Parallel
- Stage 02 (Stripe Webhooks): No shared files, independent infrastructure
- Stage 06 (Monitoring): Can define metrics schema while scraper is built

### Blocks These Stages
- Stage 04 (Trend Detection Engine): Consumes video data from Redis queue produced by this stage
- Stage 05 (Alert Pipeline): Requires trend data from detection engine (indirect dependency)

---

## 3. Technical Components

### 3.1 Scraper Service Architecture

```
+-------------------+       +----------------+       +------------------+
|   TikTok-Api      |       |    Redis       |       |   PostgreSQL     |
|   (Playwright)    |------>|    Queue       |------>|   (Trends)       |
|   + IPRoyal       |       |   72hr TTL     |       |                  |
+-------------------+       +----------------+       +------------------+
        |                          |                        |
        v                          v                        v
+-------------------+       +----------------+       +------------------+
|   Rate Limiter    |       |   Consumer     |       |   Trend Detector |
|   (Token Bucket)  |       |   (Processor)  |       |   (Stage 04)     |
+-------------------+       +----------------+       +------------------+
        |
        v
+-------------------+
|  Circuit Breaker  |
|  + Retry Logic    |
+-------------------+
```

### 3.2 Directory Structure

```
/scraper/
+-- __init__.py
+-- main.py                    # Entry point, orchestrates producer
+-- config.py                  # Environment configuration loader
+-- producer.py                # TikTok-Api producer implementation
+-- consumer.py                # Redis consumer (preliminary for Stage 04)
+-- rate_limiter.py            # Token bucket rate limiter
+-- circuit_breaker.py         # Circuit breaker pattern
+-- retry_handler.py           # Retry logic with tenacity
+-- models.py                  # Pydantic models for video data
+-- health.py                  # Health check endpoints
+-- logging_config.py          # Structured logging setup
+-- tests/
|   +-- __init__.py
|   +-- test_producer.py
|   +-- test_rate_limiter.py
|   +-- test_circuit_breaker.py
|   +-- test_retry_handler.py
+-- requirements.txt           # Python dependencies
```

### 3.3 Producer Implementation (producer.py)

The producer fetches TikTok data and pushes to Redis queue.

```python
# Key classes and methods:

class TikTokProducer:
    """Produces video data to Redis queue."""

    def __init__(self, redis_client: redis.Redis, proxy: str = None):
        self.redis = redis_client
        self.proxy = proxy
        self.rate_limiter = RateLimiter(rate=0.17, burst=5)  # ~10 req/min
        self.circuit_breaker = CircuitBreaker(failure_threshold=5, recovery_timeout=300)

    async def scrape_trending(self, count: int = 100) -> AsyncGenerator[VideoData, None]:
        """Fetch trending videos with rate limiting and retry."""
        async with self.circuit_breaker:
            await self.rate_limiter.acquire()
            async with TikTokApi() as api:
                async for video in api.trending.videos(count=count):
                    yield self._parse_video(video)

    async def scrape_hashtag(self, hashtag: str, count: int = 100) -> AsyncGenerator[VideoData, None]:
        """Fetch videos for specific hashtag with conservative rate limiting."""
        # Rate limit: 5-10 req/min (0.08-0.17 req/sec)
        ...

    async def scrape_user(self, username: str, count: int = 50) -> AsyncGenerator[VideoData, None]:
        """Fetch user videos with most conservative rate limiting."""
        # Rate limit: 2-5 req/min (0.03-0.08 req/sec)
        ...

    async def push_to_queue(self, video: VideoData, queue: str = "tiktok:videos") -> None:
        """Push video metadata to Redis queue with 72-hour TTL."""
        await self.redis.lpush(queue, video.model_dump_json())
        await self.redis.expire(queue, 72 * 3600)

    def _parse_video(self, video) -> VideoData:
        """Extract relevant fields from TikTok video object."""
        ...

    async def run_continuous(self, interval: int = 300):
        """Run scraper continuously with configurable interval between cycles."""
        ...
```

### 3.4 Rate Limiter Implementation (rate_limiter.py)

Token bucket algorithm for smooth rate limiting.

```python
class RateLimiter:
    """Token bucket rate limiter for API calls."""

    def __init__(self, rate: float, burst: int):
        """
        Args:
            rate: Requests per second (e.g., 0.17 = ~10 req/min)
            burst: Maximum burst size
        """
        self.rate = rate
        self.burst = burst
        self.tokens = burst
        self.last_update = time.time()
        self.lock = asyncio.Lock()

    async def acquire(self, tokens: int = 1) -> None:
        """Acquire tokens, waiting if necessary."""
        async with self.lock:
            now = time.time()
            elapsed = now - self.last_update
            self.tokens = min(self.burst, self.tokens + elapsed * self.rate)
            self.last_update = now

            if self.tokens < tokens:
                wait_time = (tokens - self.tokens) / self.rate
                await asyncio.sleep(wait_time)
                self.tokens = 0
            else:
                self.tokens -= tokens

# Pre-configured rate limiters per endpoint type
RATE_LIMITS = {
    "trending": RateLimiter(rate=0.25, burst=10),   # 15 req/min, burst 10
    "hashtag": RateLimiter(rate=0.12, burst=5),     # 7 req/min, burst 5
    "user": RateLimiter(rate=0.05, burst=3),        # 3 req/min, burst 3
}
```

### 3.5 Circuit Breaker Implementation (circuit_breaker.py)

Prevents cascading failures during TikTok outages or blocks.

```python
from enum import Enum

class CircuitState(Enum):
    CLOSED = "closed"        # Normal operation
    OPEN = "open"            # Failing, reject requests
    HALF_OPEN = "half_open"  # Testing if recovered

class CircuitBreaker:
    """Circuit breaker for TikTok API calls."""

    def __init__(
        self,
        failure_threshold: int = 5,
        recovery_timeout: int = 300,  # 5 minutes
        half_open_max_calls: int = 3
    ):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.half_open_max_calls = half_open_max_calls
        self.failure_count = 0
        self.success_count = 0
        self.last_failure_time: Optional[float] = None
        self.state = CircuitState.CLOSED
        self.lock = asyncio.Lock()

    async def call(self, func: Callable, *args, **kwargs) -> Any:
        """Execute function with circuit breaker protection."""
        async with self.lock:
            await self._check_state_transition()

            if self.state == CircuitState.OPEN:
                raise CircuitOpenError("Circuit breaker is OPEN - TikTok API unavailable")

        try:
            result = await func(*args, **kwargs)
            await self._on_success()
            return result
        except Exception as e:
            await self._on_failure()
            raise

    async def _check_state_transition(self) -> None:
        """Check and update circuit state based on time."""
        if self.state == CircuitState.OPEN:
            if time.time() - self.last_failure_time > self.recovery_timeout:
                self.state = CircuitState.HALF_OPEN
                self.success_count = 0

    async def _on_success(self) -> None:
        """Handle successful call."""
        async with self.lock:
            self.failure_count = 0
            if self.state == CircuitState.HALF_OPEN:
                self.success_count += 1
                if self.success_count >= self.half_open_max_calls:
                    self.state = CircuitState.CLOSED

    async def _on_failure(self) -> None:
        """Handle failed call."""
        async with self.lock:
            self.failure_count += 1
            self.last_failure_time = time.time()
            if self.failure_count >= self.failure_threshold:
                self.state = CircuitState.OPEN

    def get_state(self) -> dict:
        """Return current circuit breaker state for health checks."""
        return {
            "state": self.state.value,
            "failure_count": self.failure_count,
            "last_failure_time": self.last_failure_time,
        }
```

### 3.6 Retry Handler Implementation (retry_handler.py)

Exponential backoff retry logic using tenacity.

```python
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
    before_sleep_log,
)

# Custom exceptions
class TikTokScrapeError(Exception):
    """Base TikTok scraping error."""
    pass

class RateLimitError(TikTokScrapeError):
    """Rate limit exceeded."""
    pass

class BlockedError(TikTokScrapeError):
    """IP blocked by TikTok."""
    pass

class EmptyResponseError(TikTokScrapeError):
    """Empty response from TikTok."""
    pass

# Retry decorator for scraper methods
def with_retry(max_attempts: int = 3, min_wait: float = 4, max_wait: float = 60):
    """Decorator for retry with exponential backoff."""
    return retry(
        stop=stop_after_attempt(max_attempts),
        wait=wait_exponential(multiplier=1, min=min_wait, max=max_wait),
        retry=retry_if_exception_type((RateLimitError, asyncio.TimeoutError, EmptyResponseError)),
        before_sleep=before_sleep_log(logger, logging.WARNING),
        reraise=True,
    )

# Usage example:
@with_retry(max_attempts=3)
async def fetch_trending_with_retry(producer: TikTokProducer, count: int):
    """Fetch trending with automatic retry on transient errors."""
    try:
        return await producer.scrape_trending(count)
    except Exception as e:
        error_msg = str(e).lower()
        if "rate" in error_msg or "limit" in error_msg or "429" in error_msg:
            raise RateLimitError(str(e))
        elif "block" in error_msg or "banned" in error_msg or "403" in error_msg:
            raise BlockedError(str(e))
        elif "empty" in error_msg or "no videos" in error_msg:
            raise EmptyResponseError(str(e))
        raise
```

### 3.7 Data Models (models.py)

Pydantic models for type-safe video data handling.

```python
from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, List

class VideoStats(BaseModel):
    """Video engagement statistics."""
    play_count: int = Field(..., alias="playCount")
    digg_count: int = Field(..., alias="diggCount")  # Likes
    share_count: int = Field(..., alias="shareCount")
    comment_count: int = Field(..., alias="commentCount")

class VideoAuthor(BaseModel):
    """Video author/creator information."""
    unique_id: str = Field(..., alias="uniqueId")
    nickname: Optional[str] = None
    follower_count: int = Field(..., alias="followerCount")

class VideoMusic(BaseModel):
    """Music/sound information."""
    id: Optional[str] = None
    title: Optional[str] = None
    author_name: Optional[str] = None

class VideoData(BaseModel):
    """Complete video metadata structure."""
    id: str
    desc: Optional[str] = None
    create_time: int = Field(..., alias="createTime")
    stats: VideoStats
    author: VideoAuthor
    music: Optional[VideoMusic] = None
    hashtags: List[str] = Field(default_factory=list)
    scraped_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        populate_by_name = True

class ScraperHealth(BaseModel):
    """Health check response structure."""
    status: str  # "healthy" | "degraded" | "unhealthy"
    version: str
    timestamp: datetime
    checks: dict
    metrics: dict
```

### 3.8 Health Check Service (health.py)

Health monitoring endpoints for scraper status.

```python
from fastapi import FastAPI, Response
from datetime import datetime

app = FastAPI()

class HealthChecker:
    """Scraper health monitoring."""

    def __init__(
        self,
        redis_client: redis.Redis,
        circuit_breaker: CircuitBreaker,
        producer: TikTokProducer
    ):
        self.redis = redis_client
        self.circuit_breaker = circuit_breaker
        self.producer = producer
        self.last_scrape_time: Optional[datetime] = None
        self.total_videos_scraped = 0
        self.total_errors = 0

    async def check(self) -> ScraperHealth:
        """Perform health check and return status."""
        checks = {}

        # Check Redis connectivity
        try:
            start = time.time()
            await self.redis.ping()
            checks["redis"] = {"status": "pass", "latency_ms": int((time.time() - start) * 1000)}
        except Exception as e:
            checks["redis"] = {"status": "fail", "error": str(e)}

        # Check circuit breaker state
        cb_state = self.circuit_breaker.get_state()
        checks["circuit_breaker"] = {
            "status": "pass" if cb_state["state"] == "closed" else "warn",
            "state": cb_state["state"],
            "failure_count": cb_state["failure_count"],
        }

        # Check last scrape time
        checks["scraper"] = {
            "status": "pass" if self._is_recent_scrape() else "warn",
            "last_scrape": self.last_scrape_time.isoformat() if self.last_scrape_time else None,
            "videos_scraped": self.total_videos_scraped,
        }

        # Determine overall status
        if all(c["status"] == "pass" for c in checks.values()):
            status = "healthy"
        elif any(c["status"] == "fail" for c in checks.values()):
            status = "unhealthy"
        else:
            status = "degraded"

        return ScraperHealth(
            status=status,
            version="1.0.0",
            timestamp=datetime.utcnow(),
            checks=checks,
            metrics={
                "videos_scraped": self.total_videos_scraped,
                "errors": self.total_errors,
            }
        )

    def _is_recent_scrape(self) -> bool:
        """Check if last scrape was within expected interval."""
        if not self.last_scrape_time:
            return False
        return (datetime.utcnow() - self.last_scrape_time).total_seconds() < 600  # 10 min

@app.get("/health")
async def health_endpoint():
    """Health check endpoint."""
    health = await health_checker.check()
    status_code = 200 if health.status in ["healthy", "degraded"] else 503
    return Response(
        content=health.model_dump_json(),
        status_code=status_code,
        media_type="application/json"
    )

@app.get("/ready")
async def readiness_endpoint():
    """Readiness probe for Kubernetes."""
    health = await health_checker.check()
    if health.status == "healthy":
        return {"ready": True}
    return Response(content={"ready": False}, status_code=503)
```

### 3.9 Configuration (config.py)

Environment-based configuration loader.

```python
from pydantic_settings import BaseSettings
from typing import Optional

class ScraperSettings(BaseSettings):
    """Scraper configuration from environment variables."""

    # Redis
    redis_url: str = "redis://localhost:6379/0"

    # Proxy (IPRoyal - from .env)
    proxy_url: Optional[str] = None  # Format: http://user:pass@geo.iproyal.com:12321

    # Rate limiting (requests per minute)
    rate_limit_trending: int = 15
    rate_limit_hashtag: int = 7
    rate_limit_user: int = 3

    # Scraping
    scrape_batch_size: int = 100
    scrape_interval: int = 300  # seconds between cycles

    # Circuit breaker
    circuit_failure_threshold: int = 5
    circuit_recovery_timeout: int = 300

    # Health check
    health_port: int = 8080

    # Logging
    log_level: str = "INFO"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

# Global settings instance
settings = ScraperSettings()
```

### 3.10 Logging Configuration (logging_config.py)

Structured JSON logging for observability.

```python
import structlog
import logging
import sys

def configure_logging(log_level: str = "INFO"):
    """Configure structured logging for the scraper."""

    # Configure structlog
    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.processors.add_log_level,
            structlog.processors.StackInfoRenderer(),
            structlog.dev.set_exc_info,
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.JSONRenderer(),
        ],
        wrapper_class=structlog.make_filtering_bound_logger(
            logging.getLevelName(log_level)
        ),
        context_class=dict,
        logger_factory=structlog.PrintLoggerFactory(),
        cache_logger_on_first_use=True,
    )

    # Configure standard logging
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=logging.getLevelName(log_level),
    )

def get_logger(name: str) -> structlog.stdlib.BoundLogger:
    """Get a configured logger instance."""
    return structlog.get_logger(name)

# Usage:
# logger = get_logger(__name__)
# logger.info("video_scraped", video_id="12345", author="username")
```

---

## 4. API Contracts

### Internal API Endpoints

#### GET /health

**Purpose:** Health check for scraper service status

**Response (200):**
```json
{
  "status": "healthy",
  "version": "1.0.0",
  "timestamp": "2026-02-17T00:00:00Z",
  "checks": {
    "redis": {"status": "pass", "latency_ms": 3},
    "circuit_breaker": {"status": "pass", "state": "closed", "failure_count": 0},
    "scraper": {"status": "pass", "last_scrape": "2026-02-17T00:00:00Z", "videos_scraped": 5000}
  },
  "metrics": {
    "videos_scraped": 5000,
    "errors": 12
  }
}
```

**Response (503):**
```json
{
  "status": "unhealthy",
  "version": "1.0.0",
  "timestamp": "2026-02-17T00:00:00Z",
  "checks": {
    "redis": {"status": "fail", "error": "Connection refused"},
    "circuit_breaker": {"status": "warn", "state": "open", "failure_count": 5},
    "scraper": {"status": "warn", "last_scrape": null, "videos_scraped": 0}
  },
  "metrics": {
    "videos_scraped": 0,
    "errors": 50
  }
}
```

#### GET /ready

**Purpose:** Kubernetes readiness probe

**Response (200):**
```json
{"ready": true}
```

**Response (503):**
```json
{"ready": false}
```

### Redis Queue Contract

#### Queue: tiktok:videos

**Purpose:** Video metadata queue for consumer processing

**Message Format:**
```json
{
  "id": "7123456789012345678",
  "desc": "Video caption #hashtag",
  "createTime": 1700000000,
  "stats": {
    "playCount": 100000,
    "diggCount": 15000,
    "shareCount": 500,
    "commentCount": 200
  },
  "author": {
    "uniqueId": "username",
    "nickname": "Display Name",
    "followerCount": 50000
  },
  "music": {
    "id": "sound123",
    "title": "Original Sound",
    "authorName": "Creator"
  },
  "hashtags": ["viral", "trending", "fyp"],
  "scrapedAt": "2026-02-17T00:00:00.000Z"
}
```

**TTL:** 72 hours (259,200 seconds)

---

## 5. Database Schema Changes

This stage does not create new tables. It populates existing tables defined in the initial schema:

### Tables Populated

| Table | How Populated | Purpose |
|-------|---------------|---------|
| `trends` | Via consumer (Stage 04) | Detected trends |
| `trend_velocity_history` | Via consumer (Stage 04) | Velocity snapshots |

### Redis Keys Created

| Key Pattern | Type | TTL | Purpose |
|-------------|------|-----|---------|
| `tiktok:videos` | List | 72h | Video metadata queue |
| `scraper:last_run` | String | 24h | Last scrape timestamp |
| `scraper:videos_count` | Counter | 24h | Daily video count |

---

## 6. Testing Requirements

### Unit Tests

| Test | What It Validates |
|------|------------------|
| `test_rate_limiter_acquire` | Token bucket correctly waits when empty |
| `test_rate_limiter_burst` | Burst requests handled correctly |
| `test_rate_limiter_refill` | Tokens refill over time |
| `test_circuit_breaker_closed` | Normal operation passes through |
| `test_circuit_breaker_opens` | Opens after threshold failures |
| `test_circuit_breaker_half_open` | Transitions to half-open after timeout |
| `test_circuit_breaker_recovery` | Closes after successful half-open calls |
| `test_retry_handler_rate_limit` | RateLimitError triggers retry |
| `test_retry_handler_max_attempts` | Fails after max attempts |
| `test_retry_handler_exponential_backoff` | Wait time increases exponentially |
| `test_producer_parse_video` | Video data correctly parsed |
| `test_producer_push_to_queue` | Video correctly pushed to Redis |
| `test_config_loader` | Settings loaded from environment |

### Integration Tests

| Test | What It Validates |
|------|------------------|
| `test_redis_connection` | Can connect to Redis |
| `test_redis_push_pop` | Can push/pop from queue |
| `test_health_check_endpoint` | Health endpoint returns valid JSON |
| `test_scraper_with_mock_tiktok` | Full scrape cycle with mock API |

### Manual Verification

- [ ] Run scraper for 1 hour without errors
- [ ] Verify video data in Redis queue
- [ ] Check rate limiting not triggering TikTok blocks
- [ ] Verify circuit breaker opens on simulated failure
- [ ] Verify circuit breaker recovers after timeout
- [ ] Health check reflects scraper status correctly

---

## 7. Critical Constraints

**DO NOT:**
- Scrape without IPRoyal proxy rotation
- Exceed rate limits (will trigger TikTok blocks)
- Store video content (only metadata)
- Run scraper without circuit breaker enabled
- Log full video URLs with user data
- Commit `.env` file with proxy credentials
- Hardcode proxy URLs in source code
- Disable SSL verification for proxy connections

**MUST:**
- Use `python-dotenv` to load credentials from `.env`
- Implement 72-hour TTL on all Redis video data
- Use structured JSON logging with correlation IDs
- Implement graceful shutdown on SIGTERM
- Report metrics to health check endpoint
- Validate video data before pushing to queue
- Handle empty responses gracefully (not an error)

**PROXY CONFIGURATION:**
- IPRoyal credentials are pre-configured in `.env` file
- Format: `http://user:pass@geo.iproyal.com:12321`
- Read via `settings.proxy_url` in config.py

---

## 8. Progress Log

*Updated by implementing agent during work.*

### [Date] - [Time]
- **Completed:** [What was done]
- **Next:** [What's planned]
- **Blockers:** [Issues or "None"]

---

## 9. Issues & Blockers

*Document any escalations here.*

### [Issue Title] - [Status: Open/Resolved]

**Date:** [When discovered]
**Severity:** Blocker | Warning

**Description:**
[Clear description of the issue]

**Attempts Made:**
1. [Attempt 1]: [Result]
2. [Attempt 2]: [Result]
3. [Attempt 3]: [Result]

**Error Logs:**
```
[Relevant error output]
```

**Resolution:**
[How it was resolved, or "Escalated to Co-CEO"]

---

## 10. Completion Checklist

- [ ] All components built per Section 3
  - [ ] producer.py - TikTok producer implementation
  - [ ] rate_limiter.py - Token bucket rate limiter
  - [ ] circuit_breaker.py - Circuit breaker pattern
  - [ ] retry_handler.py - Retry logic with tenacity
  - [ ] models.py - Pydantic data models
  - [ ] health.py - Health check endpoints
  - [ ] config.py - Configuration loader
  - [ ] logging_config.py - Structured logging
  - [ ] main.py - Entry point
- [ ] API contracts implemented per Section 4
  - [ ] GET /health endpoint
  - [ ] GET /ready endpoint
  - [ ] Redis queue producer
- [ ] All tests passing per Section 6
  - [ ] Unit tests pass
  - [ ] Integration tests pass
- [ ] All constraints followed per Section 7
- [ ] Progress log updated per Section 8
- [ ] Success criteria met (Section 1)
  - [ ] 24+ hour continuous run
  - [ ] Rate limits respected
  - [ ] Retry logic works
  - [ ] Circuit breaker works
  - [ ] Health check works
- [ ] Verified using `verification-before-completion` skill

**Stage Completed:** [Date] | **Final Status:** [Complete/Blocked]

---

## 11. Reference Documents

| Document | Path | Purpose |
|----------|------|---------|
| Technical PRD | `docs/Project-Technical-Architecture.md` | System architecture |
| Self-Hosted Guide | `background_files/SELF_HOSTED.md` | TikTok-Api implementation |
| Technical Feasibility | `background_files/TECH_FEASIBILITY.md` | Algorithm reference |
| Progress Tracker | `PROGRESS.md` | Current project state |
| Proxy Configuration | `.env` | IPRoyal credentials |

---

*Document Version: 1.0*
*Last Updated: 2026-02-17*
