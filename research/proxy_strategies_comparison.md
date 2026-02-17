# Advanced Proxy Rotation Strategies for TikTok Scraping

**Research Date:** February 2026  
**Focus:** Avoiding TikTok's IP-based detection systems  
**Current Situation:** Single residential IP from IPRoyal still triggers CAPTCHAs

---

## Executive Summary

TikTok employs multi-layered anti-scraping defenses including IP reputation scoring, TLS fingerprinting (JA3/JA4), behavioral analysis, and request fingerprinting. Single residential IPs—even from quality providers—will eventually trigger detection due to:

- Request pattern analysis (too consistent)
- IP velocity checks (same IP, many requests)
- TLS fingerprint mismatches
- Behavioral inconsistencies

**Key Finding:** IP rotation alone is insufficient. Success requires combining rotation strategies with browser fingerprinting, session management, and intelligent request patterns.

---

## 1. Rotating vs Sticky Sessions

### 1.1 Understanding the Trade-offs

| Aspect | Rotating Proxies | Sticky Sessions |
|--------|------------------|-----------------|
| **IP Persistence** | New IP per request or interval | Same IP for session duration |
| **Best For** | High-volume distributed scraping | Account management, login sessions |
| **TikTok Risk** | Lower (harder to track) | Higher (pattern detection) |
| **Session State** | Lost per rotation | Maintained across requests |
| **Cost Efficiency** | May waste IPs on failed requests | Better success rate per IP |

### 1.2 IPRoyal Configuration Options

**Rotating Mode:**
```python
# IPRoyal rotating proxy endpoint
PROXY_HOST = "geo.iproyal.com"
PROXY_PORT = 12321
PROXY_USER = "your_username"
PROXY_PASS = "your_password"

# Format: username:password@host:port
proxy = f"http://{PROXY_USER}:{PROXY_PASS}@{PROXY_HOST}:{PROXY_PORT}"

# Auto-rotation options:
# - Every request (default)
# - Time-based: 1, 10, or 30 minutes
# - Manual via API call
```

**Sticky Session Mode:**
```python
# Add session ID to username for sticky sessions
# Format: username_session-session_id
session_id = "abc123xyz"  # Generate unique session ID
sticky_proxy = f"http://{PROXY_USER}_session-{session_id}:{PROXY_PASS}@{PROXY_HOST}:{PROXY_PORT}"

# Session persists until:
# - Explicitly closed
# - Timeout (configurable, up to 30 mins on IPRoyal)
# - IP becomes unavailable
```

### 1.3 Optimal Request-per-IP Ratios for TikTok

Based on research and testing data:

| Proxy Type | Safe Requests/IP | Optimal Session Duration | Rotation Trigger |
|------------|------------------|-------------------------|------------------|
| Datacenter | 3-5 requests | Immediate per-request | 403/captcha |
| Residential (Rotating) | 10-20 requests | 5-10 minutes | Error rate > 20% |
| Residential (Sticky) | 15-30 requests | 15-30 minutes | Captcha/block |
| Mobile (4G/5G) | 30-50 requests | 30-60 minutes | Account action |
| ISP (Static) | 50-100+ requests | Hours to days | Manual review |

**Recommendation for TikTok:**
- Use sticky sessions with 10-20 requests per IP
- Rotate on captcha/403 detection
- Maintain session for account-related actions (login, posting)
- Rotate for discovery/scraping actions

### 1.4 When to Rotate vs Keep Session

**Rotate Immediately:**
- Public content scraping (videos, profiles without login)
- Search and discovery operations
- After receiving 403/ captcha response
- When error rate exceeds threshold (20%)

**Keep Session:**
- Logged-in operations
- Multi-step workflows (add to cart, checkout)
- Account management
- After successful authentication

### 1.5 Implementation: Smart Session Manager

```python
import time
import random
import requests
from dataclasses import dataclass, field
from typing import Optional, List, Dict
from datetime import datetime, timedelta

@dataclass
class SessionMetrics:
    ip: str
    created_at: datetime
    request_count: int = 0
    error_count: int = 0
    last_used: datetime = field(default_factory=datetime.now)
    
    @property
    def error_rate(self) -> float:
        if self.request_count == 0:
            return 0.0
        return self.error_count / self.request_count
    
    @property
    def age_minutes(self) -> float:
        return (datetime.now() - self.created_at).total_seconds() / 60

class SmartProxyRotator:
    """
    Intelligent proxy rotation with session persistence and error-based switching.
    """
    
    def __init__(
        self,
        proxy_list: List[str],
        max_requests_per_ip: int = 20,
        max_session_minutes: float = 30,
        max_error_rate: float = 0.2,
        sticky_for_domains: Optional[List[str]] = None
    ):
        self.proxy_list = proxy_list
        self.max_requests = max_requests_per_ip
        self.max_session_minutes = max_session_minutes
        self.max_error_rate = max_error_rate
        self.sticky_for_domains = sticky_for_domains or []
        
        # Session management
        self.sessions: Dict[str, SessionMetrics] = {}
        self.current_proxy_idx = 0
        self.domain_sessions: Dict[str, str] = {}  # domain -> proxy mapping
        
    def _get_next_proxy(self) -> str:
        """Round-robin proxy selection."""
        proxy = self.proxy_list[self.current_proxy_idx]
        self.current_proxy_idx = (self.current_proxy_idx + 1) % len(self.proxy_list)
        return proxy
    
    def get_proxy(self, domain: Optional[str] = None) -> str:
        """
        Get appropriate proxy for request.
        
        Args:
            domain: Target domain (for sticky session decisions)
            
        Returns:
            Proxy URL to use
        """
        # Check if domain requires sticky session
        if domain and any(d in domain for d in self.sticky_for_domains):
            return self._get_sticky_proxy(domain)
        
        # Get fresh rotating proxy
        return self._get_fresh_proxy()
    
    def _get_sticky_proxy(self, domain: str) -> str:
        """Get or create sticky session for domain."""
        if domain in self.domain_sessions:
            proxy = self.domain_sessions[domain]
            metrics = self.sessions.get(proxy)
            
            # Check if session is still valid
            if metrics and self._is_session_valid(metrics):
                metrics.request_count += 1
                metrics.last_used = datetime.now()
                return proxy
        
        # Create new session
        proxy = self._get_next_proxy()
        self.domain_sessions[domain] = proxy
        self.sessions[proxy] = SessionMetrics(
            ip=proxy,
            created_at=datetime.now()
        )
        return proxy
    
    def _get_fresh_proxy(self) -> str:
        """Get fresh proxy for rotating mode."""
        proxy = self._get_next_proxy()
        
        # Initialize or reset metrics
        self.sessions[proxy] = SessionMetrics(
            ip=proxy,
            created_at=datetime.now()
        )
        return proxy
    
    def _is_session_valid(self, metrics: SessionMetrics) -> bool:
        """Check if current session should continue."""
        # Check request count
        if metrics.request_count >= self.max_requests:
            return False
        
        # Check session age
        if metrics.age_minutes >= self.max_session_minutes:
            return False
        
        # Check error rate
        if metrics.error_rate >= self.max_error_rate:
            return False
        
        return True
    
    def report_result(self, proxy: str, success: bool):
        """Report request result for metrics tracking."""
        if proxy in self.sessions:
            self.sessions[proxy].request_count += 1
            if not success:
                self.sessions[proxy].error_count += 1
    
    def force_rotate(self, domain: Optional[str] = None):
        """Force rotation for domain or global."""
        if domain and domain in self.domain_sessions:
            del self.domain_sessions[domain]
        else:
            self.sessions.clear()
            self.domain_sessions.clear()


# Usage Example
proxy_list = [
    "http://user1:pass1@geo.iproyal.com:12321",
    "http://user2:pass2@proxy.webshare.io:80",
    # ... more proxies
]

rotator = SmartProxyRotator(
    proxy_list=proxy_list,
    max_requests_per_ip=15,
    max_session_minutes=20,
    sticky_for_domains=["tiktok.com", "accounts.tiktok.com"]
)

# Make request with smart rotation
def make_request(url: str):
    domain = url.split('/')[2]
    proxy = rotator.get_proxy(domain)
    
    try:
        response = requests.get(
            url,
            proxies={"http": proxy, "https": proxy},
            timeout=30,
            headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
        )
        
        # Check for blocking indicators
        is_blocked = response.status_code in [403, 429] or "captcha" in response.text.lower()
        rotator.report_result(proxy, not is_blocked)
        
        if is_blocked:
            rotator.force_rotate(domain)
            # Retry with new proxy
            return make_request(url)
        
        return response
        
    except Exception as e:
        rotator.report_result(proxy, False)
        raise
```

