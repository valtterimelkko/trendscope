# Behavioral Evasion Techniques for Web Scraping
## Comprehensive Guide to Bypassing TikTok's Behavioral Analysis

**Research Date:** February 2026  
**Target Platform:** TikTok / Social Media Platforms  
**Purpose:** Educational research on anti-detection techniques

---

## Table of Contents

1. [Executive Summary](#executive-summary)
2. [Understanding TikTok's Detection Systems](#understanding-tiktoks-detection-systems)
3. [Session Warming Techniques](#1-session-warming-techniques)
4. [Human-like Mouse Movements](#2-human-like-mouse-movements)
5. [Timing Randomization](#3-timing-randomization)
6. [Browser Profile Building](#4-browser-profile-building)
7. [Request Pattern Randomization](#5-request-pattern-randomization)
8. [Stealth Libraries & Tools](#stealth-libraries--tools)
9. [Commercial Solutions](#commercial-solutions)
10. [Detection Risk Assessment](#detection-risk-assessment)
11. [Complete Implementation Example](#complete-implementation-example)

---

## Executive Summary

Modern anti-bot systems, particularly TikTok's multi-layered detection, analyze:
- **Browser fingerprinting** (500+ attributes)
- **Behavioral biometrics** (mouse movements, scroll patterns, typing)
- **TLS fingerprinting** (JA3/JA4 signatures)
- **Request patterns** (timing, sequence, frequency)
- **Session consistency** (cookie history, browser state)

**Effectiveness Matrix:**

| Technique | Complexity | Effectiveness | Detection Risk | Performance Impact |
|-----------|-----------|---------------|----------------|-------------------|
| Session Warming | Medium | High | Low | High (2-3 weeks) |
| Mouse Movements | Low-Medium | Medium-High | Low-Medium | Low |
| Timing Randomization | Low | Medium | Low | Low |
| Browser Profile Building | High | High | Low | Medium |
| Request Randomization | Low | Medium | Low | Low |
| Stealth Libraries | Low | Medium | Medium | Low |

---

## Understanding TikTok's Detection Systems

### Multi-Layer Detection Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    TIKTOK ANTI-BOT SYSTEMS                  │
├─────────────────────────────────────────────────────────────┤
│  LAYER 1: Network Fingerprinting                            │
│  ├── IP reputation (datacenter vs residential)              │
│  ├── TLS fingerprinting (JA3/JA4 hashes)                    │
│  └── VPN/proxy detection                                    │
├─────────────────────────────────────────────────────────────┤
│  LAYER 2: Browser Fingerprinting                            │
│  ├── Canvas/WebGL fingerprinting                            │
│  ├── Audio context fingerprinting                           │
│  ├── Font enumeration                                       │
│  ├── Navigator properties (webdriver, plugins)              │
│  └── Screen/window characteristics                          │
├─────────────────────────────────────────────────────────────┤
│  LAYER 3: Behavioral Analysis                               │
│  ├── Mouse movement patterns                                │
│  ├── Scroll velocity/acceleration                           │
│  ├── Click timing and positioning                           │
│  ├── Reading time simulation                                │
│  └── Form interaction patterns                              │
├─────────────────────────────────────────────────────────────┤
│  LAYER 4: Session Analysis                                  │
│  ├── Cookie/session history                                 │
│  ├── Browser consistency over time                          │
│  ├── Login pattern analysis                                 │
│  └── Cross-site behavior correlation                        │
└─────────────────────────────────────────────────────────────┘
```

### Key Detection Signals

| Signal | Detection Method | Mitigation |
|--------|-----------------|------------|
| `navigator.webdriver` | JavaScript API | Stealth patches |
| `HeadlessChrome` in UA | User-Agent parsing | Custom UA |
| Missing plugins | Navigator.plugins | Plugin emulation |
| Linear mouse paths | Mouse event analysis | Bezier curves |
| Perfect timing | Action interval analysis | Random delays |
| WebGL vendor | Graphics API | Vendor spoofing |
| TLS cipher order | Handshake analysis | Browser-matching TLS |

---

## 1. Session Warming Techniques

### Concept
Session warming creates a realistic browsing history before accessing the target site. TikTok and other platforms analyze browser state to determine if you're a legitimate user.

### Why It Works
- **Cookie aging**: Fresh cookies are suspicious; aged cookies indicate real usage
- **Browser history**: Empty history suggests automation
- **Trust score**: Platforms assign reputation scores based on browsing patterns
- **Fingerprint consistency**: Long-term consistent fingerprints build trust

### Implementation Approaches

#### Approach A: Automated Warming Pipeline

```python
"""
Session Warming Pipeline for TikTok Scraping
Builds browser profile credibility over 2-3 week period
"""

import asyncio
import random
from datetime import datetime, timedelta
from playwright.async_api import async_playwright
from typing import List, Optional

class SessionWarmer:
    """
    Manages browser profile warming to establish credibility
    before accessing high-security targets like TikTok.
    """
    
    # Sites to visit for building browsing history
    WARMUP_SITES = {
        'search_engines': [
            'https://www.google.com',
            'https://www.bing.com',
            'https://duckduckgo.com'
        ],
        'social_media': [
            'https://www.youtube.com',
            'https://www.instagram.com',
            'https://twitter.com',
            'https://www.reddit.com'
        ],
        'news_sites': [
            'https://news.yahoo.com',
            'https://www.bbc.com',
            'https://www.cnn.com',
            'https://techcrunch.com'
        ],
        'ecommerce': [
            'https://www.amazon.com',
            'https://www.ebay.com',
            'https://www.walmart.com'
        ],
        'video_platforms': [
            'https://www.youtube.com',
            'https://vimeo.com',
            'https://www.twitch.tv'
        ]
    }
    
    def __init__(self, profile_path: str, geolocation: dict = None):
        self.profile_path = profile_path
        self.geolocation = geolocation or {
            'latitude': 40.7128,
            'longitude': -74.0060,
            'timezone': 'America/New_York'
        }
        self.session_log = []
        
    async def warm_profile(self, duration_days: int = 14):
        """
        Execute warming routine over specified duration.
        
        Args:
            duration_days: Number of days to warm profile (recommended: 14-21)
        """
        end_date = datetime.now() + timedelta(days=duration_days)
        
        while datetime.now() < end_date:
            session_duration = random.randint(30, 120)  # 30-120 min sessions
            await self._warming_session(session_duration)
            
            # Wait 4-12 hours between sessions
            hours_until_next = random.randint(4, 12)
            print(f"Session complete. Next session in {hours_until_next} hours")
            await asyncio.sleep(hours_until_next * 3600)
    
    async def _warming_session(self, duration_minutes: int):
        """Execute single warming session with realistic behavior."""
        async with async_playwright() as p:
            # Launch with persistent context for cookie retention
            context = await p.chromium.launch_persistent_context(
                user_data_dir=self.profile_path,
                headless=False,  # Use headed mode for warming
                args=[
                    '--disable-blink-features=AutomationControlled',
                    '--disable-web-security',
                    '--disable-features=IsolateOrigins,site-per-process'
                ],
                locale='en-US',
                timezone_id=self.geolocation['timezone'],
                viewport={'width': 1920, 'height': 1080},
                device_scale_factor=1
            )
            
            page = await context.new_page()
            
            # Set geolocation
            await context.set_geolocation(self.geolocation)
            
            start_time = datetime.now()
            sites_visited = 0
            
            while (datetime.now() - start_time).seconds < duration_minutes * 60:
                # Select random site category with weighted probability
                category = self._select_category()
                site = random.choice(self.WARMUP_SITES[category])
                
                try:
                    await self._visit_site(page, site)
                    sites_visited += 1
                    
                    # Random delay between sites (2-8 minutes)
                    await asyncio.sleep(random.randint(120, 480))
                    
                except Exception as e:
                    print(f"Error visiting {site}: {e}")
                    continue
            
            await context.close()
            
            self.session_log.append({
                'timestamp': datetime.now(),
                'duration': duration_minutes,
                'sites_visited': sites_visited
            })
    
    def _select_category(self) -> str:
        """Select site category based on realistic usage patterns."""
        weights = {
            'search_engines': 0.30,
            'social_media': 0.25,
            'news_sites': 0.20,
            'ecommerce': 0.15,
            'video_platforms': 0.10
        }
        return random.choices(list(weights.keys()), weights=list(weights.values()))[0]
    
    async def _visit_site(self, page, url: str):
        """Visit site with human-like behavior."""
        print(f"Visiting: {url}")
        
        # Navigate with random timeout
        await page.goto(url, timeout=random.randint(15000, 30000))
        
        # Wait for page load with random delay
        await page.wait_for_load_state('networkidle')
        await asyncio.sleep(random.uniform(2, 5))
        
        # Simulate scrolling
        scroll_count = random.randint(3, 10)
        for _ in range(scroll_count):
            await self._human_scroll(page)
            await asyncio.sleep(random.uniform(1, 4))
        
        # Occasionally click on links (20% probability)
        if random.random() < 0.20:
            await self._click_random_link(page)
    
    async def _human_scroll(self, page):
        """Perform human-like scrolling."""
        scroll_amount = random.randint(300, 800)
        duration = random.randint(500, 1500)
        
        await page.mouse.wheel(0, scroll_amount)
        await asyncio.sleep(duration / 1000)
    
    async def _click_random_link(self, page):
        """Click random link on page."""
        links = await page.query_selector_all('a[href^="http"]')
        if links:
            link = random.choice(links[:10])  # Limit to visible links
            await link.click()
            await asyncio.sleep(random.uniform(3, 8))


# Quick warming for immediate use (less effective)
async def quick_warmup(profile_path: str):
    """
    15-minute quick warmup for new profiles.
    Less effective than long-term warming but better than nothing.
    """
    warmer = SessionWarmer(profile_path)
    await warmer._warming_session(15)
```

#### Approach B: Cookie Injection Strategy

```python
"""
Cookie-based session warming for immediate credibility boost.
Import cookies from real browser sessions.
"""

import json
import pickle
from datetime import datetime, timedelta
from typing import Dict, List

class CookieWarming:
    """
    Manages cookie acquisition and injection for session warming.
    """
    
    PREMIUM_SITES = [
        'https://www.google.com',
        'https://www.youtube.com',
        'https://www.facebook.com',
        'https://www.amazon.com',
        'https://www.reddit.com'
    ]
    
    @staticmethod
    def generate_aged_cookies(domain: str, days_old: int = 30) -> List[Dict]:
        """
        Generate realistic cookies with aged timestamps.
        
        Note: This creates synthetic cookies. Real cookies from
        actual browsing are more effective but harder to obtain.
        """
        base_time = datetime.now() - timedelta(days=days_old)
        
        cookie_templates = {
            'google.com': [
                {'name': '1P_JAR', 'value': 'generated_value'},
                {'name': 'NID', 'value': 'generated_value'},
                {'name': 'CONSENT', 'value': 'YES+US.en+201908'}
            ],
            'youtube.com': [
                {'name': 'VISITOR_INFO1_LIVE', 'value': 'generated_value'},
                {'name': 'YSC', 'value': 'generated_value'},
                {'name': 'GPS', 'value': '1'}
            ]
        }
        
        cookies = []
        for template in cookie_templates.get(domain, []):
            cookies.append({
                'name': template['name'],
                'value': template['value'],
                'domain': f'.{domain}',
                'path': '/',
                'expires': int((base_time + timedelta(days=365)).timestamp()),
                'httpOnly': random.choice([True, False]),
                'secure': True,
                'sameSite': random.choice(['Lax', 'Strict', None])
            })
        
        return cookies
    
    @staticmethod
    async def import_from_browser(
        browser_type: str = 'chrome',
        profile_path: Optional[str] = None
    ) -> Dict[str, List[Dict]]:
        """
        Import cookies from real browser installation.
        
        Args:
            browser_type: 'chrome', 'firefox', 'safari'
            profile_path: Custom profile path if not default
        
        Returns:
            Dictionary mapping domains to cookie lists
        """
        # This requires browser-specific cookie database access
        # Chrome example:
        import sqlite3
        import os
        
        default_paths = {
            'chrome': {
                'darwin': '~/Library/Application Support/Google/Chrome/Default/Cookies',
                'linux': '~/.config/google-chrome/Default/Cookies',
                'win32': r'~\AppData\Local\Google\Chrome\User Data\Default\Network\Cookies'
            }
        }
        
        # Implementation requires decryption key access
        # This is platform-specific and requires additional setup
        raise NotImplementedError("Browser cookie import requires OS-specific implementation")
```

### Effectiveness Assessment

| Metric | Score | Notes |
|--------|-------|-------|
| Implementation Complexity | 7/10 | Requires long-term commitment |
| TikTok Effectiveness | 9/10 | Critical for account-based access |
| Detection Risk | 2/10 | Very low if done properly |
| Performance Impact | High | 2-3 weeks minimum for full effect |

### Best Practices

1. **Start with search engines**: Google/YouTube browsing establishes baseline credibility
2. **Maintain consistency**: Same geolocation, timezone, and browser fingerprint throughout
3. **Build gradually**: Don't access TikTok in first 7-10 days
4. **Cross-platform activity**: Visit related sites (Instagram, YouTube) before TikTok
5. **Time patterns**: Mimic real user schedules (active during business hours)

---

## 2. Human-like Mouse Movements

### Concept
Real human mouse movements follow curved paths with variable speed, acceleration, and occasional imprecision. Bots typically move in straight lines at constant speeds.

### Why It Works
- **Fitts's Law**: Human movement time relates to distance and target size
- **Bezier curves**: Natural curved paths between points
- **Gaussian noise**: Random jitter simulates hand tremor
- **Acceleration profiles**: Humans accelerate/decelerate, not instant speed

### Mathematical Foundation

```
Bezier Curve Formula (Cubic):
B(t) = (1-t)³P₀ + 3(1-t)²tP₁ + 3(1-t)t²P₂ + t³P₃

Where:
- P₀ = Start point
- P₃ = End point  
- P₁, P₂ = Control points (determine curve shape)
- t = Parameter 0 to 1
```

### Implementation

```python
"""
Human-like Mouse Movement Simulation for Playwright
Uses Bezier curves with noise injection for realistic paths.
"""

import math
import random
import asyncio
from typing import Tuple, List, Optional
from dataclasses import dataclass
from playwright.async_api import Page

@dataclass
class Point:
    x: float
    y: float
    
class HumanMouse:
    """
    Simulates human-like mouse movements using Bezier curves
    with configurable randomness and timing.
    """
    
    def __init__(self, page: Page):
        self.page = page
        self.current_pos = Point(960, 540)  # Center of 1920x1080
        
    async def move_to(
        self,
        target_x: float,
        target_y: float,
        duration: Optional[float] = None,
        curvature: float = 0.3,
        noise_factor: float = 1.0
    ):
        """
        Move mouse to target with human-like motion.
        
        Args:
            target_x: Target X coordinate
            target_y: Target Y coordinate
            duration: Movement duration in seconds (auto-calculated if None)
            curvature: Curve intensity (0=straight, 1=very curved)
            noise_factor: Random jitter amount
        """
        start = self.current_pos
        end = Point(target_x, target_y)
        
        # Calculate distance for timing
        distance = math.sqrt((end.x - start.x)**2 + (end.y - start.y)**2)
        
        # Auto-calculate duration based on Fitts's Law
        if duration is None:
            # Fitts's Law: MT = a + b * log2(D/W + 1)
            # Simplified: base time + time per pixel
            duration = 0.2 + (distance / 800) * random.uniform(0.8, 1.2)
        
        # Generate Bezier control points
        cp1, cp2 = self._generate_control_points(start, end, curvature)
        
        # Calculate number of steps based on duration
        steps = max(int(duration * 60), 20)  # 60 FPS minimum 20 steps
        
        for i in range(steps + 1):
            t = i / steps
            
            # Apply easing function
            eased_t = self._ease_in_out_cubic(t)
            
            # Calculate position on Bezier curve
            pos = self._cubic_bezier(start, cp1, cp2, end, eased_t)
            
            # Add noise (hand tremor simulation)
            if noise_factor > 0:
                noise_x = random.gauss(0, noise_factor * 2)
                noise_y = random.gauss(0, noise_factor * 2)
                pos = Point(pos.x + noise_x, pos.y + noise_y)
            
            # Move mouse
            await self.page.mouse.move(pos.x, pos.y)
            
            # Variable delay between steps
            step_delay = duration / steps * random.uniform(0.8, 1.2)
            await asyncio.sleep(step_delay)
        
        # Ensure exact final position
        await self.page.mouse.move(end.x, end.y)
        self.current_pos = end
    
    def _generate_control_points(
        self,
        start: Point,
        end: Point,
        curvature: float
    ) -> Tuple[Point, Point]:
        """Generate control points for Bezier curve."""
        
        # Calculate midpoint
        mid_x = (start.x + end.x) / 2
        mid_y = (start.y + end.y) / 2
        
        # Calculate perpendicular direction
        dx = end.x - start.x
        dy = end.y - start.y
        
        # Perpendicular vector
        perp_x = -dy
        perp_y = dx
        
        # Normalize
        length = math.sqrt(perp_x**2 + perp_y**2)
        if length > 0:
            perp_x /= length
            perp_y /= length
        
        # Random offset for control points
        offset = distance * curvature * random.uniform(0.3, 0.7)
        offset *= random.choice([-1, 1])  # Random curve direction
        
        # Control points offset perpendicular to path
        cp1 = Point(
            start.x + dx * 0.3 + perp_x * offset,
            start.y + dy * 0.3 + perp_y * offset
        )
        cp2 = Point(
            start.x + dx * 0.7 + perp_x * offset,
            start.y + dy * 0.7 + perp_y * offset
        )
        
        return cp1, cp2
    
    def _cubic_bezier(
        self,
        p0: Point,
        p1: Point,
        p2: Point,
        p3: Point,
        t: float
    ) -> Point:
        """Calculate point on cubic Bezier curve."""
        t2 = t * t
        t3 = t2 * t
        mt = 1 - t
        mt2 = mt * mt
        mt3 = mt2 * mt
        
        x = mt3 * p0.x + 3 * mt2 * t * p1.x + 3 * mt * t2 * p2.x + t3 * p3.x
        y = mt3 * p0.y + 3 * mt2 * t * p1.x + 3 * mt * t2 * p2.y + t3 * p3.y
        
        return Point(x, y)
    
    def _ease_in_out_cubic(self, t: float) -> float:
        """Cubic easing function for natural acceleration/deceleration."""
        if t < 0.5:
            return 4 * t * t * t
        else:
            f = ((2 * t) - 2)
            return 0.5 * f * f * f + 1
    
    async def click(
        self,
        selector: Optional[str] = None,
        x: Optional[float] = None,
        y: Optional[float] = None,
        button: str = 'left'
    ):
        """
        Click with human-like movement to target.
        
        Args:
            selector: CSS selector to click (alternative to coordinates)
            x: X coordinate (if no selector)
            y: Y coordinate (if no selector)
            button: 'left', 'right', or 'middle'
        """
        if selector:
            element = await self.page.query_selector(selector)
            if not element:
                raise ValueError(f"Element not found: {selector}")
            
            bbox = await element.bounding_box()
            if not bbox:
                raise ValueError(f"Element not visible: {selector}")
            
            # Click within element with some randomness
            x = bbox['x'] + random.uniform(5, bbox['width'] - 5)
            y = bbox['y'] + random.uniform(5, bbox['height'] - 5)
        
        elif x is None or y is None:
            raise ValueError("Must provide either selector or x,y coordinates")
        
        # Add slight overshoot (humans often overshoot and correct)
        if random.random() < 0.3:
            overshoot_x = x + random.uniform(-10, 10)
            overshoot_y = y + random.uniform(-10, 10)
            await self.move_to(overshoot_x, overshoot_y)
            await asyncio.sleep(random.uniform(0.05, 0.15))
        
        # Move to target
        await self.move_to(x, y)
        
        # Pause before click (human reaction time)
        await asyncio.sleep(random.uniform(0.1, 0.3))
        
        # Perform click
        await self.page.mouse.click(x, y, button=button)
    
    async def scroll(
        self,
        amount: int,
        duration: Optional[float] = None
    ):
        """
        Scroll with human-like velocity changes.
        
        Args:
            amount: Pixels to scroll (positive=down, negative=up)
            duration: Scroll duration (auto if None)
        """
        if duration is None:
            duration = abs(amount) / 1000 * random.uniform(0.8, 1.5)
        
        steps = max(int(duration * 30), 10)
        step_amount = amount / steps
        
        for i in range(steps):
            # Variable scroll speed
            factor = math.sin((i / steps) * math.pi)  # Accelerate then decelerate
            delta = step_amount * (0.5 + factor * 0.5)
            
            await self.page.mouse.wheel(0, delta)
            await asyncio.sleep(duration / steps)


# Advanced: Perlin Noise Mouse Movement
class PerlinMouse(HumanMouse):
    """
    Advanced mouse movement using Perlin noise for organic randomness.
    Based on Oxymouse implementation principles.
    """
    
    def __init__(self, page: Page, seed: Optional[int] = None):
        super().__init__(page)
        self.seed = seed or random.randint(0, 10000)
        self.noise_offset = random.random() * 1000
    
    def _perlin_noise(self, x: float) -> float:
        """Simplified Perlin noise implementation."""
        # Perlin noise produces smooth, natural-looking randomness
        # Full implementation would use proper gradient noise
        return (math.sin(x) + math.sin(x * 2.1) * 0.5 + 
                math.sin(x * 4.3) * 0.25) / 1.75
    
    async def move_perlin(
        self,
        target_x: float,
        target_y: float,
        octaves: int = 4
    ):
        """
        Move using Perlin noise-based paths.
        Creates more organic, less predictable movements.
        
        Args:
            target_x: Target X coordinate
            target_y: Target Y coordinate
            octaves: Number of noise layers (higher = more complex)
        """
        start = self.current_pos
        distance = math.sqrt((target_x - start.x)**2 + (target_y - start.y)**2)
        steps = max(int(distance / 5), 30)
        
        for i in range(steps + 1):
            t = i / steps
            
            # Base linear interpolation
            base_x = start.x + (target_x - start.x) * t
            base_y = start.y + (target_y - start.y) * t
            
            # Apply Perlin noise offsets
            noise_val = 0
            amplitude = 1.0
            frequency = 1.0
            
            for _ in range(octaves):
                noise_input = (t + self.noise_offset) * frequency
                noise_val += self._perlin_noise(noise_input) * amplitude
                amplitude *= 0.5
                frequency *= 2
            
            # Apply noise perpendicular to path
            dx = target_x - start.x
            dy = target_y - start.y
            perp_x, perp_y = -dy, dx
            
            length = math.sqrt(perp_x**2 + perp_y**2)
            if length > 0:
                perp_x /= length
                perp_y /= length
            
            offset = noise_val * distance * 0.3
            x = base_x + perp_x * offset
            y = base_y + perp_y * offset
            
            await self.page.mouse.move(x, y)
            await asyncio.sleep(random.uniform(0.01, 0.03))
        
        self.current_pos = Point(target_x, target_y)


# Usage Example
async def example_usage():
    """Example of human-like mouse usage."""
    from playwright.async_api import async_playwright
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        page = await browser.new_page()
        await page.goto('https://example.com')
        
        mouse = HumanMouse(page)
        
        # Move to button with human-like motion
        await mouse.click(selector='#submit-button')
        
        # Scroll down naturally
        await mouse.scroll(800)
        
        # Move to specific coordinates
        await mouse.move_to(500, 600, duration=1.5)
        
        await browser.close()

# Run: asyncio.run(example_usage())
```

### Alternative: Ghost Cursor Implementation

```python
"""
Ghost Cursor-style implementation for Playwright Python.
Adapted from the popular JavaScript library.
"""

import math
import random
from typing import Tuple, Optional
from dataclasses import dataclass

@dataclass
class Vector:
    x: float
    y: float

def bezier_curve(
    start: Vector,
    control1: Vector,
    control2: Vector,
    end: Vector,
    steps: int = 100
) -> list[Vector]:
    """Generate points along cubic Bezier curve."""
    points = []
    for i in range(steps + 1):
        t = i / steps
        t2 = t * t
        t3 = t2 * t
        mt = 1 - t
        mt2 = mt * mt
        mt3 = mt2 * mt
        
        x = mt3 * start.x + 3 * mt2 * t * control1.x + \
            3 * mt * t2 * control2.x + t3 * end.x
        y = mt3 * start.y + 3 * mt2 * t * control1.y + \
            3 * mt * t2 * control2.y + t3 * end.y
        
        points.append(Vector(x, y))
    
    return points

def generate_control_points(
    start: Vector,
    end: Vector,
    spread: float = 0.5
) -> Tuple[Vector, Vector]:
    """Generate random control points for curve variation."""
    # Distance between points
    dist = math.sqrt((end.x - start.x)**2 + (end.y - start.y)**2)
    
    # Random offset for control points
    offset = dist * spread
    
    # Control point 1: near start
    cp1 = Vector(
        start.x + (end.x - start.x) * random.uniform(0.2, 0.4) + 
        random.uniform(-offset, offset),
        start.y + (end.y - start.y) * random.uniform(0.2, 0.4) + 
        random.uniform(-offset, offset)
    )
    
    # Control point 2: near end
    cp2 = Vector(
        start.x + (end.x - start.x) * random.uniform(0.6, 0.8) + 
        random.uniform(-offset, offset),
        start.y + (end.y - start.y) * random.uniform(0.6, 0.8) + 
        random.uniform(-offset, offset)
    )
    
    return cp1, cp2

class GhostCursor:
    """Simplified Ghost Cursor implementation for Playwright."""
    
    def __init__(self, page):
        self.page = page
        self.previous = Vector(0, 0)
    
    async def move_to(
        self,
        x: float,
        y: float,
        steps: int = 100
    ):
        """Move with ghost-like fluid motion."""
        start = self.previous
        end = Vector(x, y)
        
        cp1, cp2 = generate_control_points(start, end)
        points = bezier_curve(start, cp1, cp2, end, steps)
        
        for point in points:
            # Add slight randomness
            jitter_x = random.gauss(0, 0.5)
            jitter_y = random.gauss(0, 0.5)
            
            await self.page.mouse.move(
                point.x + jitter_x,
                point.y + jitter_y
            )
            
            # Variable timing
            await asyncio.sleep(random.uniform(0.005, 0.015))
        
        self.previous = end
```

### Effectiveness Assessment

| Metric | Score | Notes |
|--------|-------|-------|
| Implementation Complexity | 4/10 | Well-documented algorithms |
| TikTok Effectiveness | 7/10 | Important for behavioral scoring |
| Detection Risk | 3/10 | Low if properly implemented |
| Performance Impact | Low | Minimal overhead |

### Libraries Available

| Library | Language | Algorithm | Best For |
|---------|----------|-----------|----------|
| ghost-cursor | JS/TS | Bezier | Playwright/Puppeteer |
| Oxymouse | Python | Bezier/Gaussian/Perlin | Complex movements |
| shy-mouse | JS | Bezier + Fitts | Natural interactions |
| Custom (above) | Python | Bezier/Perlin | Full control |

---

## 3. Timing Randomization

### Concept
Human actions have variable timing. Bots often have precise intervals that create detectable patterns.

### Why It Works
- **Reaction time**: Humans need 150-300ms to react
- **Reading time**: Real users spend time reading content
- **Variable interest**: Different content gets different attention
- **Fatigue patterns**: Humans slow down over time

### Implementation

```python
"""
Timing Randomization for Human-like Behavior Simulation
"""

import random
import asyncio
import math
from typing import Optional, Callable
from dataclasses import dataclass
from enum import Enum

class ContentType(Enum):
    """Content types with different reading patterns."""
    HEADLINE = "headline"
    PARAGRAPH = "paragraph"
    IMAGE = "image"
    VIDEO = "video"
    FORM = "form"
    NAVIGATION = "navigation"

@dataclass
class TimingProfile:
    """Configurable timing profile for different personas."""
    base_reaction_time: float = 0.25  # seconds
    reaction_variance: float = 0.15
    
    reading_speed_wpm: int = 200  # words per minute
    reading_variance: float = 0.3
    
    scroll_pause_min: float = 0.5
    scroll_pause_max: float = 2.0
    
    fatigue_factor: float = 0.05  # Slowdown per minute

class HumanTiming:
    """
    Generates human-like timing delays for various actions.
    Uses psychological models of human behavior.
    """
    
    def __init__(self, profile: Optional[TimingProfile] = None):
        self.profile = profile or TimingProfile()
        self.session_start = asyncio.get_event_loop().time()
        self.action_count = 0
    
    def _get_fatigue_multiplier(self) -> float:
        """Calculate fatigue-based slowdown."""
        elapsed_minutes = (asyncio.get_event_loop().time() - self.session_start) / 60
        return 1 + (self.profile.fatigue_factor * elapsed_minutes)
    
    async def reaction_delay(self, complexity: str = 'normal'):
        """
        Simulate human reaction time.
        
        Args:
            complexity: 'simple', 'normal', 'complex' affects delay
        """
        multipliers = {
            'simple': 0.8,
            'normal': 1.0,
            'complex': 1.5
        }
        
        base = self.profile.base_reaction_time * multipliers.get(complexity, 1.0)
        variance = self.profile.reaction_variance
        
        # Log-normal distribution (humans have longer tail for slow reactions)
        delay = random.lognormvariate(
            mu=math.log(base),
            sigma=variance
        )
        
        # Apply fatigue
        delay *= self._get_fatigue_multiplier()
        
        await asyncio.sleep(max(0.1, delay))
    
    async def reading_delay(
        self,
        word_count: int,
        content_type: ContentType = ContentType.PARAGRAPH
    ):
        """
        Simulate reading time for content.
        
        Args:
            word_count: Number of words to "read"
            content_type: Type of content affects reading speed
        """
        # Content type modifiers
        modifiers = {
            ContentType.HEADLINE: 0.3,      # Quick scan
            ContentType.PARAGRAPH: 1.0,     # Normal reading
            ContentType.IMAGE: 0.5,         # Quick glance
            ContentType.VIDEO: 1.2,         # Slower for video
            ContentType.FORM: 1.5,          # Careful reading
            ContentType.NAVIGATION: 0.2     # Very quick
        }
        
        base_time = (word_count / self.profile.reading_speed_wpm) * 60
        modifier = modifiers.get(content_type, 1.0)
        
        # Add variance
        time_with_variance = base_time * modifier * random.uniform(
            1 - self.profile.reading_variance,
            1 + self.profile.reading_variance
        )
        
        # Apply fatigue
        time_with_variance *= self._get_fatigue_multiplier()
        
        await asyncio.sleep(time_with_variance)
    
    async def scroll_delay(self, scroll_amount: int):
        """
        Delay between scroll actions.
        
        Args:
            scroll_amount: Pixels scrolled (affects pause time)
        """
        # Larger scrolls = longer pause to "read"
        base_pause = self.profile.scroll_pause_min
        scroll_factor = min(abs(scroll_amount) / 500, 1.0)  # Cap at 1
        
        pause_range = self.profile.scroll_pause_max - self.profile.scroll_pause_min
        delay = base_pause + (pause_range * scroll_factor)
        
        # Random variation
        delay *= random.uniform(0.8, 1.5)
        delay *= self._get_fatigue_multiplier()
        
        await asyncio.sleep(delay)
    
    async def between_actions(self, action_type: str = 'default'):
        """
        General delay between actions.
        
        Args:
            action_type: Category of action for timing adjustment
        """
        base_delays = {
            'click': (0.2, 0.8),
            'type': (0.05, 0.15),
            'navigate': (2.0, 5.0),
            'default': (0.5, 1.5)
        }
        
        min_delay, max_delay = base_delays.get(action_type, base_delays['default'])
        delay = random.uniform(min_delay, max_delay)
        delay *= self._get_fatigue_multiplier()
        
        await asyncio.sleep(delay)
    
    async def typing_delay(self, char: Optional[str] = None):
        """
        Simulate human typing speed with character-specific delays.
        
        Args:
            char: Character being typed (affects speed)
        """
        # Base WPM ~60 for typing
        base_wpm = 60
        base_delay = 60 / (base_wpm * 5)  # Convert to seconds per char
        
        # Character-specific adjustments
        if char:
            if char in '.!?':  # Punctuation pauses
                base_delay *= random.uniform(2, 4)
            elif char == ' ':  # Space between words
                base_delay *= random.uniform(1.2, 1.5)
            elif char.isupper():  # Shift key takes time
                base_delay *= random.uniform(1.1, 1.3)
        
        # Add Gaussian noise
        delay = random.gauss(base_delay, base_delay * 0.2)
        delay *= self._get_fatigue_multiplier()
        
        await asyncio.sleep(max(0.01, delay))


class RandomizedScheduler:
    """
    Schedules actions with non-deterministic timing patterns.
    Avoids predictable intervals that trigger bot detection.
    """
    
    def __init__(self):
        self.last_action_time = 0
        self.action_history = []
    
    def get_next_delay(
        self,
        target_interval: float,
        variance: float = 0.3
    ) -> float:
        """
        Get randomized delay that maintains average target interval.
        
        Uses Gaussian distribution with occasional outliers
        to simulate human inconsistency.
        
        Args:
            target_interval: Desired average time between actions
            variance: Standard deviation as fraction of target
        """
        # Base Gaussian randomization
        std_dev = target_interval * variance
        delay = random.gauss(target_interval, std_dev)
        
        # Add occasional outliers (10% chance)
        if random.random() < 0.1:
            outlier_factor = random.choice([0.3, 2.5, 3.0])
            delay *= outlier_factor
        
        # Ensure minimum delay
        return max(0.5, delay)
    
    def get_burst_pattern(
        self,
        num_actions: int,
        base_interval: float
    ) -> list[float]:
        """
        Generate timing pattern for action burst.
        Humans often do actions in clusters with pauses.
        
        Args:
            num_actions: Number of actions in burst
            base_interval: Base time between actions
        """
        delays = []
        
        for i in range(num_actions - 1):
            # Faster within burst
            if i < num_actions - 1:
                delay = random.uniform(base_interval * 0.3, base_interval * 0.7)
            else:
                # Longer pause after burst
                delay = random.uniform(base_interval * 2, base_interval * 4)
            
            delays.append(delay)
        
        return delays


# Usage Example
async def example_timing():
    """Example of timing randomization."""
    timing = HumanTiming()
    
    # Simulate reading a paragraph
    await timing.reading_delay(word_count=150, content_type=ContentType.PARAGRAPH)
    
    # React and click
    await timing.reaction_delay(complexity='simple')
    # ... perform click ...
    
    # Type text with human-like delays
    text = "Hello, this is a test message."
    for char in text:
        # ... type character ...
        await timing.typing_delay(char)
    
    # Scroll with natural pauses
    await timing.scroll_delay(scroll_amount=800)
```

### Effectiveness Assessment

| Metric | Score | Notes |
|--------|-------|-------|
| Implementation Complexity | 2/10 | Simple randomization |
| TikTok Effectiveness | 6/10 | Reduces timing pattern detection |
| Detection Risk | 2/10 | Very low |
| Performance Impact | Minimal | Just adds delays |

---

## 4. Browser Profile Building

### Concept
Creating a consistent, realistic browser fingerprint that remains stable across sessions.

### Why It Works
- **Fingerprint consistency**: Real users have stable fingerprints
- **Hardware correlation**: Settings should match (timezone with geolocation)
- **Browser authenticity**: Proper plugin arrays, WebGL vendors, etc.

### Implementation

```python
"""
Browser Profile Building for Anti-Detection
Creates consistent, realistic browser fingerprints.
"""

import random
import json
from typing import Dict, List, Optional
from dataclasses import dataclass, asdict
from enum import Enum

class OS(Enum):
    WINDOWS_10 = "Windows 10"
    WINDOWS_11 = "Windows 11"
    MACOS = "macOS"
    LINUX = "Linux"

class Browser(Enum):
    CHROME = "Chrome"
    FIREFOX = "Firefox"
    EDGE = "Edge"

@dataclass
class BrowserProfile:
    """
    Complete browser profile configuration.
    All fields should be consistent with each other.
    """
    # Basic info
    os: str
    os_version: str
    browser: str
    browser_version: str
    
    # Screen/Window
    screen_width: int
    screen_height: int
    window_width: int
    window_height: int
    color_depth: int
    pixel_ratio: float
    
    # Hardware
    cpu_cores: int
    memory_gb: int
    
    # Locale
    language: str
    languages: List[str]
    timezone: str
    
    # Geolocation
    latitude: float
    longitude: float
    
    # WebGL
    webgl_vendor: str
    webgl_renderer: str
    
    # Plugins
    plugins: List[Dict]
    
    # Fonts
    fonts: List[str]
    
    # User Agent
    user_agent: str
    
    # Canvas
    canvas_noise: Optional[float] = None

class ProfileGenerator:
    """
    Generates realistic browser profiles with internal consistency.
    """
    
    # Realistic WebGL vendor/renderer combinations
    WEBGL_CONFIGS = {
        'Windows': [
            ('Google Inc. (NVIDIA)', 'ANGLE (NVIDIA, NVIDIA GeForce GTX 1660 Direct3D11 vs_5_0 ps_5_0, D3D11)'),
            ('Google Inc. (AMD)', 'ANGLE (AMD, AMD Radeon RX 580 Direct3D11 vs_5_0 ps_5_0, D3D11)'),
            ('Google Inc. (Intel)', 'ANGLE (Intel, Intel(R) UHD Graphics 620 Direct3D11 vs_5_0 ps_5_0, D3D11)'),
            ('Google Inc. (Microsoft)', 'ANGLE (Microsoft, Microsoft Basic Render Driver Direct3D11 vs_5_0 ps_5_0, D3D11)'),
        ],
        'macOS': [
            ('Apple Inc.', 'Apple M1'),
            ('Apple Inc.', 'Apple M2'),
            ('Apple Inc.', 'Apple M3'),
            ('Intel Inc.', 'Intel Iris OpenGL Engine'),
        ],
        'Linux': [
            ('Google Inc. (NVIDIA)', 'ANGLE (NVIDIA, NVIDIA GeForce GTX 1080 OpenGL 4.5)'),
            ('Google Inc. (AMD)', 'ANGLE (AMD, AMD Radeon Pro 5500M OpenGL 4.6)'),
        ]
    }
    
    # Common system fonts by OS
    SYSTEM_FONTS = {
        'Windows': [
            'Arial', 'Arial Black', 'Calibri', 'Cambria', 'Comic Sans MS',
            'Consolas', 'Courier New', 'Georgia', 'Impact', 'Segoe UI',
            'Tahoma', 'Times New Roman', 'Trebuchet MS', 'Verdana',
            'Webdings', 'Wingdings', 'Segoe Print', 'Segoe Script'
        ],
        'macOS': [
            'Arial', 'Courier', 'Courier New', 'Geneva', 'Georgia',
            'Helvetica', 'Helvetica Neue', 'Lucida Grande', 'Monaco',
            'Palatino', 'Times', 'Times New Roman', 'Verdana',
            'San Francisco', '.AppleSystemUIFont'
        ],
        'Linux': [
            'Arial', 'Courier', 'Courier New', 'DejaVu Sans',
            'DejaVu Sans Mono', 'DejaVu Serif', 'FreeMono',
            'FreeSans', 'FreeSerif', 'Liberation Mono',
            'Liberation Sans', 'Liberation Serif', 'Noto Sans'
        ]
    }
    
    # Common Chrome plugins
    CHROME_PLUGINS = [
        {'name': 'Chrome PDF Plugin', 'filename': 'internal-pdf-viewer'},
        {'name': 'Chrome PDF Viewer', 'filename': 'mhjfbmdgcfjbbpaeojofohoefgiehjai'},
        {'name': 'Native Client', 'filename': 'internal-nacl-plugin'},
    ]
    
    def __init__(self):
        self.used_profiles = set()
    
    def generate_profile(
        self,
        os_type: Optional[OS] = None,
        browser: Optional[Browser] = None,
        geolocation: Optional[Dict] = None
    ) -> BrowserProfile:
        """
        Generate a complete, consistent browser profile.
        
        Args:
            os_type: Target OS (random if None)
            browser: Target browser (random if None)
            geolocation: {'latitude': float, 'longitude': float}
        """
        os_type = os_type or random.choice(list(OS))
        browser = browser or Browser.CHROME  # Default to Chrome for most realistic
        
        # Get OS-specific settings
        os_name = os_type.value.split()[0]
        
        # Generate screen resolution
        screen = self._generate_screen(os_name)
        
        # Generate hardware specs
        hardware = self._generate_hardware(os_name)
        
        # Generate or use provided geolocation
        if geolocation:
            geo = geolocation
            timezone = self._get_timezone_for_location(geo['latitude'], geo['longitude'])
        else:
            geo, timezone = self._generate_geolocation()
        
        # Generate WebGL config
        webgl_vendor, webgl_renderer = random.choice(self.WEBGL_CONFIGS.get(os_name, self.WEBGL_CONFIGS['Windows']))
        
        # Generate user agent
        user_agent = self._generate_user_agent(os_type, browser)
        
        # Generate language based on geolocation
        language = self._get_language_for_location(geo['latitude'], geo['longitude'])
        
        profile = BrowserProfile(
            os=os_type.value,
            os_version=self._get_os_version(os_type),
            browser=browser.value,
            browser_version='124.0.6367.60',
            screen_width=screen['width'],
            screen_height=screen['height'],
            window_width=screen['width'] - random.randint(20, 100),
            window_height=screen['height'] - random.randint(100, 200),
            color_depth=24,
            pixel_ratio=random.choice([1, 1, 1, 1.25, 1.5, 2]),
            cpu_cores=hardware['cores'],
            memory_gb=hardware['memory'],
            language=language,
            languages=[language, 'en-US', 'en'],
            timezone=timezone,
            latitude=geo['latitude'],
            longitude=geo['longitude'],
            webgl_vendor=webgl_vendor,
            webgl_renderer=webgl_renderer,
            plugins=self.CHROME_PLUGINS,
            fonts=self.SYSTEM_FONTS.get(os_name, self.SYSTEM_FONTS['Windows']),
            user_agent=user_agent,
            canvas_noise=random.random() * 0.01  # Subtle canvas noise
        )
        
        return profile
    
    def _generate_screen(self, os_name: str) -> Dict:
        """Generate realistic screen resolution."""
        # Common resolutions weighted by popularity
        resolutions = [
            (1920, 1080, 0.35),  # 1080p most common
            (1366, 768, 0.15),
            (1440, 900, 0.10),
            (2560, 1440, 0.12),
            (3840, 2160, 0.08),
            (1536, 864, 0.08),
            (1280, 720, 0.07),
            (1680, 1050, 0.03),
            (2560, 1600, 0.02),
        ]
        
        total_weight = sum(r[2] for r in resolutions)
        r = random.uniform(0, total_weight)
        
        cumulative = 0
        for width, height, weight in resolutions:
            cumulative += weight
            if r <= cumulative:
                return {'width': width, 'height': height}
        
        return {'width': 1920, 'height': 1080}
    
    def _generate_hardware(self, os_name: str) -> Dict:
        """Generate realistic hardware specs."""
        # Common CPU core counts
        cores = random.choices(
            [2, 4, 6, 8, 12, 16],
            weights=[0.05, 0.25, 0.30, 0.25, 0.10, 0.05]
        )[0]
        
        # Memory (should correlate somewhat with cores)
        memory_options = {
            2: [4, 8],
            4: [8, 16],
            6: [16, 32],
            8: [16, 32, 64],
            12: [32, 64],
            16: [32, 64, 128]
        }
        
        memory = random.choice(memory_options.get(cores, [8, 16]))
        
        return {'cores': cores, 'memory': memory}
    
    def _generate_geolocation(self) -> tuple:
        """Generate realistic geolocation with timezone."""
        # Major cities with realistic distribution
        cities = [
            {'lat': 40.7128, 'lon': -74.0060, 'tz': 'America/New_York', 'weight': 0.15},  # NYC
            {'lat': 34.0522, 'lon': -118.2437, 'tz': 'America/Los_Angeles', 'weight': 0.12},  # LA
            {'lat': 51.5074, 'lon': -0.1278, 'tz': 'Europe/London', 'weight': 0.10},  # London
            {'lat': 35.6762, 'lon': 139.6503, 'tz': 'Asia/Tokyo', 'weight': 0.08},  # Tokyo
            {'lat': 52.5200, 'lon': 13.4050, 'tz': 'Europe/Berlin', 'weight': 0.07},  # Berlin
            {'lat': 48.8566, 'lon': 2.3522, 'tz': 'Europe/Paris', 'weight': 0.07},  # Paris
            {'lat': 41.8781, 'lon': -87.6298, 'tz': 'America/Chicago', 'weight': 0.06},  # Chicago
            {'lat': 29.7604, 'lon': -95.3698, 'tz': 'America/Chicago', 'weight': 0.05},  # Houston
            {'lat': 33.4484, 'lon': -112.0740, 'tz': 'America/Phoenix', 'weight': 0.04},  # Phoenix
            {'lat': 37.7749, 'lon': -122.4194, 'tz': 'America/Los_Angeles', 'weight': 0.06},  # SF
            {'lat': -33.8688, 'lon': 151.2093, 'tz': 'Australia/Sydney', 'weight': 0.04},  # Sydney
            {'lat': 55.7558, 'lon': 37.6173, 'tz': 'Europe/Moscow', 'weight': 0.03},  # Moscow
            {'lat': 39.9042, 'lon': 116.4074, 'tz': 'Asia/Shanghai', 'weight': 0.08},  # Beijing
            {'lat': 19.0760, 'lon': 72.8777, 'tz': 'Asia/Kolkata', 'weight': 0.05},  # Mumbai
        ]
        
        total = sum(c['weight'] for c in cities)
        r = random.uniform(0, total)
        
        cumulative = 0
        for city in cities:
            cumulative += city['weight']
            if r <= cumulative:
                # Add small random offset for exact position
                lat = city['lat'] + random.uniform(-0.1, 0.1)
                lon = city['lon'] + random.uniform(-0.1, 0.1)
                return ({'latitude': lat, 'longitude': lon}, city['tz'])
        
        return ({'latitude': 40.7128, 'longitude': -74.0060}, 'America/New_York')
    
    def _generate_user_agent(self, os_type: OS, browser: Browser) -> str:
        """Generate realistic user agent."""
        chrome_version = '124.0.6367.60'
        
        templates = {
            OS.WINDOWS_10: f'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/{chrome_version} Safari/537.36',
            OS.WINDOWS_11: f'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/{chrome_version} Safari/537.36',
            OS.MACOS: f'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/{chrome_version} Safari/537.36',
            OS.LINUX: f'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/{chrome_version} Safari/537.36'
        }
        
        return templates.get(os_type, templates[OS.WINDOWS_10])
    
    def _get_os_version(self, os_type: OS) -> str:
        """Get OS version string."""
        versions = {
            OS.WINDOWS_10: '10.0.19045',
            OS.WINDOWS_11: '10.0.22631',
            OS.MACOS: '14.4.1',
            OS.LINUX: '5.15.0'
        }
        return versions.get(os_type, '10.0.19045')
    
    def _get_timezone_for_location(self, lat: float, lon: float) -> str:
        """Get timezone for coordinates."""
        # Simplified - in production use timezonefinder library
        if -130 < lon < -60:
            if lat > 35:
                return 'America/New_York'
            elif lat > 30:
                return 'America/Chicago'
            else:
                return 'America/Los_Angeles'
        elif -10 < lon < 40:
            return 'Europe/London'
        elif 130 < lon < 150:
            return 'Asia/Tokyo'
        return 'UTC'
    
    def _get_language_for_location(self, lat: float, lon: float) -> str:
        """Get primary language for location."""
        if -130 < lon < -60:
            return 'en-US'
        elif -10 < lon < 40:
            return 'en-GB'
        elif 130 < lon < 150:
            return 'ja-JP'
        elif 70 < lon < 90:
            return 'hi-IN'
        elif 100 < lon < 130:
            return 'zh-CN'
        return 'en-US'


# Profile persistence
class ProfileManager:
    """
    Manages saving and loading browser profiles for session consistency.
    """
    
    def __init__(self, storage_path: str = './profiles'):
        self.storage_path = storage_path
        import os
        os.makedirs(storage_path, exist_ok=True)
    
    def save_profile(self, profile: BrowserProfile, name: str):
        """Save profile to disk."""
        filepath = f"{self.storage_path}/{name}.json"
        with open(filepath, 'w') as f:
            json.dump(asdict(profile), f, indent=2)
    
    def load_profile(self, name: str) -> Optional[BrowserProfile]:
        """Load profile from disk."""
        import os
        filepath = f"{self.storage_path}/{name}.json"
        if not os.path.exists(filepath):
            return None
        
        with open(filepath, 'r') as f:
            data = json.load(f)
            return BrowserProfile(**data)
    
    def list_profiles(self) -> List[str]:
        """List available profiles."""
        import os
        files = os.listdir(self.storage_path)
        return [f.replace('.json', '') for f in files if f.endswith('.json')]


# Playwright integration
async def create_stealth_context(
    playwright,
    profile: BrowserProfile,
    headless: bool = False
):
    """
    Create Playwright context with profile settings.
    
    Args:
        playwright: Playwright instance
        profile: BrowserProfile to use
        headless: Whether to run headless
    """
    context = await playwright.chromium.launch_persistent_context(
        user_data_dir=f'./profiles/{profile.language}',
        headless=headless,
        args=[
            '--disable-blink-features=AutomationControlled',
            f'--window-size={profile.window_width},{profile.window_height}',
            '--disable-web-security',
            '--disable-features=IsolateOrigins,site-per-process',
        ],
        viewport={
            'width': profile.window_width,
            'height': profile.window_height
        },
        user_agent=profile.user_agent,
        locale=profile.language,
        timezone_id=profile.timezone,
        geolocation={
            'latitude': profile.latitude,
            'longitude': profile.longitude
        },
        permissions=['geolocation'],
        device_scale_factor=profile.pixel_ratio
    )
    
    # Apply additional stealth scripts
    await _apply_stealth_scripts(context, profile)
    
    return context

async def _apply_stealth_scripts(context, profile: BrowserProfile):
    """Apply JavaScript patches for fingerprint consistency."""
    
    stealth_script = f"""
    // Override navigator properties
    Object.defineProperty(navigator, 'webdriver', {{
        get: () => undefined
    }});
    
    Object.defineProperty(navigator, 'hardwareConcurrency', {{
        get: () => {profile.cpu_cores}
    }});
    
    Object.defineProperty(navigator, 'deviceMemory', {{
        get: () => {profile.memory_gb}
    }});
    
    Object.defineProperty(navigator, 'languages', {{
        get: () => {profile.languages}
    }});
    
    // Override plugins
    Object.defineProperty(navigator, 'plugins', {{
        get: () => {profile.plugins}
    }});
    
    // Screen properties
    Object.defineProperty(screen, 'width', {{
        get: () => {profile.screen_width}
    }});
    
    Object.defineProperty(screen, 'height', {{
        get: () => {profile.screen_height}
    }});
    
    Object.defineProperty(screen, 'colorDepth', {{
        get: () => {profile.color_depth}
    }});
    
    // WebGL vendor spoofing
    const getParameter = WebGLRenderingContext.prototype.getParameter;
    WebGLRenderingContext.prototype.getParameter = function(parameter) {{
        if (parameter === 37445) {{
            return '{profile.webgl_vendor}';
        }}
        if (parameter === 37446) {{
            return '{profile.webgl_renderer}';
        }}
        return getParameter(parameter);
    }};
    
    // Remove automation markers
    delete navigator.__proto__.webdriver;
    
    // Override chrome runtime
    window.chrome = window.chrome || {{}};
    window.chrome.runtime = window.chrome.runtime || {{}};
    """
    
    # Add script to all pages
    await context.add_init_script(stealth_script)
```

### Effectiveness Assessment

| Metric | Score | Notes |
|--------|-------|-------|
| Implementation Complexity | 7/10 | Requires many coordinated changes |
| TikTok Effectiveness | 9/10 | Critical for avoiding fingerprint flagging |
| Detection Risk | 2/10 | Low with proper consistency |
| Performance Impact | Low | One-time setup |

---

## 5. Request Pattern Randomization

### Concept
Varying the timing, order, and characteristics of requests to avoid pattern detection.

### Why It Works
- **Rate consistency**: Humans don't make requests at exact intervals
- **Sequence variation**: Real users navigate unpredictably
- **Header consistency**: Request headers should match browser fingerprint

### Implementation

```python
"""
Request Pattern Randomization for Stealth Scraping
"""

import random
import asyncio
from typing import Dict, List, Optional
from dataclasses import dataclass
from enum import Enum

class RequestStrategy(Enum):
    RANDOM = "random"
    BURST = "burst"
    CONSERVATIVE = "conservative"
    AGGRESSIVE = "aggressive"

@dataclass
class RequestPattern:
    """Configuration for request timing patterns."""
    min_delay: float = 2.0
    max_delay: float = 8.0
    burst_probability: float = 0.1
    burst_size_range: tuple = (3, 7)
    burst_delay_range: tuple = (0.5, 1.5)

class RequestRandomizer:
    """
    Randomizes request patterns to avoid detection.
    """
    
    def __init__(self, pattern: Optional[RequestPattern] = None):
        self.pattern = pattern or RequestPattern()
        self.request_history = []
        self.consecutive_requests = 0
    
    async def get_next_delay(self) -> float:
        """
        Calculate delay before next request.
        Uses burst patterns and variable timing.
        """
        # Check if we're in a burst
        if self.consecutive_requests > 0:
            self.consecutive_requests -= 1
            return random.uniform(
                self.pattern.burst_delay_range[0],
                self.pattern.burst_delay_range[1]
            )
        
        # Chance to start a burst
        if random.random() < self.pattern.burst_probability:
            self.consecutive_requests = random.randint(
                self.pattern.burst_size_range[0],
                self.pattern.burst_size_range[1]
            )
        
        # Normal random delay
        delay = random.uniform(self.pattern.min_delay, self.pattern.max_delay)
        
        # Add occasional long pauses (5% chance)
        if random.random() < 0.05:
            delay *= random.uniform(3, 6)
        
        return delay
    
    def generate_headers(self, base_profile: Dict) -> Dict:
        """
        Generate randomized but consistent headers.
        
        Args:
            base_profile: Browser profile for consistency
        """
        headers = {
            'User-Agent': base_profile.get('user_agent'),
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
            'Accept-Language': base_profile.get('language', 'en-US'),
            'Accept-Encoding': 'gzip, deflate, br',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': random.choice(['none', 'same-origin', 'cross-site']),
            'Sec-Fetch-User': '?1',
            'Cache-Control': random.choice(['max-age=0', 'no-cache']),
        }
        
        # Randomly omit some headers (humans don't send every header every time)
        optional_headers = ['DNT', 'Upgrade-Insecure-Requests']
        for header in optional_headers:
            if random.random() < 0.3:
                headers.pop(header, None)
        
        return headers
    
    def randomize_viewport(self, base_width: int, base_height: int) -> Dict:
        """
        Slightly randomize viewport for each request.
        Maintains approximate size while adding variance.
        """
        # Small variations that humans might have
        # (resizing browser, zoom levels, etc.)
        width_var = random.randint(-20, 20)
        height_var = random.randint(-30, 30)
        
        return {
            'width': max(800, base_width + width_var),
            'height': max(600, base_height + height_var)
        }


class UserAgentRotator:
    """
    Rotates user agents while maintaining consistency within sessions.
    """
    
    CHROME_UAS = [
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
        'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
    ]
    
    FIREFOX_UAS = [
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:125.0) Gecko/20100101 Firefox/125.0',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:125.0) Gecko/20100101 Firefox/125.0',
    ]
    
    def __init__(self, stickiness: float = 0.8):
        """
        Args:
            stickiness: Probability of keeping same UA (0-1)
        """
        self.stickiness = stickiness
        self.current_ua = None
        self.session_ua = None
    
    def get_user_agent(self, force_new: bool = False) -> str:
        """
        Get user agent with session stickiness.
        """
        if force_new or not self.current_ua:
            self.current_ua = random.choice(self.CHROME_UAs)
            if not self.session_ua:
                self.session_ua = self.current_ua
        elif random.random() > self.stickiness:
            # Small chance to rotate
            self.current_ua = random.choice(self.CHROME_UAs)
        
        return self.current_ua
    
    def get_session_ua(self) -> str:
        """Get consistent UA for entire session."""
        if not self.session_ua:
            self.session_ua = random.choice(self.CHROME_UAs)
        return self.session_ua


# Request sequence randomization
class NavigationRandomizer:
    """
    Randomizes navigation patterns to simulate natural browsing.
    """
    
    def __init__(self):
        self.visited_urls = []
        self.back_probability = 0.15
    
    def should_go_back(self) -> bool:
        """Determine if user should go back (rather than new page)."""
        if len(self.visited_urls) < 2:
            return False
        return random.random() < self.back_probability
    
    def get_navigation_delay(self, action_type: str = 'click') -> float:
        """
        Get delay for navigation action.
        
        Args:
            action_type: 'click', 'type', 'scroll', 'back'
        """
        delays = {
            'click': (0.5, 2.0),
            'type': (0.05, 0.2),
            'scroll': (0.3, 1.0),
            'back': (0.8, 2.5),
            'new_tab': (1.0, 3.0)
        }
        
        min_d, max_d = delays.get(action_type, (0.5, 2.0))
        return random.uniform(min_d, max_d)
    
    def get_scroll_pattern(self) -> List[int]:
        """
        Generate realistic scroll amounts.
        Returns list of scroll deltas.
        """
        pattern = []
        total_scroll = 0
        target_scroll = random.randint(1000, 5000)
        
        while total_scroll < target_scroll:
            # Variable scroll amounts
            scroll = random.randint(200, 800)
            pattern.append(scroll)
            total_scroll += scroll
            
            # Occasionally scroll back up (reading)
            if random.random() < 0.2:
                pattern.append(-random.randint(100, 400))
        
        return pattern
```

### Effectiveness Assessment

| Metric | Score | Notes |
|--------|-------|-------|
| Implementation Complexity | 3/10 | Simple randomization |
| TikTok Effectiveness | 6/10 | Helps avoid pattern detection |
| Detection Risk | 3/10 | Low |
| Performance Impact | Low | Adds delays only |

---

## Stealth Libraries & Tools

### 1. Playwright-Stealth (Python)

```python
"""
Playwright-Stealth Integration
Most popular anti-detection library for Playwright.
"""

# Installation: pip install playwright-stealth

from playwright.sync_api import sync_playwright
from playwright_stealth import stealth_sync, StealthConfig

# Basic usage
with sync_playwright() as p:
    browser = p.chromium.launch(headless=False)
    page = browser.new_page()
    
    # Apply stealth patches
    stealth_sync(page)
    
    page.goto('https://tiktok.com')
    # ... scraping logic ...

# Advanced configuration
config = StealthConfig(
    # Vendor and renderer for WebGL
    vendor='Intel Inc.',
    renderer='Intel Iris OpenGL Engine',
    
    # Navigator overrides
    navigator_languages=['en-US', 'en'],
    navigator_hardware_concurrency=8,
    navigator_device_memory=8,
    
    # Custom user agent
    user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.0.36',
    
    # Disable specific evasions
    disable_evasions=['chrome_runtime', 'navigator_plugins']
)

with sync_playwright() as p:
    browser = p.chromium.launch()
    page = browser.new_page()
    stealth_sync(page, config)
```

**Evasions Included:**
- `chrome_app`: Removes `window.chrome.app` signature
- `chrome_csi`: Patches `chrome.csi`
- `chrome_load_times`: Patches `chrome.loadTimes`
- `chrome_runtime`: Adds functional `chrome.runtime`
- `iframe_content_window`: Prevents iframe detection
- `media_codecs`: Adds proprietary codec support
- `navigator_hardware_concurrency`: Sets logical processors
- `navigator_languages`: Sets language list
- `navigator_permissions`: Masks permission queries
- `navigator_plugins`: Emulates plugins array
- `navigator_vendor`: Sets vendor string
- `navigator_webdriver`: Removes `navigator.webdriver`
- `sourceurl`: Prevents sourceURL detection
- `user_agent`: Sets consistent user agent
- `webgl_vendor`: Spoofs WebGL vendor/renderer
- `window_outerdimensions`: Sets window dimensions

### 2. Undetected-Playwright

```python
"""
Undetected-Playwright Alternative
More aggressive patching approach.
"""

# Installation: pip install undetected-playwright

from undetected_playwright import sync_playwright

with sync_playwright() as p:
    # Launches with built-in stealth
    browser = p.chromium.launch(
        headless=False,
        args=['--disable-blink-features=AutomationControlled']
    )
    
    context = browser.new_context(
        viewport={'width': 1920, 'height': 1080},
        user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    )
    
    page = context.new_page()
    page.goto('https://tiktok.com')
```

### 3. Rebrowser-Playwright

```python
"""
Rebrowser-Playwright for Advanced Evasion
Handles runtime fingerprinting and TLS issues.
"""

# Installation: pip install rebrowser-playwright

from rebrowser_playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.launch(
        # Rebrowser handles many evasions automatically
        rebrowser=True
    )
    page = browser.new_page()
    page.goto('https://tiktok.com')
```

### Library Comparison

| Library | Maintenance | Effectiveness | Ease of Use | Best For |
|---------|-------------|---------------|-------------|----------|
| playwright-stealth | Moderate | Medium | Easy | Quick setup |
| undetected-playwright | Moderate | Medium-High | Easy | Drop-in replacement |
| rebrowser-playwright | Active | High | Medium | Advanced evasion |
| Custom patches | N/A | Highest | Hard | Maximum control |

### Limitations

**Playwright-Stealth Limitations:**
- Struggles against advanced anti-bots (DataDome, PerimeterX at max settings)
- May not handle all TLS fingerprinting
- Canvas fingerprinting patches are basic
- Open source = detection signatures are known

**When Libraries Fail:**
- Enterprise-grade anti-bot (Kasada, Shape Security)
- Active behavioral analysis with ML
- Device binding (hardware attestation)
- Continuous challenge/response systems

---

## Commercial Solutions

### 1. ScrapingAnt

**Features:**
- Managed headless browser
- Automatic proxy rotation
- Built-in stealth patches
- CAPTCHA solving

**Pricing:**
- Free tier: 10,000 API credits/month
- Startup: $19/month (500K credits)
- Business: $99/month (3M credits)

**Integration:**

```python
import requests

# Simple API call - handles all evasion
response = requests.get(
    'https://api.scrapingant.com/v2/general',
    params={
        'url': 'https://tiktok.com',
        'x-api-key': 'YOUR_API_KEY',
        'proxy_country': 'us',
        'wait_for_selector': '.video-feed'
    }
)

print(response.text)
```

### 2. ScraperAPI

**Features:**
- 40M+ residential proxy pool
- JavaScript rendering
- Auto IP rotation
- CAPTCHA bypass

**Pricing:**
- Hobby: $49/month (100K API calls)
- Startup: $149/month (1M API calls)
- Business: $299/month (3M API calls)

### 3. Bright Data (formerly Luminati)

**Features:**
- Premium residential proxies
- Proxy Manager for custom logic
- Built-in fingerprinting
- 72M+ IPs

**Pricing:**
- Residential: $8.40/GB
- ISP proxies: $0.50/IP + $15/GB

### 4. Oxylabs

**Features:**
- 100M+ residential proxies
- AI-powered anti-detection
- Web Scraper API
- Real-time crawler

**Pricing:**
- Residential: $8/GB
- Web Scraper API: $99/month (17K requests)

### 5. Browserless (Self-hosted/Managed)

**Features:**
- Managed browser infrastructure
- Stealth mode built-in
- Session management
- Proxy integration

```python
import requests

# Use Browserless API
response = requests.post(
    'https://chrome.browserless.io/content',
    headers={'Content-Type': 'application/json'},
    json={
        'url': 'https://tiktok.com',
        'stealth': True,
        'waitFor': 5000
    }
)
```

### Commercial vs Self-hosted Comparison

| Factor | Self-hosted | Commercial |
|--------|-------------|------------|
| Cost (scale) | Lower at scale | Higher at scale |
| Setup time | High | Low |
| Maintenance | High | None |
| Detection risk | Higher (known signatures) | Lower (proprietary methods) |
| Flexibility | Full | Limited |
| Proxy quality | Self-managed | Premium included |
| Support | Community | Professional |

---

## Detection Risk Assessment

### Risk Matrix by Technique

```
Detection Risk vs. Implementation Effort

High Risk │
          │   • Raw Playwright
          │   • No delays
          │   • Straight mouse
          │
Medium    │   • Basic stealth lib
          │   • Fixed timing
          │   • Random UA only
          │
Low Risk  │   • Custom profile  • Commercial API
          │   • Bezier mouse    • Session warming
          │   • Human timing    • Browser farm
          │
          └────────────────────────────────
            Low Effort          High Effort
```

### Detection Indicators

| Red Flag | Detection Likelihood | Mitigation |
|----------|---------------------|------------|
| `navigator.webdriver=true` | 100% | Stealth library |
| Linear mouse paths | 70% | Bezier curves |
| Perfect timing | 60% | Random delays |
| Missing plugins | 50% | Plugin emulation |
| Datacenter IP | 80% | Residential proxy |
| Fresh cookies | 40% | Session warming |
| Headless UA | 90% | Custom UA |
| WebGL mismatch | 45% | Profile consistency |

### TikTok-Specific Detection

TikTok's detection stack likely includes:
- **Shape Security/F5**: Behavioral fingerprinting
- **Custom ML models**: Pattern recognition
- **Device binding**: Hardware attestation attempts
- **Cross-reference**: Multi-signal correlation

**Highest Impact Mitigations:**
1. Residential/mobile proxies (40% of detection)
2. Session warming (30% of detection)
3. Browser profile consistency (20% of detection)
4. Behavioral simulation (10% of detection)

---

## Complete Implementation Example

```python
"""
Complete TikTok Scraping Implementation with All Evasion Techniques
"""

import asyncio
import random
from datetime import datetime
from playwright.async_api import async_playwright, Page

# Import our custom modules (from above)
# from mouse_simulation import HumanMouse, PerlinMouse
# from timing import HumanTiming, ContentType
# from profile import ProfileGenerator, BrowserProfile, create_stealth_context
# from request_patterns import RequestRandomizer

class StealthTikTokScraper:
    """
    Production-ready TikTok scraper with comprehensive evasion.
    """
    
    def __init__(self, profile: 'BrowserProfile'):
        self.profile = profile
        self.timing = HumanTiming()
        self.request_randomizer = RequestRandomizer()
        self.mouse = None
        self.page = None
        
    async def initialize(self, playwright):
        """Initialize browser with full stealth configuration."""
        
        # Create context with profile
        self.context = await create_stealth_context(
            playwright,
            self.profile,
            headless=False  # Headed mode for better stealth
        )
        
        self.page = await self.context.new_page()
        self.mouse = HumanMouse(self.page)
        
        # Additional evasion scripts
        await self._inject_advanced_stealth()
        
    async def _inject_advanced_stealth(self):
        """Inject advanced stealth scripts."""
        
        scripts = [
            # Canvas noise injection
            f"""
            const originalToDataURL = HTMLCanvasElement.prototype.toDataURL;
            HTMLCanvasElement.prototype.toDataURL = function(...args) {{
                const result = originalToDataURL.apply(this, args);
                if (result.length > 1000) {{
                    // Add subtle noise to canvas fingerprint
                    return result.slice(0, -4) + Math.random().toString(36).slice(2, 6);
                }}
                return result;
            }};
            """,
            
            # Audio context spoofing
            """
            const originalGetFloatFrequencyData = 
                AnalyserNode.prototype.getFloatFrequencyData;
            AnalyserNode.prototype.getFloatFrequencyData = function(array) {
                originalGetFloatFrequencyData.call(this, array);
                // Add imperceptible noise
                for (let i = 0; i < array.length; i++) {
                    array[i] += (Math.random() - 0.5) * 0.001;
                }
            };
            """,
            
            # Font enumeration protection
            """
            const originalFonts = document.fonts;
            Object.defineProperty(document, 'fonts', {
                get: () => ({
                    ...originalFonts,
                    check: () => true  // Always report font available
                })
            });
            """
        ]
        
        for script in scripts:
            await self.page.add_init_script(script)
    
    async def warmup_session(self, minutes: int = 10):
        """Quick session warming before TikTok access."""
        
        warmup_sites = [
            'https://www.google.com',
            'https://www.youtube.com',
            'https://www.reddit.com'
        ]
        
        for site in warmup_sites:
            await self._visit_with_human_behavior(site, duration=minutes/len(warmup_sites)*60)
    
    async def _visit_with_human_behavior(self, url: str, duration: float):
        """Visit site with full human simulation."""
        
        await self.page.goto(url, wait_until='networkidle')
        await self.timing.reaction_delay()
        
        # Random scrolling
        end_time = asyncio.get_event_loop().time() + duration
        while asyncio.get_event_loop().time() < end_time:
            scroll_amount = random.randint(300, 800)
            await self.mouse.scroll(scroll_amount)
            await self.timing.scroll_delay(scroll_amount)
            
            # Occasionally pause to "read"
            if random.random() < 0.3:
                await self.timing.reading_delay(
                    word_count=random.randint(50, 200),
                    content_type=ContentType.PARAGRAPH
                )
    
    async def navigate_to_tiktok(self):
        """Navigate to TikTok with full evasion."""
        
        # Random delay before navigation
        delay = await self.request_randomizer.get_next_delay()
        await asyncio.sleep(delay)
        
        # Navigate
        await self.page.goto('https://tiktok.com', wait_until='networkidle')
        
        # Wait and observe (critical for TikTok)
        await self.timing.reading_delay(
            word_count=100,
            content_type=ContentType.NAVIGATION
        )
        
        # Simulate initial browsing
        await self._simulate_tiktok_browsing()
    
    async def _simulate_tiktok_browsing(self):
        """Simulate natural TikTok browsing behavior."""
        
        # Scroll through feed naturally
        for _ in range(random.randint(5, 15)):
            # Random scroll amount (video height varies)
            scroll = random.randint(400, 900)
            
            # Use Bezier curve mouse movement
            await self.mouse.move_to(
                random.randint(200, 800),
                random.randint(300, 700),
                duration=random.uniform(0.5, 1.5)
            )
            
            # Scroll with human-like timing
            await self.mouse.scroll(scroll)
            await self.timing.scroll_delay(scroll)
            
            # Watch video (variable attention)
            watch_time = random.uniform(3, 15)
            await asyncio.sleep(watch_time)
            
            # Occasional interactions
            if random.random() < 0.2:
                await self._interact_with_video()
    
    async def _interact_with_video(self):
        """Simulate video interaction (like, comment, etc.)."""
        
        interaction_type = random.choice(['like', 'scroll_faster', 'pause'])
        
        if interaction_type == 'like':
            # Find and click like button with human movement
            like_button = await self.page.query_selector('[data-e2e="like-button"]')
            if like_button:
                bbox = await like_button.bounding_box()
                if bbox:
                    await self.mouse.click(
                        x=bbox['x'] + random.uniform(10, bbox['width']-10),
                        y=bbox['y'] + random.uniform(10, bbox['height']-10)
                    )
                    await self.timing.reaction_delay('simple')
    
    async def scrape_video_data(self, video_url: str) -> dict:
        """Scrape data from specific video."""
        
        # Navigate with randomization
        await self.page.goto(video_url, wait_until='networkidle')
        await self.timing.reaction_delay('complex')
        
        # Let video load
        await asyncio.sleep(3)
        
        # Extract data
        data = await self.page.evaluate('''() => {
            return {
                title: document.querySelector('h1')?.textContent || '',
                author: document.querySelector('[data-e2e="user-title"]')?.textContent || '',
                likes: document.querySelector('[data-e2e="likes-count"]')?.textContent || '',
                comments: document.querySelector('[data-e2e="comment-count"]')?.textContent || ''
            };
        }''')
        
        return data
    
    async def close(self):
        """Clean shutdown."""
        if self.context:
            await self.context.close()


# Main execution
async def main():
    """Example main function."""
    
    # Generate profile
    generator = ProfileGenerator()
    profile = generator.generate_profile()
    
    async with async_playwright() as p:
        scraper = StealthTikTokScraper(profile)
        
        try:
            await scraper.initialize(p)
            
            # Optional: warmup session
            # await scraper.warmup_session(minutes=5)
            
            # Navigate to TikTok
            await scraper.navigate_to_tiktok()
            
            # Scrape data
            # data = await scraper.scrape_video_data('https://tiktok.com/@user/video/...')
            
            await asyncio.sleep(30)  # Keep open for observation
            
        finally:
            await scraper.close()

# Run: asyncio.run(main())
```

---

## Conclusion

### Technique Effectiveness Summary

| Rank | Technique | Impact | Effort | ROI |
|------|-----------|--------|--------|-----|
| 1 | Session Warming | Critical | High | High |
| 2 | Residential Proxies | Critical | Low | Very High |
| 3 | Browser Profile | High | Medium | High |
| 4 | Mouse Movements | Medium | Low | Medium |
| 5 | Timing Randomization | Medium | Low | Medium |
| 6 | Stealth Libraries | Medium | Low | High |

### Recommended Stack for TikTok

**Minimum Viable:**
1. Playwright-stealth
2. Random delays (1-5 seconds)
3. Residential proxies

**Recommended:**
1. Custom browser profile
2. Bezier mouse movements
3. Session warming (7+ days)
4. Premium residential proxies
5. Human timing simulation

**Enterprise:**
1. Browser farm (AdsPower, Multilogin)
2. 21+ day aged profiles
3. Mobile proxies
4. Custom stealth patches
5. ML-based behavior variation

### Legal and Ethical Considerations

**Important:**
- Always respect robots.txt
- Comply with platform Terms of Service
- Don't scrape personal data
- Consider rate limiting
- Be aware of CFAA and similar laws

This research is for educational purposes and authorized testing only.

---

*Document Version: 1.0*  
*Last Updated: February 2026*
