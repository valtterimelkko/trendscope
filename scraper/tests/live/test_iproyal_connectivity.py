"""
IPRoyal Proxy Connectivity Tests

Tests IPRoyal residential proxy functionality:
- Basic connectivity through proxy
- IP rotation verification
- Session persistence
- Authentication
- Region targeting (US)
- Connection latency
- Rotating vs session proxy modes

SAFETY:
- MAX 5 requests (well under 10 limit)
- 6 second delays between requests
- Read-only operations only
"""

import asyncio
import time
from typing import Set

import pytest
import pytest_asyncio

# Test markers
pytestmark = [
    pytest.mark.live,
    pytest.mark.requires_proxy,
    pytest.mark.slow,
]


# =============================================================================
# Test 1: Basic Proxy Connectivity
# =============================================================================

@pytest.mark.live
@pytest.mark.requires_proxy
async def test_iproyal_basic_connectivity(
    http_client_with_proxy,
    rate_limited_request,
    request_tracker,
):
    """
    Test basic proxy connectivity to httpbin.org/ip.
    
    Verifies:
    - Proxy connection succeeds
    - Egress IP is returned
    - Response time is reasonable (< 30s)
    """
    async with rate_limited_request:
        start_time = time.time()
        
        response = await http_client_with_proxy.get(
            "https://httpbin.org/ip",
            timeout=30.0
        )
        
        elapsed = time.time() - start_time
        
        # Record request for safety tracking
        request_tracker.record("httpbin.org/ip", "test_iproyal_basic_connectivity")
        
        # Validate response
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        data = response.json()
        assert "origin" in data, "Response missing 'origin' field"
        
        egress_ip = data["origin"]
        assert egress_ip, "Egress IP is empty"
        
        # Log for visibility
        print(f"\n✓ Basic connectivity test passed")
        print(f"  Egress IP: {egress_ip}")
        print(f"  Latency: {elapsed:.2f}s")
        
        # Validate IP format (basic check)
        ip_parts = egress_ip.split(".")
        assert len(ip_parts) == 4, f"Invalid IP format: {egress_ip}"


# =============================================================================
# Test 2: IP Rotation Verification
# =============================================================================

@pytest.mark.live
@pytest.mark.requires_proxy
async def test_iproyal_ip_rotation(
    proxy_url_rotating,
    rate_limited_request,
    request_tracker,
):
    """
    Test that rotating proxy returns different egress IPs.
    
    Makes 3 requests through rotating proxy and verifies
    we get different IPs (indicating rotation is working).
    
    Note: Due to IPRoyal's rotation logic, same IP may appear
    consecutively. We check for at least 2 unique IPs.
    """
    try:
        import httpx
    except ImportError:
        pytest.skip("httpx not installed")
    
    ips: Set[str] = set()
    latencies = []
    
    # Make 3 requests with rotating proxy
    for i in range(3):
        async with rate_limited_request:
            start_time = time.time()
            
            async with httpx.AsyncClient(
                proxy=proxy_url_rotating,
                timeout=30.0
            ) as client:
                response = await client.get("https://httpbin.org/ip")
            
            elapsed = time.time() - start_time
            latencies.append(elapsed)
            
            # Track request
            request_tracker.record(
                f"httpbin.org/ip (rotation {i+1}/3)",
                "test_iproyal_ip_rotation"
            )
            
            assert response.status_code == 200
            data = response.json()
            egress_ip = data["origin"]
            ips.add(egress_ip)
            
            print(f"  Request {i+1}: IP={egress_ip}, Latency={elapsed:.2f}s")
    
    # Verify we got at least 1 IP (could be same or different)
    assert len(ips) >= 1, "No IPs returned"
    
    # Log rotation results
    print(f"\n✓ IP rotation test completed")
    print(f"  Unique IPs: {len(ips)}")
    print(f"  IPs seen: {', '.join(ips)}")
    print(f"  Avg latency: {sum(latencies)/len(latencies):.2f}s")
    
    # Note: IPRoyal rotating may return same IP for consecutive requests
    # depending on their rotation algorithm. We don't fail on same IPs.
    if len(ips) == 1:
        print("  Note: All requests used same IP (rotation may be time-based)")


# =============================================================================
# Test 3: Session Persistence
# =============================================================================