### 1.6 Cost Estimates: IPRoyal

| Plan Type | Price | Traffic | Effective Cost |
|-----------|-------|---------|----------------|
| **Pay As You Go** | $7/GB | 1GB | $7.00/GB |
| **Starter** | $12.50/mo | 2GB | $6.25/GB |
| **Business** | $80/mo | 15GB | $5.33/GB |
| **Enterprise** | $250/mo | 50GB | $5.00/GB |
| **Custom** | $1.75/GB | 1000GB+ | $1.75/GB |

*Note: IPRoyal offers non-expiring traffic with pay-as-you-go options*

---

## 2. Multiple Proxy Providers Strategy

### 2.1 Provider Comparison Matrix

| Provider | Residential Price | Mobile Price | ISP Price | Pool Size | Key Strength |
|----------|-------------------|--------------|-----------|-----------|--------------|
| **IPRoyal** | $1.75-7/GB | $80-150/mo (unlimited) | $2/IP/day | 32M+ | Budget-friendly, flexible |
| **Oxylabs** | $8-10/GB | $20-25/GB | N/A | 100M+ | Large pool, enterprise |
| **Bright Data** | $6.6-15/GB | ~$60/GB | $0.60-1.20/IP | 72M+ | Premium, city-level targeting |
| **Webshare** | $4.50-7/GB | N/A | N/A | 30M+ | Good balance, rotating endpoints |
| **SOAX** | $6.60-12/GB | $150-300/mo | N/A | 155M+ | Clean pool, precise targeting |
| **Smartproxy** | $7-12/GB | N/A | $2.50/IP | 55M+ | User-friendly, good docs |

### 2.2 Load Balancing Across Providers

**Why Multi-Provider:**
- No single point of failure
- Different IP pools = different detection profiles
- Cost optimization (use cheaper for low-risk, premium for high-risk)
- Geographic coverage variations

**Implementation: Multi-Provider Proxy Pool**

```python
import random
import hashlib
from dataclasses import dataclass
from typing import List, Dict, Optional
from enum import Enum

class ProviderTier(Enum):
    PREMIUM = "premium"      # Bright Data, Oxylabs - for high-risk
    STANDARD = "standard"    # IPRoyal, Smartproxy - general use
    BUDGET = "budget"        # Webshare, PacketStream - discovery

@dataclass
class Provider:
    name: str
    tier: ProviderTier
    proxy_endpoint: str
    weight: float = 1.0  # Load balancing weight
    current_failure_rate: float = 0.0
    cost_per_gb: float = 0.0

class MultiProviderProxyManager:
    """
    Load balance across multiple proxy providers with intelligent routing.
    """
    
    def __init__(self):
        self.providers: Dict[str, Provider] = {}
        self.failure_windows: Dict[str, List[float]] = {}  # Recent failure tracking
        
    def register_provider(self, provider: Provider):
        """Add a proxy provider to the pool."""
        self.providers[provider.name] = provider
        self.failure_windows[provider.name] = []
    
    def select_provider(
        self,
        priority: Optional[ProviderTier] = None,
        target_domain: Optional[str] = None
    ) -> str:
        """
        Select best provider based on tier, health, and weights.
        
        Args:
            priority: Preferred tier level
            target_domain: Domain being accessed (for sticky routing)
        
        Returns:
            Provider name
        """
        candidates = list(self.providers.values())
        
        # Filter by tier if specified
        if priority:
            candidates = [p for p in candidates if p.tier == priority]
        
        if not candidates:
            candidates = list(self.providers.values())
        
        # Calculate selection weights based on health and base weight
        weights = []
        for provider in candidates:
            # Reduce weight based on failure rate
            health_factor = 1 - provider.current_failure_rate
            effective_weight = provider.weight * health_factor
            weights.append(max(effective_weight, 0.1))  # Min weight
        
        # Weighted random selection
        selected = random.choices(candidates, weights=weights, k=1)[0]
        return selected.name
    
    def get_proxy(
        self,
        priority: Optional[ProviderTier] = None,
        target_domain: Optional[str] = None
    ) -> str:
        """Get proxy URL from selected provider."""
        provider_name = self.select_provider(priority, target_domain)
        provider = self.providers[provider_name]
        return provider.proxy_endpoint
    
    def report_result(self, provider_name: str, success: bool):
        """Report success/failure for provider health tracking."""
        if provider_name not in self.providers:
            return
        
        window = self.failure_windows[provider_name]
        window.append(0.0 if success else 1.0)
        
        # Keep only last 100 results
        if len(window) > 100:
            window.pop(0)
        
        # Update failure rate
        if window:
            self.providers[provider_name].current_failure_rate = sum(window) / len(window)
    
    def get_cost_optimized_proxy(self, risk_level: str = "medium") -> str:
        """
        Select proxy optimized for cost based on risk level.
        
        Args:
            risk_level: "low", "medium", "high"
        """
        if risk_level == "low":
            # Use budget providers for discovery
            return self.get_proxy(priority=ProviderTier.BUDGET)
        elif risk_level == "medium":
            # Use standard providers
            return self.get_proxy(priority=ProviderTier.STANDARD)
        else:
            # Use premium for critical operations
            return self.get_proxy(priority=ProviderTier.PREMIUM)


# Setup example
manager = MultiProviderProxyManager()

# Budget provider for initial discovery
manager.register_provider(Provider(
    name="webshare",
    tier=ProviderTier.BUDGET,
    proxy_endpoint="http://user:pass@proxy.webshare.io:80",
    weight=2.0,
    cost_per_gb=4.5
))

# Standard provider for general scraping
manager.register_provider(Provider(
    name="iproyal",
    tier=ProviderTier.STANDARD,
    proxy_endpoint="http://user:pass@geo.iproyal.com:12321",
    weight=3.0,
    cost_per_gb=5.0
))

# Premium provider for TikTok (high detection)
manager.register_provider(Provider(
    name="brightdata",
    tier=ProviderTier.PREMIUM,
    proxy_endpoint="http://user:pass@brd.superproxy.io:22225",
    weight=1.0,
    cost_per_gb=10.0
))
```

