"""
Memory-safe TikTok scraper with resource limits

This wraps the scraper with safeguards to prevent system crashes.
"""

import os
import sys
import resource
import signal

# Set resource limits before any imports
# Max 2GB memory
resource.setrlimit(resource.RLIMIT_AS, (2 * 1024 * 1024 * 1024, 2 * 1024 * 1024 * 1024))

# Timeout handler
def timeout_handler(signum, frame):
    print("\n⏱️  SCRAPER TIMEOUT: Operation took too long")
    sys.exit(1)

# Set 5 minute timeout
signal.signal(signal.SIGALRM, timeout_handler)
signal.alarm(300)

# Now import the actual scraper
from tiktok_scraper import TikTokScraperWithCaptcha, scrape_trending_videos

if __name__ == "__main__":
    print("🛡️  Running with resource safeguards:")
    print("   - Memory limit: 2GB")
    print("   - Timeout: 5 minutes")
    print()
    
    import asyncio
    asyncio.run(scrape_trending_videos(count=3))
