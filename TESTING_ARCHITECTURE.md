# Trendscope Testing Architecture

**Date:** 2026-02-17  
**Scope:** Stages 1-4 (Backend API, Scraper, Trend Detection, Alert Pipeline Foundation)  
**Status:** Test Infrastructure Design

---

## Executive Summary

This document outlines a comprehensive testing strategy for Trendscope stages 1-4. The testing approach follows a **4-Layer Pyramid**:

```
        /\
       /  \     E2E Tests (Real TikTok API + IPRoyal)
      /----\    -----------------------------------
     /      \   Live Integration Tests
    /--------\  -----------------------------------
   /          \ Integration Tests (Redis, PostgreSQL)
  /------------\-----------------------------------
 /              \Unit Tests (Isolated Components)
/----------------\----------------------------------
```

**Key Principles:**
1. **Test what GLM-5 built** - Focus on stages 1-4, avoid conflicting with stage 5-6 work
2. **Real-world validation** - Live tests with IPRoyal and TikTok API
3. **Iterative execution** - Start fast, expand coverage
4. **Parallel execution** - Independent test modules run simultaneously

---

## Stage Inventory

| Stage | Module | Status | Components to Test |
|-------|--------|--------|-------------------|
| 01 | `/frontend/app/api/` | Complete | API routes, auth, webhooks |
| 02 | `/frontend/app/api/webhooks/` | Complete | Stripe webhooks |
| 03 | `/scraper/` | Complete | Producer, rate limiter, circuit breaker, health |
| 04 | `/detection/` | Complete | Consumer, velocity engine, saturation, lifecycle, persistence |
| 05 | `/alerts/` | Partial | Models (GLM-5 working on rest) |

---

## Test Layer 1: Unit Tests (Fast, Isolated)

### 1.1 Scraper Module Unit Tests
**Location:** `scraper/tests/unit/`

| Test File | Target | Test Cases |
|-----------|--------|------------|
| `test_rate_limiter.py` | `RateLimiter` | Token bucket algorithm, burst handling, thread safety |
| `test_circuit_breaker.py` | `CircuitBreaker` | State transitions, failure counting, recovery logic |
| `test_models.py` | `VideoData`, `VideoStats` | Validation, serialization, edge cases |
| `test_health.py` | Health endpoints | Status reporting, component checks |

**Key Scenarios:**
- Rate limiter: Burst capacity, gradual refill, concurrent access
- Circuit breaker: CLOSED→OPEN→HALF_OPEN→CLOSED transitions
- Models: Invalid data rejection, JSON serialization round-trip

### 1.2 Detection Module Unit Tests
**Location:** `detection/tests/unit/`

| Test File | Target | Test Cases |
|-----------|--------|------------|
| `test_velocity_engine.py` | `VelocityEngine` | Exponential growth detection, R² calculation, Rule of 70 |
| `test_saturation.py` | `SaturationEngine` | Saturation scoring, lifecycle thresholds |
| `test_lifecycle_manager.py` | `LifecycleManager` | State transitions, expiration logic |
| `test_models.py` | `Trend`, `VideoData` | Validation, factory methods |
| `test_trend_detector.py` | `TrendDetector` | Trend extraction, aggregation logic |

**Key Scenarios:**
- Velocity: Perfect exponential (R²=1.0), no growth (R²=0), insufficient data
- Saturation: Early stage (0-30%), peaking (60-80%), saturated (90%+)
- Lifecycle: emerging→peaking→saturated→expired transitions

### 1.3 Alerts Module Unit Tests
**Location:** `alerts/tests/unit/`

| Test File | Target | Test Cases |
|-----------|--------|------------|
| `test_models.py` | `Alert`, `Tier` | Validation, status transitions |
| `test_deduplication.py` | Deduplication logic | Hash generation, window checking |
| `test_tier_router.py` | `TierRouter` | Tier-based routing logic |

---

## Test Layer 2: Integration Tests (Component Interactions)

### 2.1 Scraper-Redis Integration
**Location:** `scraper/tests/integration/`

| Test File | Scenario |
|-----------|----------|
| `test_redis_queue.py` | Push/pop video data, TTL enforcement |
| `test_producer_consumer.py` | End-to-end producer→Redis→consumer flow |

**Requirements:** Redis running (local or Upstash)

### 2.2 Detection-PostgreSQL Integration
**Location:** `detection/tests/integration/`

| Test File | Scenario |
|-----------|----------|
| `test_persistence.py` | Trend CRUD, velocity history, upsert logic |
| `test_consumer_pipeline.py` | Video→Detection→Database full flow |

**Requirements:** PostgreSQL with migrations applied

---