### 2.3 Failover Strategies

```python
import requests
from functools import wraps
from typing import Callable, Optional
import time

class ProxyFailoverHandler:
    """
    Automatic failover between providers with circuit breaker pattern.
    """
    
    def __init__(
        self,
        providers: List[str],
        max_retries: int = 3,
        circuit_threshold: int = 5,
        circuit_timeout: int = 60
    ):
        self.providers = providers
        self.max_retries = max_retries
        self.circuit_threshold = circuit_threshold
        self.circuit_timeout = circuit_timeout
        
        # Circuit breaker state
        self.failure_counts: Dict[str, int] = {p: 0 for p in providers}
        self.circuit_open: Dict[str, Optional[float]] = {p: None for p in providers}
    
    def _is_circuit_closed(self, provider: str) -> bool:
        """Check if circuit breaker allows requests."""
        open_time = self.circuit_open[provider]
        if open_time is None:
            return True
        
        # Check if timeout has passed
        if time.time() - open_time > self.circuit_timeout:
            self.circuit_open[provider] = None
            self.failure_counts[provider] = 0
            return True
        
        return False
    
    def _record_failure(self, provider: str):
        """Record failure and potentially open circuit."""
        self.failure_counts[provider] += 1
        
        if self.failure_counts[provider] >= self.circuit_threshold:
            self.circuit_open[provider] = time.time()
            print(f"Circuit opened for {provider}")
    
    def _record_success(self, provider: str):
        """Reset failure count on success."""
        self.failure_counts[provider] = max(0, self.failure_counts[provider] - 1)
    
    def execute_with_failover(
        self,
        request_func: Callable,
        *args,
        **kwargs
    ) -> requests.Response:
        """
        Execute request with automatic provider failover.
        
        Args:
            request_func: Function that makes the actual request
            *args, **kwargs: Arguments for request_func
        """
        last_exception = None
        
        for attempt in range(self.max_retries):
            # Get available providers (circuit closed)
            available = [p for p in self.providers if self._is_circuit_closed(p)]
            
            if not available:
                # All circuits open, wait and retry
                time.sleep(self.circuit_timeout)
                available = self.providers
            
            # Try each available provider
            for provider in available:
                try:
                    # Inject provider into request
                    kwargs['proxy'] = provider
                    response = request_func(*args, **kwargs)
                    
                    # Check for blocking
                    if response.status_code < 400:
                        self._record_success(provider)
                        return response
                    else:
                        self._record_failure(provider)
                        last_exception = Exception(f"HTTP {response.status_code}")
                        
                except Exception as e:
                    self._record_failure(provider)
                    last_exception = e
                    continue
        
        raise last_exception or Exception("All providers failed")


# Usage with requests
def make_tiktok_request(url: str, proxy: str, **kwargs) -> requests.Response:
    """Wrapper for TikTok requests."""
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9",
        "Accept-Encoding": "gzip, deflate, br",
        "DNT": "1",
        "Connection": "keep-alive",
    }
    
    return requests.get(
        url,
        proxies={"http": proxy, "https": proxy},
        headers=headers,
        timeout=30,
        **kwargs
    )

# Setup failover handler
failover = ProxyFailoverHandler([
    "http://user1:pass1@geo.iproyal.com:12321",
    "http://user2:pass2@brd.superproxy.io:22225",
    "http://user3:pass3@proxy.webshare.io:80",
])

# Execute with automatic failover
response = failover.execute_with_failover(
    make_tiktok_request,
    "https://www.tiktok.com/@username"
)
```

### 2.4 Cost Optimization Formula

```python
class CostOptimizer:
    """
    Optimize proxy costs based on traffic patterns and success rates.
    """
    
    def __init__(self):
        self.usage_stats: Dict[str, Dict] = {}
    
    def calculate_optimal_mix(
        self,
        monthly_gb: float,
        tiktok_percentage: float = 0.3  # 30% high-risk traffic
    ) -> Dict[str, float]:
        """
        Calculate optimal provider mix for cost efficiency.
        
        Returns allocation percentages by provider tier.
        """
        tiktok_gb = monthly_gb * tiktok_percentage
        other_gb = monthly_gb - tiktok_gb
        
        # For TikTok: Mix of mobile (high trust) and premium residential
        tiktok_allocation = {
            "mobile": tiktok_gb * 0.6,      # 60% mobile for high trust
            "premium_residential": tiktok_gb * 0.4,  # 40% premium residential
        }
        
        # For other sites: Standard residential (sufficient)
        other_allocation = {
            "standard_residential": other_gb
        }
        
        # Cost estimates (per GB)
        costs = {
            "mobile": 25.0,              # $25/GB average
            "premium_residential": 10.0,  # $10/GB
            "standard_residential": 5.0,  # $5/GB
        }
        
        total_cost = (
            tiktok_allocation["mobile"] * costs["mobile"] +
            tiktok_allocation["premium_residential"] * costs["premium_residential"] +
            other_allocation["standard_residential"] * costs["standard_residential"]
        )
        
        return {
            "allocations": {**tiktok_allocation, **other_allocation},
            "estimated_monthly_cost": total_cost,
            "cost_per_gb": total_cost / monthly_gb
        }


# Example: 100GB monthly traffic
optimizer = CostOptimizer()
result = optimizer.calculate_optimal_mix(monthly_gb=100, tiktok_percentage=0.4)
print(f"Estimated cost: ${result['estimated_monthly_cost']:.2f}/month")
print(f"Effective cost: ${result['cost_per_gb']:.2f}/GB")
```

---

## 3. Mobile Proxies (4G/5G)

### 3.1 Why Mobile Proxies Have Higher Trust

Mobile proxies use IP addresses from cellular carriers (4G/5G/LTE), which provide:

| Factor | Mobile Proxy Advantage |
|--------|----------------------|
| **IP Rotation** | NAT-based automatic rotation (carrier-level) |
| **Trust Score** | 95-99% (highest) - real user behavior |
| **Detection Evasion** | Harder to distinguish from real mobile users |
| **CAPTCHA Rate** | Significantly lower than residential |
| **Blacklist Status** | Rarely flagged due to dynamic allocation |

**Technical Reason:** Mobile IPs use CGNAT (Carrier-Grade NAT), where hundreds/thousands of real users share the same public IP. Blocking a mobile IP would block many legitimate users, so platforms are more lenient.

### 3.2 Mobile Proxy Providers Comparison

| Provider | Type | Price | Locations | Notes |
|----------|------|-------|-----------|-------|
| **IPRoyal** | Rotating 4G/5G | $80-150/mo (unlimited) | US, UK, EU | Best value unlimited |
| **Oxylabs** | 4G/5G | $20-25/GB | 140+ countries | Premium quality |
| **TheSocialProxy** | Dedicated 4G | $129-299/mo | US, UK, EU | Specialized for social |
| **ProxyEmpire** | Rotating 4G | $150-300/mo | 21+ countries | Good targeting |
| **SOAX** | 4G/5G | $330/mo (unlimited) | Global | Clean pool |
| **Rayobyte** | 4G/5G | $75-125/mo | US | Budget option |

