"""
Live test configuration and fixtures.

Handles:
- --run-live flag detection
- Proxy credential validation
- Rate limiting enforcement
- Circuit breaker setup
"""

import asyncio
import os
import time
from typing import AsyncGenerator, Optional

import pytest
import pytest_asyncio


# =============================================================================
# Pytest Configuration
# =============================================================================

def pytest_addoption(parser):
    """Add --run-live flag to pytest."""
    parser.addoption(
        "--run-live",
        action="store_true",
        default=False,
        help="Run live integration tests with real external services",
    )


def pytest_configure(config):
    """Configure pytest with live test markers."""
    config.addinivalue_line(
        "markers", "live: Live tests with real external services"
    )
    config.addinivalue_line(
        "markers", "requires_proxy: Tests requiring IPRoyal proxy"
    )
    config.addinivalue_line(
        "markers", "requires_tiktok: Tests requiring TikTok API access"
    )
    config.addinivalue_line(
        "markers", "slow: Tests that take longer to complete"
    )


def pytest_collection_modifyitems(config, items):
    """Skip live tests unless --run-live is specified."""
    if not config.getoption("--run-live"):
        skip_live = pytest.mark.skip(
            reason="Live tests disabled (use --run-live to enable)"
        )
        for item in items:
            if "live" in item.keywords:
                item.add_marker(skip_live)


# =============================================================================
# Proxy Configuration Fixtures
# =============================================================================

@pytest.fixture(scope="module")
def proxy_url() -> Optional[str]:
    """Get IPRoyal session proxy URL from environment."""
    from scraper.proxy_utils import load_proxy_from_env, validate_proxy_url, test_proxy_connection
    
    proxy = load_proxy_from_env()
    if not proxy:
        pytest.skip("PROXY_URL not configured in environment", allow_module_level=True)
    
    # Validate proxy URL
    validation = validate_proxy_url(proxy)
    if not validation["valid"]:
        pytest.skip(
            f"PROXY_URL is invalid: {'; '.join(validation['issues'])}",
            allow_module_level=True
        )
    
    # Check for warnings (expired session credentials)
    if validation["warnings"]:
        warnings_str = "; ".join(validation["warnings"])
        # Don't skip, but warn
        print(f"\n⚠️  PROXY WARNING: {warnings_str}")
    
    # Test connection
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        test_result = loop.run_until_complete(test_proxy_connection(proxy))
        loop.close()
        
        if not test_result["success"]:
            error_msg = test_result.get("error", "Unknown error")
            if "407" in error_msg:
                pytest.skip(
                    f"Proxy authentication failed (407). Credentials may be expired. "
                    f"Get new credentials from IPRoyal dashboard. Original URL had: "
                    f"{validation.get('components', {}).get('password_length', 'unknown')} char password",
                    allow_module_level=True
                )
            else:
                pytest.skip(f"Proxy connection test failed: {error_msg}", allow_module_level=True)
    except Exception as e:
        pytest.skip(f"Could not test proxy: {e}", allow_module_level=True)
    
    return proxy


@pytest.fixture(scope="module")
def proxy_url_rotating() -> Optional[str]:
    """Get IPRoyal rotating proxy URL from environment."""
    proxy = os.getenv("PROXY_URL_ROTATING")
    if not proxy:
        pytest.skip(
            "PROXY_URL_ROTATING not configured in environment",
            allow_module_level=True
        )
    return proxy


@pytest.fixture(scope="module")
def proxy_credentials() -> dict:
    """Get parsed proxy credentials."""
    proxy = os.getenv("PROXY_URL")
    if not proxy:
        pytest.skip("PROXY_URL not configured", allow_module_level=True)
    
    # Parse proxy URL: http://user:pass@host:port
    try:
        from urllib.parse import urlparse
        parsed = urlparse(proxy)
        return {
            "url": proxy,
            "host": parsed.hostname,
            "port": parsed.port,
            "username": parsed.username,
            "password": parsed.password,
            "scheme": parsed.scheme,
        }
    except Exception as e:
        pytest.skip(f"Failed to parse PROXY_URL: {e}", allow_module_level=True)


# =============================================================================
# Rate Limiting Fixtures
# =============================================================================

@pytest.fixture(scope="module")
def rate_limit_delay() -> float:
    """
    Minimum delay between requests in seconds.
    
    0.17 req/sec = ~6 seconds between requests
    """
    return 6.0  # 6 seconds = 10 requests per minute max


