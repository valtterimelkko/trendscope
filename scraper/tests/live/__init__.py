"""
Live integration tests for external services.

These tests make real API calls to:
- IPRoyal proxy service
- TikTok API (via TikTok-Api library)

SAFETY REQUIREMENTS:
- MAX 10 requests per test run
- Rate limit: 0.17 req/sec (10 req/min MAXIMUM)
- Circuit breaker MUST be active
- IPRoyal proxy REQUIRED for all TikTok tests
- Tests are opt-in (--run-live flag required)

Usage:
    pytest scraper/tests/live/ --run-live  # Run live tests
    pytest scraper/tests/live/            # Skip live tests (default)
"""

import os
import sys

# Ensure project root is in path
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
if project_root not in sys.path:
    sys.path.insert(0, project_root)