### 3.3 Cost Comparison: Mobile vs Other Types

| Proxy Type | Cost per GB | Cost per Month | Best For |
|------------|-------------|----------------|----------|
| Datacenter | $0.50-2 | $50-100 | Non-sensitive scraping |
| Residential (Rotating) | $5-15 | $100-500 | General use |
| **Mobile (4G/5G)** | **$10-30** | **$100-300** | **TikTok, social media** |
| ISP (Static) | $2-5 | $50-150 | Account management |

**Value Proposition for TikTok:**
- Mobile proxies cost 2-3x residential but offer 5-10x lower detection rates
- For TikTok specifically, mobile proxies often pay for themselves through higher success rates

### 3.4 Effectiveness for TikTok

Based on research and user reports:

| Metric | Datacenter | Residential | Mobile (4G/5G) |
|--------|------------|-------------|----------------|
| Success Rate | 10-30% | 60-80% | 85-95% |
| CAPTCHA Rate | 70%+ | 20-40% | 5-15% |
| Account Ban Risk | Very High | Medium | Low |
| Session Duration | < 5 min | 10-30 min | 30-60 min |

**Recommendation:** For TikTok specifically, mobile proxies are worth the premium due to the platform's aggressive anti-bot detection.

### 3.5 Implementation: Mobile Proxy Integration

```python
class MobileProxyManager:
    """
    Manager for mobile proxy connections with session optimization.
    """
    
    def __init__(
        self,
        proxy_url: str,
        session_duration: int = 1800,  # 30 minutes default
        rotate_on_block: bool = True
    ):
        self.proxy_url = proxy_url
        self.session_duration = session_duration
        self.rotate_on_block = rotate_on_block
        
        self.session_start: Optional[float] = None
        self.request_count = 0
    
    def get_connection(self) -> str:
        """Get mobile proxy connection with session management."""
        current_time = time.time()
        
        # Check if session should rotate
        if self.session_start:
            session_age = current_time - self.session_start
            if session_age > self.session_duration:
                self.rotate_session()
        
        if not self.session_start:
            self.session_start = current_time
        
        self.request_count += 1
        return self.proxy_url
    
    def rotate_session(self):
        """Force session rotation."""
        self.session_start = time.time()
        self.request_count = 0
        
        # For IPRoyal mobile: session rotation happens automatically
        # For others: may need API call
        print("Mobile proxy session rotated")
    
    def report_block(self):
        """Report a block/captcha for immediate rotation."""
        if self.rotate_on_block:
            self.rotate_session()


# IPRoyal Mobile Proxy Configuration
IPROYAL_MOBILE_CONFIG = {
    "proxy_host": "geo.iproyal.com",
    "proxy_port": 12321,
    "username": "your_username",
    "password": "your_password",
    
    # Session settings
    "sticky_session": True,  # Keep same IP for session
    "session_duration": 1800,  # 30 minutes
    
    # IPRoyal mobile features:
    # - Unlimited bandwidth
    # - Auto-rotation on interval
    # - Carrier selection available
}

# Usage
mobile_proxy = f"http://{IPROYAL_MOBILE_CONFIG['username']}:{IPROYAL_MOBILE_CONFIG['password']}@{IPROYAL_MOBILE_CONFIG['proxy_host']}:{IPROYAL_MOBILE_CONFIG['proxy_port']}"

manager = MobileProxyManager(
    proxy_url=mobile_proxy,
    session_duration=1800
)
```

---

## 4. ISP Proxies (Static Residential)

### 4.1 When Static is Better Than Rotating

ISP proxies (also called "static residential") are hosted in datacenters but registered with ISPs:

| Scenario | Use Static ISP | Use Rotating |
|----------|---------------|--------------|
| **Account Management** | ✓ Multiple accounts per IP | ✗ IPs change unpredictably |
| **Long Sessions** | ✓ Hours to days | ✗ Minutes only |
| **Login Persistence** | ✓ Consistent identity | ✗ Cookies invalidated |
| **Price Monitoring** | ✓ Same "shopper" profile | ✗ Location inconsistency |
| **High-Volume Scraping** | ✗ Rate limit issues | ✓ Distribute load |

### 4.2 ISP Proxy Providers

| Provider | Price/IP | Locations | Speed |
|----------|----------|-----------|-------|
| **IPRoyal** | $2.00/day | US, UK, EU | 1 Gbps |
| **Bright Data** | $0.60/day (bulk) | 195 countries | High |
| **Oxylabs** | $2.50/day | Global | High |
| **Smartproxy** | $2.50/day | US, EU | 1 Gbps |
| **Webshare** | $1.80/day | 10+ countries | Good |
| **Rayobyte** | $1.00/day | US | Good |

### 4.3 TikTok-Specific Considerations for ISP

ISP proxies work for TikTok but with caveats:

**Advantages:**
- Lower cost than mobile
- Consistent location
- No rotation-related session loss

**Disadvantages:**
- More likely to be flagged than mobile
- Static nature makes pattern detection easier
- Not recommended for bulk discovery

**Best Practice for TikTok:**
- Use ISP proxies for account management (logged-in operations)
- Use mobile/rotating residential for discovery/scraping
- Limit ISP proxy to 50-100 requests per day per IP

### 4.4 Implementation: Hybrid Static/Rotating

```python
class HybridProxyManager:
    """
    Combine ISP (static) and rotating proxies for optimal TikTok workflow.
    """
    
    def __init__(
        self,
        isp_proxies: List[str],      # For account management
        rotating_proxies: List[str],  # For discovery
    ):
        self.isp_pool = isp_proxies
        self.rotating_pool = rotating_proxies
        
        # Track ISP proxy health
        self.isp_usage: Dict[str, Dict] = {
            proxy: {"daily_requests": 0, "last_reset": time.time()}
            for proxy in isp_proxies
        }
    
    def get_proxy_for_action(self, action: str, account_id: Optional[str] = None) -> str:
        """
        Get appropriate proxy based on action type.
        
        Args:
            action: Type of action ("login", "scrape", "discover", "post")
            account_id: Account identifier for sticky ISP assignment
        """
        if action in ["login", "account_manage"]:
            # Use ISP for account operations
            return self._get_isp_proxy(account_id)
        
        elif action == "scrape":
            # Use rotating for scraping
            return random.choice(self.rotating_pool)
        
        elif action == "discover":
            # High-rotation for discovery
            return self._get_high_rotation_proxy()
        
        else:
            # Default to rotating
            return random.choice(self.rotating_pool)
    
    def _get_isp_proxy(self, account_id: Optional[str] = None) -> str:
        """Get ISP proxy, optionally sticky by account."""
        if account_id:
            # Hash account to consistent ISP
            idx = hash(account_id) % len(self.isp_pool)
            return self.isp_pool[idx]
        
        # Find least-used ISP
        return min(self.isp_pool, 
                   key=lambda p: self.isp_usage[p]["daily_requests"])
    
    def _get_high_rotation_proxy(self) -> str:
        """Get proxy optimized for rapid rotation."""
        # Use premium rotating with per-request rotation
        return random.choice(self.rotating_pool)
    
    def reset_daily_counters(self):
        """Reset daily usage counters."""
        current_time = time.time()
        for proxy in self.isp_usage:
            self.isp_usage[proxy]["daily_requests"] = 0
            self.isp_usage[proxy]["last_reset"] = current_time


# Configuration
HYBRID_CONFIG = {
    "isp_proxies": [
        "http://user:pass@isp1.iproyal.com:12321",
        "http://user:pass@isp2.iproyal.com:12321",
    ],
    "rotating_proxies": [
        "http://user:pass@geo.iproyal.com:12321",
        "http://user:pass@brd.superproxy.io:22225",
    ]
}

hybrid = HybridProxyManager(
    isp_proxies=HYBRID_CONFIG["isp_proxies"],
    rotating_proxies=HYBRID_CONFIG["rotating_proxies"]
)

# Usage examples
login_proxy = hybrid.get_proxy_for_action("login", account_id="user123")
scrape_proxy = hybrid.get_proxy_for_action("scrape")
discover_proxy = hybrid.get_proxy_for_action("discover")
```