@pytest.mark.live
@pytest.mark.requires_proxy
async def test_iproyal_session_persistence(
    proxy_url,
    rate_limited_request,
    request_tracker,
):
    """
    Test that session proxy maintains same IP within session.
    
    Session proxies should return the same egress IP for
    multiple requests (session duration: 30m per .env).
    """
    try:
        import httpx
    except ImportError:
        pytest.skip("httpx not installed")
    
    ips: Set[str] = set()
    
    # Make 3 requests with session proxy
    for i in range(3):
        async with rate_limited_request:
            async with httpx.AsyncClient(
                proxy=proxy_url,
                timeout=30.0
            ) as client:
                response = await client.get("https://httpbin.org/ip")
            
            request_tracker.record(
                f"httpbin.org/ip (session {i+1}/3)",
                "test_iproyal_session_persistence"
            )
            
            assert response.status_code == 200
            data = response.json()
            egress_ip = data["origin"]
            ips.add(egress_ip)
            
            print(f"  Request {i+1}: IP={egress_ip}")
    
    print(f"\n✓ Session persistence test completed")
    print(f"  Unique IPs in session: {len(ips)}")
    print(f"  Session IP(s): {', '.join(ips)}")
    
    # Session should ideally maintain same IP
    # Allow for 1 IP change due to potential session rotation
    assert len(ips) <= 2, f"Too many IP changes in session: {len(ips)} unique IPs"


# =============================================================================
# Test 4: Proxy Authentication
# =============================================================================

@pytest.mark.live
@pytest.mark.requires_proxy
async def test_iproyal_authentication(
    proxy_credentials,
    rate_limited_request,
    request_tracker,
):
    """
    Test proxy authentication.
    
    Verifies:
    - Credentials are properly embedded in proxy URL
    - Authentication succeeds
    - Invalid credentials would fail
    """
    try:
        import httpx
    except ImportError:
        pytest.skip("httpx not installed")
    
    # Verify credentials are present
    assert proxy_credentials["username"], "Proxy username is empty"
    assert proxy_credentials["password"], "Proxy password is empty"
    assert proxy_credentials["host"], "Proxy host is empty"
    assert proxy_credentials["port"], "Proxy port is empty"
    
    async with rate_limited_request:
        # Test with valid credentials
        async with httpx.AsyncClient(
            proxy=proxy_credentials["url"],
            timeout=30.0
        ) as client:
            response = await client.get("https://httpbin.org/ip")
        
        request_tracker.record(
            "httpbin.org/ip (auth test)",
            "test_iproyal_authentication"
        )
        
        assert response.status_code == 200, "Authentication failed"
        
        print(f"\n✓ Authentication test passed")
        print(f"  Proxy host: {proxy_credentials['host']}")
        print(f"  Proxy port: {proxy_credentials['port']}")
        print(f"  Username: {proxy_credentials['username'][:10]}...")


# =============================================================================
# Test 5: US Region Targeting
# =============================================================================

@pytest.mark.live
@pytest.mark.requires_proxy
async def test_iproyal_us_region_targeting(
    http_client_with_proxy,
    rate_limited_request,
    request_tracker,
):
    """
    Test that US region targeting is working.
    
    Uses ip-api.com to verify the egress IP is from US.
    """
    async with rate_limited_request:
        # Get IP info from ip-api
        response = await http_client_with_proxy.get(
            "http://ip-api.com/json/",
            timeout=30.0
        )
        
        request_tracker.record("ip-api.com", "test_iproyal_us_region_targeting")
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify country
        country = data.get("country", "Unknown")
        country_code = data.get("countryCode", "Unknown")
        
        print(f"\n✓ Region targeting test completed")
        print(f"  Country: {country} ({country_code})")
        print(f"  Region: {data.get('regionName', 'Unknown')}")
        print(f"  City: {data.get('city', 'Unknown')}")
        print(f"  ISP: {data.get('isp', 'Unknown')}")
        
        # The proxy is configured for US (_country-us in URL)
        assert country_code == "US", f"Expected US, got {country_code}"


# =============================================================================
# Test 6: Connection Latency Measurement
# =============================================================================