## Test Layer 3: Live Integration Tests (Real Services)

### 3.1 IPRoyal Proxy Connectivity
**Location:** `scraper/tests/live/`

| Test File | Scenario | What It Tests |
|-----------|----------|---------------|
| `test_iproyal_connectivity.py` | Basic proxy connection | IP rotation working |
| `test_ip_rotation.py` | Multiple requests | Different egress IPs |
| `test_session_persistence.py` | Session stickiness | Session lifetime (30m) |

**Requirements:** IPRoyal credentials from `.env`
**Safety:** Low request volume (< 10 req), read-only operations

### 3.2 TikTok API Scraping (Limited)
**Location:** `scraper/tests/live/`

| Test File | Scenario | What It Tests |
|-----------|----------|---------------|
| `test_tiktok_trending.py` | Scrape 5 trending videos | TikTok-Api working |
| `test_tiktok_hashtag.py` | Scrape #viral hashtag | Hashtag endpoint |
| `test_rate_limit_compliance.py` | 10 requests at limit | Rate limiting active |

**Requirements:** IPRoyal proxy (MUST use), Playwright installed
**Safety:** Minimal requests (5-10), circuit breaker active, rate limits enforced

---

## Test Layer 4: E2E & Load Tests

### 4.1 End-to-End Data Flow
**Location:** `tests/e2e/`

| Test File | Scenario |
|-----------|----------|
| `test_full_pipeline.py` | TikTok→Scraper→Redis→Detection→PostgreSQL |

### 4.2 Load & Stress Tests
**Location:** `tests/load/`

| Test File | Scenario | Purpose |
|-----------|----------|---------|
| `test_rate_limiter_stress.py` | 1000 concurrent acquires | Thread safety, performance |
| `test_circuit_breaker_stress.py` | Rapid failure simulation | Recovery behavior |
| `test_detection_throughput.py` | 10k videos processed | Processing capacity |

---

## Test Infrastructure

### Directory Structure
```
/scraper/tests/
├── __init__.py
├── conftest.py              # Shared fixtures
├── unit/
│   ├── __init__.py
│   ├── test_rate_limiter.py
│   ├── test_circuit_breaker.py
│   ├── test_models.py
│   └── test_health.py
├── integration/
│   ├── __init__.py
│   ├── test_redis_queue.py
│   └── test_producer_consumer.py
└── live/
    ├── __init__.py
    ├── test_iproyal_connectivity.py
    └── test_tiktok_trending.py

/detection/tests/
├── __init__.py
├── conftest.py
├── fixtures/
│   ├── sample_video_data.json
│   └── sample_trend_data.json
├── unit/
│   ├── test_velocity_engine.py
│   ├── test_saturation.py
│   ├── test_lifecycle_manager.py
│   ├── test_models.py
│   └── test_trend_detector.py
├── integration/
│   ├── test_persistence.py
│   └── test_consumer_pipeline.py
└── load/
    └── test_detection_throughput.py

/alerts/tests/
├── __init__.py
├── conftest.py
└── unit/
    ├── test_models.py
    ├── test_deduplication.py
    └── test_tier_router.py

/tests/                      # Project-level tests
├── e2e/
│   └── test_full_pipeline.py
└── load/
    ├── test_rate_limiter_stress.py
    └── test_circuit_breaker_stress.py
```

### Shared Infrastructure Files

**`pytest.ini`** (Root level)
```ini
[pytest]
asyncio_mode = auto
testpaths = scraper/tests detection/tests alerts/tests
test_categories =
    unit: Unit tests (fast, isolated)
    integration: Integration tests (requires services)
    live: Live tests (requires real APIs)
    load: Load/stress tests
    e2e: End-to-end tests
markers =
    unit: Unit tests
    integration: Integration tests
    live: Live tests with real APIs
    load: Load tests
    slow: Slow tests
    requires_redis: Tests requiring Redis
    requires_postgres: Tests requiring PostgreSQL
    requires_proxy: Tests requiring IPRoyal proxy
```

**`conftest.py`** (Per-module)
- Fixtures for mocked Redis, PostgreSQL
- Fixtures for real Redis, PostgreSQL (integration)
- Fixtures for IPRoyal proxy configuration
- Sample data generators

### Test Data Fixtures

**Sample Video Data** (`detection/tests/fixtures/sample_video_data.json`)
- 10 realistic TikTok video records
- Various growth patterns (viral, steady, flat)
- Complete metadata (author, music, stats)

**Sample Trend Data** (`detection/tests/fixtures/sample_trend_data.json`)
- Trends at different lifecycle stages
- Velocity history time-series data
- Saturation scoring examples

---

## Execution Strategy