---

## 5. Proxy Rotation Algorithms

### 5.1 Algorithm Comparison

| Algorithm | Description | Best For | TikTok Suitability |
|-----------|-------------|----------|-------------------|
| **Round-Robin** | Cycle through sequentially | Balanced load distribution | Good |
| **Random** | Random selection | Avoiding patterns | Good |
| **Weighted** | Based on speed/success | Optimizing for performance | Better |
| **Error-Based** | Rotate on errors/captchas | Adaptive to blocking | Better |
| **Rate-Limit-Based** | Rotate when approaching limits | Precise control | Best |
| **Session-Based** | Persistent per domain | Account management | Best for login |

### 5.2 Intelligent Rotation Implementation

```python
import time
import random
import statistics
from collections import deque
from typing import Dict, List, Deque, Optional
from dataclasses import dataclass, field
from datetime import datetime

@dataclass
class ProxyMetrics:
    """Track detailed metrics for each proxy."""
    proxy: str
    total_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    captcha_encounters: int = 0
    avg_response_time: float = 0.0
    last_used: Optional[datetime] = None
    cooldown_until: Optional[float] = None
    response_times: Deque[float] = field(default_factory=lambda: deque(maxlen=50))
    
    @property
    def success_rate(self) -> float:
        if self.total_requests == 0:
            return 1.0
        return self.successful_requests / self.total_requests
    
    @property
    def is_available(self) -> bool:
        if self.cooldown_until is None:
            return True
        return time.time() > self.cooldown_until
    
    def update_response_time(self, duration: float):
        self.response_times.append(duration)
        self.avg_response_time = statistics.mean(self.response_times)


class IntelligentProxyRotator:
    """
    Advanced proxy rotator with multiple algorithms and adaptive selection.
    """
    
    ALGORITHMS = ["round_robin", "weighted", "adaptive", "least_connections"]
    
    def __init__(
        self,
        proxies: List[str],
        algorithm: str = "adaptive",
        cooldown_seconds: int = 300,
        max_failures_before_cooldown: int = 3
    ):
        self.proxies = proxies
        self.algorithm = algorithm
        self.cooldown_seconds = cooldown_seconds
        self.max_failures = max_failures_before_cooldown
        
        # Metrics tracking
        self.metrics: Dict[str, ProxyMetrics] = {
            proxy: ProxyMetrics(proxy=proxy) for proxy in proxies
        }
        
        # Round-robin state
        self.rr_index = 0
        
        # Active connections tracking
        self.active_connections: Dict[str, int] = {proxy: 0 for proxy in proxies}
    
    def get_proxy(self) -> str:
        """Get proxy using selected algorithm."""
        if self.algorithm == "round_robin":
            return self._round_robin()
        elif self.algorithm == "weighted":
            return self._weighted_selection()
        elif self.algorithm == "adaptive":
            return self._adaptive_selection()
        elif self.algorithm == "least_connections":
            return self._least_connections()
        else:
            return self._adaptive_selection()
    
    def _round_robin(self) -> str:
        """Simple round-robin selection."""
        available = [p for p in self.proxies if self.metrics[p].is_available]
        
        if not available:
            # All proxies in cooldown, pick least recent
            return min(self.proxies, 
                      key=lambda p: self.metrics[p].cooldown_until or 0)
        
        # Get next in rotation
        for _ in range(len(available)):
            proxy = available[self.rr_index % len(available)]
            self.rr_index = (self.rr_index + 1) % len(available)
            if self.metrics[proxy].is_available:
                return proxy
        
        return available[0]
    
    def _weighted_selection(self) -> str:
        """Weighted selection based on success rate and response time."""
        available = [p for p in self.proxies if self.metrics[p].is_available]
        
        if not available:
            available = self.proxies
        
        # Calculate weights
        weights = []
        for proxy in available:
            m = self.metrics[proxy]
            # Higher success rate = higher weight
            # Lower response time = higher weight
            weight = m.success_rate * (1 / (1 + m.avg_response_time))
            weights.append(max(weight, 0.1))
        
        return random.choices(available, weights=weights, k=1)[0]
    
    def _adaptive_selection(self) -> str:
        """
        Adaptive selection combining multiple factors.
        Considers: success rate, recent performance, cooldown status.
        """
        scores = []
        
        for proxy in self.proxies:
            m = self.metrics[proxy]
            
            # Base score from success rate (0-1)
            score = m.success_rate
            
            # Penalty for recent failures
            recent_failures = m.failed_requests - m.successful_requests
            if recent_failures > 0:
                score *= (0.9 ** recent_failures)
            
            # Penalty if in cooldown
            if not m.is_available:
                remaining = m.cooldown_until - time.time()
                score *= (0.5 ** (remaining / 60))  # Decay over time
            
            # Bonus for fast response times
            if m.avg_response_time < 2.0:
                score *= 1.1
            
            scores.append((proxy, score))
        
        # Normalize and select
        total_score = sum(s for _, s in scores)
        if total_score == 0:
            return random.choice(self.proxies)
        
        weights = [s / total_score for _, s in scores]
        proxies = [p for p, _ in scores]
        
        return random.choices(proxies, weights=weights, k=1)[0]
    
    def _least_connections(self) -> str:
        """Select proxy with fewest active connections."""
        available = [p for p in self.proxies if self.metrics[p].is_available]
        
        if not available:
            available = self.proxies
        
        return min(available, key=lambda p: self.active_connections[p])
    
    def report_request_start(self, proxy: str):
        """Track active connection."""
        self.active_connections[proxy] += 1
        self.metrics[proxy].last_used = datetime.now()
    
    def report_request_end(
        self,
        proxy: str,
        success: bool,
        response_time: float,
        captcha: bool = False
    ):
        """Report request completion with metrics."""
        self.active_connections[proxy] = max(0, self.active_connections[proxy] - 1)
        
        m = self.metrics[proxy]
        m.total_requests += 1
        m.update_response_time(response_time)
        
        if success:
            m.successful_requests += 1
        else:
            m.failed_requests += 1
        
        if captcha:
            m.captcha_encounters += 1
        
        # Apply cooldown if too many failures
        if m.failed_requests >= self.max_failures and m.success_rate < 0.5:
            m.cooldown_until = time.time() + self.cooldown_seconds
            print(f"Proxy {proxy} cooled down due to low success rate")
    
    def get_health_report(self) -> Dict:
        """Get health status of all proxies."""
        return {
            proxy: {
                "success_rate": m.success_rate,
                "avg_response_time": m.avg_response_time,
                "total_requests": m.total_requests,
                "in_cooldown": not m.is_available,
                "active_connections": self.active_connections[proxy]
            }
            for proxy, m in self.metrics.items()
        }


# Usage Example
proxies = [
    "http://user1:pass1@geo.iproyal.com:12321",
    "http://user2:pass2@proxy.webshare.io:80",
    "http://user3:pass3@brd.superproxy.io:22225",
]

rotator = IntelligentProxyRotator(
    proxies=proxies,
    algorithm="adaptive",
    cooldown_seconds=300
)

# Make request with tracking
def tracked_request(url: str) -> Optional[requests.Response]:
    proxy = rotator.get_proxy()
    rotator.report_request_start(proxy)
    
    start = time.time()
    try:
        response = requests.get(
            url,
            proxies={"http": proxy, "https": proxy},
            timeout=30
        )
        
        duration = time.time() - start
        has_captcha = "captcha" in response.text.lower()
        is_success = response.status_code < 400 and not has_captcha
        
        rotator.report_request_end(
            proxy=proxy,
            success=is_success,
            response_time=duration,
            captcha=has_captcha
        )
        
        return response if is_success else None
        
    except Exception as e:
        duration = time.time() - start
        rotator.report_request_end(
            proxy=proxy,
            success=False,
            response_time=duration,
            captcha=False
        )
        return None
```