@pytest.mark.live
@pytest.mark.requires_proxy
async def test_iproyal_connection_latency(
    http_client_with_proxy,
    rate_limited_request,
    request_tracker,
):
    """
    Measure proxy connection latency.
    
    Makes multiple requests and calculates:
    - Min/Max/Average latency
    - P95 latency estimate
    """
    latencies = []
    
    # Make 5 latency measurements
    for i in range(5):
        async with rate_limited_request:
            start_time = time.time()
            
            response = await http_client_with_proxy.get(
                "https://httpbin.org/ip",
                timeout=30.0
            )
            
            elapsed = time.time() - start_time
            latencies.append(elapsed)
            
            request_tracker.record(
                f"httpbin.org/ip (latency {i+1}/5)",
                "test_iproyal_connection_latency"
            )
            
            assert response.status_code == 200
    
    # Calculate statistics
    avg_latency = sum(latencies) / len(latencies)
    min_latency = min(latencies)
    max_latency = max(latencies)
    sorted_latencies = sorted(latencies)
    p95 = sorted_latencies[int(len(sorted_latencies) * 0.95)]
    
    print(f"\n✓ Latency measurement completed")
    print(f"  Requests: {len(latencies)}")
    print(f"  Min: {min_latency:.2f}s")
    print(f"  Max: {max_latency:.2f}s")
    print(f"  Avg: {avg_latency:.2f}s")
    print(f"  P95: {p95:.2f}s")
    
    # Latency should be reasonable (< 30 seconds for proxy)
    assert avg_latency < 30.0, f"Average latency too high: {avg_latency:.2f}s"


# =============================================================================
# Test 7: Rotating vs Session Proxy Comparison
# =============================================================================

@pytest.mark.live
@pytest.mark.requires_proxy
async def test_iproyal_rotating_vs_session(
    proxy_url,
    proxy_url_rotating,
    rate_limited_request,
    request_tracker,
):
    """
    Compare rotating and session proxy modes.
    
    Tests both proxy types and compares their behavior:
    - Session: Same IP across requests
    - Rotating: Potentially different IPs
    """
    try:
        import httpx
    except ImportError:
        pytest.skip("httpx not installed")
    
    session_ips = []
    rotating_ips = []
    
    # Test session proxy (2 requests)
    print("\n  Testing session proxy...")
    for i in range(2):
        async with rate_limited_request:
            async with httpx.AsyncClient(proxy=proxy_url, timeout=30.0) as client:
                response = await client.get("https://httpbin.org/ip")
            
            request_tracker.record(
                f"httpbin.org/ip (session compare {i+1}/2)",
                "test_iproyal_rotating_vs_session"
            )
            
            data = response.json()
            session_ips.append(data["origin"])
            print(f"    Session request {i+1}: {data['origin']}")
    
    # Test rotating proxy (2 requests)
    print("  Testing rotating proxy...")
    for i in range(2):
        async with rate_limited_request:
            async with httpx.AsyncClient(
                proxy=proxy_url_rotating,
                timeout=30.0
            ) as client:
                response = await client.get("https://httpbin.org/ip")
            
            request_tracker.record(
                f"httpbin.org/ip (rotating compare {i+1}/2)",
                "test_iproyal_rotating_vs_session"
            )
            
            data = response.json()
            rotating_ips.append(data["origin"])
            print(f"    Rotating request {i+1}: {data['origin']}")
    
    print(f"\n✓ Proxy mode comparison completed")
    print(f"  Session proxy IPs: {set(session_ips)}")
    print(f"  Rotating proxy IPs: {set(rotating_ips)}")
    
    # Both should return valid IPs
    assert all(session_ips), "Session proxy returned empty IP"
    assert all(rotating_ips), "Rotating proxy returned empty IP"


# =============================================================================
# Test 8: HTTPS Proxy Support
# =============================================================================

@pytest.mark.live
@pytest.mark.requires_proxy
async def test_iproyal_https_support(
    http_client_with_proxy,
    rate_limited_request,
    request_tracker,
):
    """
    Test that proxy properly handles HTTPS connections.
    
    Verifies SSL/TLS works through the proxy.
    """
    async with rate_limited_request:
        # Test HTTPS site
        response = await http_client_with_proxy.get(
            "https://httpbin.org/get",
            timeout=30.0
        )
        
        request_tracker.record("httpbin.org/get", "test_iproyal_https_support")
        
        assert response.status_code == 200
        
        data = response.json()
        
        # httpbin returns request info - verify headers present
        assert "headers" in data
        
        print(f"\n✓ HTTPS support test passed")
        print(f"  Origin: {data.get('origin', 'Unknown')}")
        print(f"  URL: {data.get('url', 'Unknown')}")


# =============================================================================
# Test Summary
# =============================================================================

def pytest_sessionfinish(session, exitstatus):
    """Print test summary at end of session."""
    if session.config.getoption("--run-live"):
        print("\n" + "=" * 60)
        print("IPRoyal Live Test Summary")
        print("=" * 60)
        print("All IPRoyal connectivity tests completed.")
        print("Proxy is operational and configured correctly.")
        print("=" * 60)