@pytest_asyncio.fixture
async def rate_limited_request(rate_limit_delay: float):
    """
    Context manager for rate-limited requests.
    
    Usage:
        async with rate_limited_request:
            # Make request here
    """
    last_request_time = 0
    
    class RateLimiter:
        async def __aenter__(self):
            nonlocal last_request_time
            elapsed = time.time() - last_request_time
            if elapsed < rate_limit_delay:
                wait_time = rate_limit_delay - elapsed
                await asyncio.sleep(wait_time)
            return self
        
        async def __aexit__(self, exc_type, exc_val, exc_tb):
            nonlocal last_request_time
            last_request_time = time.time()
            return False
    
    return RateLimiter()


# =============================================================================
# Circuit Breaker Fixtures
# =============================================================================

@pytest_asyncio.fixture
async def circuit_breaker():
    """Create a circuit breaker for live tests."""
    from scraper.circuit_breaker import CircuitBreaker
    
    # More sensitive settings for live tests
    cb = CircuitBreaker(
        failure_threshold=2,  # Open after 2 failures
        recovery_timeout=60,  # 1 minute recovery (faster for tests)
        half_open_max_calls=1  # Only 1 test call in half-open
    )
    return cb


# =============================================================================
# HTTP Client Fixtures
# =============================================================================

@pytest_asyncio.fixture
async def http_client_with_proxy(proxy_url: str) -> AsyncGenerator:
    """Create httpx client with proxy configuration."""
    try:
        import httpx
    except ImportError:
        pytest.skip("httpx not installed", allow_module_level=True)
    
    client = httpx.AsyncClient(
        proxy=proxy_url,
        timeout=30.0,
        follow_redirects=True,
    )
    try:
        yield client
    finally:
        await client.aclose()


@pytest_asyncio.fixture
async def http_client_without_proxy() -> AsyncGenerator:
    """Create httpx client without proxy (for comparison tests)."""
    try:
        import httpx
    except ImportError:
        pytest.skip("httpx not installed", allow_module_level=True)
    
    client = httpx.AsyncClient(
        timeout=30.0,
        follow_redirects=True,
    )
    try:
        yield client
    finally:
        await client.aclose()


# =============================================================================
# Request Tracking (Safety)
# =============================================================================

@pytest.fixture(scope="session")
def request_tracker():
    """Track request counts to enforce MAX 10 limit."""
    class RequestTracker:
        def __init__(self, max_requests: int = 10):
            self.max_requests = max_requests
            self.count = 0
            self.requests_made = []
        
        def record(self, endpoint: str, test_name: str):
            """Record a request."""
            self.count += 1
            self.requests_made.append({
                "endpoint": endpoint,
                "test": test_name,
                "timestamp": time.time(),
            })
            if self.count > self.max_requests:
                raise RuntimeError(
                    f"MAX REQUEST LIMIT EXCEEDED: {self.count} requests "
                    f"(max: {self.max_requests})"
                )
        
        def get_summary(self) -> dict:
            """Get request summary."""
            return {
                "total_requests": self.count,
                "max_allowed": self.max_requests,
                "requests": self.requests_made,
            }
    
    return RequestTracker(max_requests=10)


# =============================================================================
# TikTok API Fixtures
# =============================================================================

@pytest_asyncio.fixture
async def tiktok_api_with_proxy(proxy_url: str):
    """
    Create TikTok-Api instance with proxy.
    
    Note: TikTok-Api uses Playwright which handles proxies differently.
    The proxy is passed at browser launch time.
    """
    try:
        from TikTokApi import TikTokApi
    except ImportError:
        pytest.skip(
            "TikTok-Api not installed (pip install TikTok-Api)",
            allow_module_level=True
        )
    
    # TikTok-Api v6+ uses context managers
    api = TikTokApi()
    return api


# =============================================================================
# Validation Fixtures
# =============================================================================

@pytest.fixture
def validate_video_data():
    """Validate TikTok video data structure."""
    def _validate(video_data: dict) -> bool:
        required_fields = ["id"]
        for field in required_fields:
            if field not in video_data:
                raise ValueError(f"Missing required field: {field}")
        
        # Validate ID format (numeric string)
        if not video_data["id"].isdigit():
            raise ValueError(f"Invalid video ID format: {video_data['id']}")
        
        return True
    
    return _validate