### 5.3 Rate-Limit-Based Rotation

```python
class RateLimitRotator:
    """
    Rotate proxies based on rate limit tracking per domain.
    """
    
    def __init__(
        self,
        proxies: List[str],
        requests_per_minute: int = 10,
        requests_per_hour: int = 100
    ):
        self.proxies = proxies
        self.rpm_limit = requests_per_minute
        self.rph_limit = requests_per_hour
        
        # Track usage per proxy per domain
        self.usage: Dict[str, Dict[str, Deque[float]]] = {
            proxy: {"requests": deque(), "domains": {}}
            for proxy in proxies
        }
    
    def get_proxy(self, domain: str) -> Optional[str]:
        """
        Get proxy that hasn't exceeded rate limits for domain.
        """
        current_time = time.time()
        
        for proxy in self.proxies:
            usage = self.usage[proxy]
            
            # Clean old requests
            self._clean_old_requests(usage["requests"], current_time)
            
            # Check rate limits
            if len(usage["requests"]) < self.rph_limit:
                # Check per-minute limit
                recent = sum(1 for t in usage["requests"] 
                           if current_time - t < 60)
                
                if recent < self.rpm_limit:
                    usage["requests"].append(current_time)
                    return proxy
        
        # All proxies at limit - wait or return None
        return None
    
    def _clean_old_requests(self, requests: Deque[float], current_time: float):
        """Remove requests older than 1 hour."""
        while requests and current_time - requests[0] > 3600:
            requests.popleft()
```

### 5.4 Session Persistence Strategies

```python
class SessionPersistenceManager:
    """
    Manage session persistence with automatic failover.
    """
    
    def __init__(self, rotator: IntelligentProxyRotator):
        self.rotator = rotator
        self.sessions: Dict[str, Dict] = {}  # session_id -> {proxy, cookies, created}
    
    def create_session(self, session_id: Optional[str] = None) -> str:
        """Create new persistent session."""
        if session_id is None:
            session_id = f"sess_{int(time.time())}_{random.randint(1000, 9999)}"
        
        proxy = self.rotator.get_proxy()
        self.sessions[session_id] = {
            "proxy": proxy,
            "cookies": {},
            "created": time.time(),
            "last_used": time.time()
        }
        
        return session_id
    
    def get_session(self, session_id: str) -> Optional[Dict]:
        """Get session with proxy and cookies."""
        if session_id not in self.sessions:
            return None
        
        session = self.sessions[session_id]
        session["last_used"] = time.time()
        return session
    
    def rotate_session(self, session_id: str):
        """Rotate proxy for existing session while keeping cookies."""
        if session_id in self.sessions:
            new_proxy = self.rotator.get_proxy()
            old_proxy = self.sessions[session_id]["proxy"]
            self.sessions[session_id]["proxy"] = new_proxy
            print(f"Session {session_id}: rotated from {old_proxy} to {new_proxy}")
```

---

## 6. Managed Scraping Services

### 6.1 ScrapingBee

**Overview:** Web scraping API that handles proxies and headless browsers

| Feature | Details |
|---------|---------|
| **Pricing** | $49-599/month |
| **Credits** | 250K-8M API credits/month |
| **JS Rendering** | Available (costs extra credits) |
| **Proxy Types** | Datacenter + Premium residential |
| **Concurrent** | 10-200 requests |

**Pricing Tiers:**
| Plan | Monthly Cost | Credits | Per 1K Credits |
|------|--------------|---------|----------------|
| Freelance | $49 | 250,000 | $0.196 |
| Startup | $99 | 1,000,000 | $0.099 |
| Business | $249 | 3,000,000 | $0.083 |
| Business+ | $599 | 8,000,000 | $0.075 |

**Credit Cost Multipliers:**
- Basic request: 1 credit
- JavaScript rendering: +5 credits
- Premium proxy: +10 credits
- Both JS + Premium: 25 credits

**Python Implementation:**
```python
import requests

class ScrapingBeeClient:
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://app.scrapingbee.com/api/v1"
    
    def scrape(
        self,
        url: str,
        render_js: bool = False,
        premium_proxy: bool = False,
        country_code: Optional[str] = None
    ) -> requests.Response:
        """
        Scrape URL via ScrapingBee.
        
        Args:
            url: Target URL
            render_js: Enable JavaScript rendering (+5 credits)
            premium_proxy: Use premium residential proxies (+10 credits)
            country_code: Geo-targeting (e.g., 'us', 'gb')
        """
        params = {
            "api_key": self.api_key,
            "url": url,
        }
        
        if render_js:
            params["render_js"] = "true"
        
        if premium_proxy:
            params["premium_proxy"] = "true"
        
        if country_code:
            params["country_code"] = country_code
        
        # TikTok requires JS rendering + premium proxy
        if "tiktok.com" in url:
            params["render_js"] = "true"
            params["premium_proxy"] = "true"
        
        response = requests.get(self.base_url, params=params, timeout=60)
        return response


# Usage
client = ScrapingBeeClient(api_key="YOUR_API_KEY")

# Standard request (1 credit)
response = client.scrape("https://example.com")

# TikTok (25 credits per request due to JS + premium)
tiktok = client.scrape(
    "https://www.tiktok.com/@username",
    render_js=True,
    premium_proxy=True
)
```

**Pros/Cons for TikTok:**
| Pros | Cons |
|------|------|
| No proxy management needed | Expensive for TikTok (25 credits/request) |
| Handles browser automation | Limited control over fingerprinting |
| Automatic retry logic | May still be detected by advanced checks |
| Simple API | Cost adds up at scale |

---