### Phase 1: Unit Tests (Immediate - Can Run in Parallel)
All unit tests are independent and can run simultaneously.

**Agent Tasks:**
1. Scraper unit tests agent
2. Detection unit tests agent  
3. Alerts unit tests agent

### Phase 2: Integration Tests (Sequential, requires services)
Requires Redis and PostgreSQL to be running.

**Agent Tasks:**
1. Scraper-Redis integration agent
2. Detection-PostgreSQL integration agent

### Phase 3: Live Tests (Careful, rate-limited)
Real API calls - must respect rate limits.

**Agent Tasks:**
1. IPRoyal connectivity agent
2. TikTok API live test agent (carefully rate-limited)

### Phase 4: Load & E2E Tests (Final validation)
Performance and full pipeline validation.

**Agent Tasks:**
1. Load test agent
2. E2E pipeline agent

---

## Safety & Constraints

### Live Test Safety
```python
# MAX_REQUESTS limits for live tests
TIKTOK_LIVE_TEST_MAX_REQUESTS = 10
TIKTOK_LIVE_TEST_RATE = 0.17  # 10 req/min

# Circuit breaker must be active
CIRCUIT_BREAKER_REQUIRED = True

# Proxy required for all TikTok tests
PROXY_REQUIRED = True
```

### Environment Detection
Tests should detect environment and skip if requirements not met:
```python
# Skip if no Redis
pytest.skip("Redis not available", allow_module_level=True)

# Skip if no proxy credentials
pytest.skip("IPRoyal credentials not configured")

# Skip live tests by default (opt-in)
pytest.skip("Live tests disabled (use --run-live to enable)")
```

---

## Success Criteria

### Minimum Viable Test Coverage
- [ ] 80%+ unit test coverage for `scraper/` (excluding live API calls)
- [ ] 80%+ unit test coverage for `detection/` (excluding database)
- [ ] 100% model validation coverage
- [ ] Circuit breaker state transitions fully tested
- [ ] Rate limiting behavior fully tested
- [ ] Velocity calculation accuracy validated

### Integration Test Success
- [ ] Redis queue operations work end-to-end
- [ ] PostgreSQL persistence works end-to-end
- [ ] Producer→Consumer pipeline functional

### Live Test Success
- [ ] IPRoyal proxy connects successfully
- [ ] IP rotation working (different egress IPs)
- [ ] TikTok-Api fetches real video data
- [ ] Rate limiting prevents blocks

### Performance Benchmarks
- [ ] Rate limiter: 1000 concurrent acquires < 1 second
- [ ] Detection: Process 1000 videos < 5 seconds
- [ ] Circuit breaker: Recovery < 5 minutes

---

## Implementation Notes for Agents

### Agent 1: Test Infrastructure Setup
- Create pytest.ini at root
- Create conftest.py files for each module
- Create fixture data files
- Add pytest and pytest-asyncio to requirements.txt

### Agent 2: Scraper Unit Tests
- Test rate_limiter.py (token bucket, burst, concurrency)
- Test circuit_breaker.py (states, transitions, recovery)
- Test models.py (validation, serialization)
- Test health.py (endpoint responses)

### Agent 3: Detection Unit Tests
- Test velocity_engine.py (R², growth rate, doubling time)
- Test saturation.py (scoring, thresholds)
- Test lifecycle_manager.py (state transitions)
- Test trend_detector.py (aggregation, extraction)

### Agent 4: Integration Tests
- Test Redis queue operations
- Test PostgreSQL persistence
- Test producer→consumer flow

### Agent 5: Live Tests
- Test IPRoyal connectivity
- Test TikTok API with proxy (limited requests)
- Validate real-world data flow

### Agent 6: Load & E2E Tests
- Stress test rate limiter
- Stress test circuit breaker
- Full pipeline E2E test

---

## Risks & Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| GLM-5 conflicts | High | Only test stages 1-4, avoid /alerts/ beyond models |
| IPRoyal blocks | Medium | Low request volume, circuit breaker active |
| TikTok blocks | Medium | Use proxy, rate limits, minimal test data |
| Test flakiness | Low | Proper fixtures, deterministic data |
| Long execution | Low | Parallel execution, categorized tests |

---

## Next Steps

1. **Spawn Agent 1:** Create test infrastructure (pytest.ini, conftest.py, fixtures)
2. **Spawn Agents 2-3 in parallel:** Unit tests for scraper and detection
3. **Spawn Agent 4:** Integration tests (requires services)
4. **Spawn Agent 5:** Live tests (IPRoyal + TikTok, careful rate limiting)
5. **Spawn Agent 6:** Load and E2E tests
6. **Execute full test suite** and generate coverage report