### 6.2 ScraperAPI

**Overview:** Proxy rotation API with built-in CAPTCHA solving

| Feature | Details |
|---------|---------|
| **Pricing** | $49-299/month |
| **Credits** | 100K-unlimited API calls |
| **Geotargeting** | 50+ countries |
| **CAPTCHA Solving** | Built-in |
| **Concurrent** | Up to 100 threads |

**Pricing Tiers:**
| Plan | Monthly Cost | API Calls | Per 1K Calls |
|------|--------------|-----------|--------------|
| Hobby | $49 | 100,000 | $0.49 |
| Startup | $149 | 1,000,000 | $0.149 |
| Business | $299 | 3,000,000 | $0.10 |
| Scaling | Custom | Custom | Custom |

**Credit Multipliers:**
- Basic request: 1 API credit
- Premium proxy: 10 API credits
- Some domains cost extra

**Python Implementation:**
```python
import requests

class ScraperAPIClient:
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://api.scraperapi.com"
    
    def scrape(
        self,
        url: str,
        premium: bool = False,
        country: Optional[str] = None,
        keep_headers: bool = True
    ) -> requests.Response:
        """
        Scrape URL via ScraperAPI.
        
        Args:
            url: Target URL
            premium: Use premium residential proxies (10x cost)
            country: Country code for geotargeting
            keep_headers: Forward custom headers
        """
        payload = {
            "api_key": self.api_key,
            "url": url,
            "keep_headers": str(keep_headers).lower(),
        }
        
        if premium:
            payload["premium"] = "true"
        
        if country:
            payload["country_code"] = country
        
        # For TikTok, always use premium
        if "tiktok.com" in url:
            payload["premium"] = "true"
        
        response = requests.get(
            f"{self.base_url}/",
            params=payload,
            timeout=60
        )
        return response


# Usage
client = ScraperAPIClient(api_key="YOUR_API_KEY")

# TikTok requires premium (10 credits per request)
tiktok = client.scrape(
    "https://www.tiktok.com/@username",
    premium=True,
    country="us"
)
```

**Pros/Cons for TikTok:**
| Pros | Cons |
|------|------|
| Built-in CAPTCHA solving | Still detected by TikTok at times |
| Good success rate for general sites | 10x cost for premium |
| Simple integration | No JavaScript rendering option |
| Auto-retry on failures | Limited for SPA sites like TikTok |

---

### 6.3 ZenRows

**Overview:** Advanced scraping API with AI-powered anti-detection

| Feature | Details |
|---------|---------|
| **Pricing** | $49-999/month |
| **Universal API** | Basic + Protected results |
| **Scraping Browser** | Playwright-based |
| **Residential Proxies** | Included |
| **AI Web Unblocker** | Premium feature |

**Pricing Tiers:**
| Plan | Monthly | Basic Results | Protected Results | Residential GB |
|------|---------|---------------|-------------------|----------------|
| Developer | $49 | 250,000 | 10,000 | 12.7 GB |
| Startup | $99 | 1,000,000 | 40,000 | 24.8 GB |
| Business | $249 | 3,000,000 | 120,000 | 60 GB |
| Enterprise | $999 | 12,000,000 | 480,000 | 297 GB |

**Cost Structure:**
- Basic request: 1 result
- JavaScript rendering: 5x cost
- Premium proxy: 10x cost
- Both: 25x cost (similar to ScrapingBee)

**Python Implementation:**
```python
import requests

class ZenRowsClient:
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://api.zenrows.com/v1/"
    
    def scrape(
        self,
        url: str,
        js_render: bool = False,
        premium_proxy: bool = False,
        autoparse: bool = False
    ) -> requests.Response:
        """
        Scrape URL via ZenRows Universal Scraper API.
        
        Args:
            url: Target URL
            js_render: Enable JavaScript rendering (5x cost)
            premium_proxy: Use premium proxies (10x cost)
            autoparse: Extract structured data automatically
        """
        params = {
            "apikey": self.api_key,
            "url": url,
        }
        
        if js_render:
            params["js_render"] = "true"
        
        if premium_proxy:
            params["premium_proxy"] = "true"
        
        if autoparse:
            params["autoparse"] = "true"
        
        # For TikTok
        if "tiktok.com" in url:
            params["js_render"] = "true"
            params["premium_proxy"] = "true"
        
        response = requests.get(self.base_url, params=params, timeout=60)
        return response
    
    def scrape_with_browser(
        self,
        url: str,
        wait_for: Optional[str] = None,
        screenshots: bool = False
    ) -> requests.Response:
        """
        Use Scraping Browser (Playwright-based).
        More expensive but better for complex sites.
        """
        # Note: This uses a different endpoint
        params = {
            "apikey": self.api_key,
            "url": url,
            "browser": "true"
        }
        
        if wait_for:
            params["wait_for"] = wait_for
        
        if screenshots:
            params["screenshots"] = "true"
        
        response = requests.get(
            "https://api.zenrows.com/v1/scraping-browser",
            params=params,
            timeout=90
        )
        return response


# Usage
client = ZenRowsClient(api_key="YOUR_API_KEY")

# TikTok scraping (25x cost)
tiktok = client.scrape(
    "https://www.tiktok.com/@username",
    js_render=True,
    premium_proxy=True
)

# Alternative: Use Scraping Browser for complex pages
result = client.scrape_with_browser(
    "https://www.tiktok.com/@username",
    wait_for=".video-feed-item"  # Wait for content to load
)
```

**Pros/Cons for TikTok:**
| Pros | Cons |
|------|------|
| AI Web Unblocker (adaptive) | Premium pricing |
| Scraping Browser option | Complex pricing tiers |
| Good documentation | Learning curve |
| Residential proxies included | Can get expensive at scale |

---

### 6.4 Service Comparison for TikTok

| Service | Cost per 1K TikTok Requests | JS Rendering | Success Rate | Best For |
|---------|---------------------------|--------------|--------------|----------|
| **ScrapingBee** | ~$2.50 (25 credits) | ✓ Built-in | 70-80% | Simple integration |
| **ScraperAPI** | ~$1.50 (10 credits) | ✗ No JS | 50-60% | Non-JS sites |
| **ZenRows** | ~$1.75 (25 credits) | ✓ Built-in | 75-85% | Complex anti-bot |

**Recommendation for TikTok:**
- **Best Overall:** ZenRows with AI Web Unblocker
- **Best Value:** Build custom solution with mobile proxies + fingerprinting
- **Quick Start:** ScrapingBee for initial testing

---

## 7. TikTok-Specific Recommendations

### 7.1 Detection Factors Summary

TikTok uses multi-layer detection:

| Layer | Detection Method | Bypass Strategy |
|-------|------------------|-----------------|
| **IP Layer** | IP reputation, datacenter detection | Use mobile > residential > ISP proxies |
| **TLS Layer** | JA3/JA4 fingerprinting | Use real browsers (Playwright/Puppeteer) |
| **HTTP Layer** | Header order, HTTP/2 fingerprint | Match browser headers exactly |
| **Behavioral** | Mouse patterns, timing, scrolling | Human-like delays and actions |
| **JavaScript** | Canvas fingerprinting, WebGL | Use stealth plugins |

### 7.2 Recommended Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    TikTok Scraper Architecture               │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐   │
│  │   Discovery  │───▶│   Mobile     │───▶│    Queue     │   │
│  │   (Rotating) │    │   Proxies    │    │              │   │
│  └──────────────┘    └──────────────┘    └──────────────┘   │
│         │                                          │         │
│         ▼                                          ▼         │
│  ┌──────────────┐                         ┌──────────────┐   │
│  │  Content IDs │                         │   Worker     │   │
│  │   (Store)    │◀────────────────────────│   Pool       │   │
│  └──────────────┘                         └──────────────┘   │
│                                                    │         │
│                                                    ▼         │
│                                           ┌──────────────┐   │
│                                           │  Playwright  │   │
│                                           │  + Stealth   │   │
│                                           │  + ISP Proxy │   │
│                                           └──────────────┘   │
│                                                    │         │
│                                                    ▼         │
│                                           ┌──────────────┐   │
│                                           │  Data Store  │   │
│                                           └──────────────┘   │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

### 7.3 Optimal Configuration

```python
# Recommended TikTok scraping configuration
TIKTOK_CONFIG = {
    # Discovery phase - high rotation, mobile proxies
    "discovery": {
        "proxy_type": "mobile_4g",
        "provider": "iproyal",  # or "thesocialproxy"
        "rotation": "per_request",
        "requests_per_ip": 10,
        "concurrency": 5,
        "delay_between_requests": (2, 5),  # Random 2-5 seconds
    },
    
    # Scraping phase - sticky sessions, ISP proxies for accounts
    "scraping": {
        "proxy_type": "isp_static",
        "provider": "iproyal",
        "rotation": "sticky",
        "session_duration": 1800,  # 30 minutes
        "browser": {
            "engine": "playwright",
            "stealth_plugins": True,
            "headless": True,
            "viewport": {"width": 1920, "height": 1080},
        },
        "fingerprint": {
            "locale": "en-US",
            "timezone": "America/New_York",
            "user_agent": "chrome_latest",
        }
    },
    
    # Failover settings
    "failover": {
        "max_retries": 3,
        "retry_delay": (5, 10),
        "provider_failover": True,
        "providers": ["iproyal", "oxylabs", "brightdata"],
    }
}
```

### 7.4 Cost Estimate for Production TikTok Scraper

**Scenario:** 100,000 TikTok profiles/month, ~10 requests per profile

| Component | Quantity | Unit Cost | Monthly Cost |
|-----------|----------|-----------|--------------|
| Mobile Proxies (Discovery) | 50GB | $25/GB | $1,250 |
| ISP Proxies (Scraping) | 20 IPs | $2/day | $1,200 |
| Proxy Management | - | - | (included) |
| **Total** | | | **~$2,450/month** |

**Alternative (Managed Service):**
- ZenRows: 1M protected results @ $249 = $249/month
- But may need more for high volume

**Break-Even Analysis:**
- Custom infrastructure: $2,450/month, ~95% success rate
- Managed service: $2,000-3,000/month, ~80% success rate

---

## 8. Summary & Action Plan

### 8.1 Strategy Ranking for TikTok

| Rank | Strategy | Effectiveness | Cost | Complexity |
|------|----------|---------------|------|------------|
| 1 | **Mobile Proxies + Stealth Browser** | ⭐⭐⭐⭐⭐ | $$$ | High |
| 2 | **Multi-Provider Residential + Rotation** | ⭐⭐⭐⭐ | $$ | Medium |
| 3 | **ZenRows/ScrapingBee** | ⭐⭐⭐⭐ | $$ | Low |
| 4 | **ISP Proxies (account-based)** | ⭐⭐⭐ | $$ | Medium |
| 5 | **Single Residential (current)** | ⭐⭐ | $ | Low |

### 8.2 Immediate Recommendations

**Phase 1 (Immediate - Low Cost):**
1. Implement intelligent rotation with IPRoyal sticky sessions
2. Add request jitter (random delays between 2-10 seconds)
3. Implement error-based rotation (rotate on 403/captcha)

**Phase 2 (Short-term - Medium Investment):**
1. Add mobile proxy tier from IPRoyal ($80-150/month)
2. Use mobile for discovery, residential for detail scraping
3. Implement multi-provider failover

**Phase 3 (Long-term - Full Solution):**
1. Deploy Playwright with stealth plugins
2. Implement full fingerprint randomization
3. Build provider-agnostic proxy manager

### 8.3 Expected Outcomes

| Metric | Current | Phase 1 | Phase 2 | Phase 3 |
|--------|---------|---------|---------|---------|
| Success Rate | 20-30% | 50-60% | 75-85% | 90-95% |
| CAPTCHA Rate | 60%+ | 30-40% | 10-20% | <5% |
| Monthly Cost | $50 | $100 | $300 | $2,000+ |

---

## Appendix A: Quick Reference Code

### A.1 Complete Working Example

```python
"""
Complete TikTok scraping setup with intelligent proxy rotation.
"""
import requests
import time
import random
from typing import Optional, Dict

class TikTokScraper:
    def __init__(self):
        self.mobile_proxies = [
            "http://user:pass@geo.iproyal.com:12321",
        ]
        self.current_proxy_idx = 0
        self.failure_count = 0
        
    def get_proxy(self) -> str:
        """Get next mobile proxy."""
        proxy = self.mobile_proxies[self.current_proxy_idx]
        self.current_proxy_idx = (self.current_proxy_idx + 1) % len(self.mobile_proxies)
        return proxy
    
    def get_headers(self) -> Dict[str, str]:
        """Get realistic browser headers."""
        return {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                         "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
            "Accept-Encoding": "gzip, deflate, br",
            "DNT": "1",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
            "Sec-Fetch-Dest": "document",
            "Sec-Fetch-Mode": "navigate",
            "Sec-Fetch-Site": "none",
            "Sec-Fetch-User": "?1",
            "Cache-Control": "max-age=0",
        }
    
    def scrape_profile(self, username: str) -> Optional[Dict]:
        """Scrape TikTok profile with retry logic."""
        url = f"https://www.tiktok.com/@{username}"
        max_retries = 3
        
        for attempt in range(max_retries):
            proxy = self.get_proxy()
            
            try:
                # Random delay
                time.sleep(random.uniform(2, 5))
                
                response = requests.get(
                    url,
                    proxies={"http": proxy, "https": proxy},
                    headers=self.get_headers(),
                    timeout=30,
                    allow_redirects=True
                )
                
                # Check for blocking
                if response.status_code == 200 and "captcha" not in response.text.lower():
                    self.failure_count = max(0, self.failure_count - 1)
                    return {
                        "status": "success",
                        "content": response.text,
                        "proxy_used": proxy
                    }
                else:
                    self.failure_count += 1
                    print(f"Blocked (attempt {attempt + 1}), rotating...")
                    time.sleep(random.uniform(5, 10))
                    
            except Exception as e:
                print(f"Error: {e}")
                self.failure_count += 1
                time.sleep(random.uniform(5, 10))
        
        return None


# Run
if __name__ == "__main__":
    scraper = TikTokScraper()
    result = scraper.scrape_profile("example_user")
    print(result)
```

---

**Document Version:** 1.0  
**Last Updated:** February 2026  
**Next Review:** March 2026
