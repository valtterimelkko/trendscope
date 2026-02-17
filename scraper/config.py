"""
Scraper Configuration Module

Environment-based configuration using Pydantic Settings.
Loads credentials from .env file at project root.

CRITICAL: Never commit .env file with proxy credentials.
"""

from pydantic_settings import BaseSettings
from pydantic import Field
from typing import Optional
from functools import lru_cache
import os
from pathlib import Path


class ScraperSettings(BaseSettings):
    """Scraper configuration from environment variables.

    All settings can be overridden via environment variables.
    Credentials are loaded from .env file at project root.
    """

    # Redis Configuration
    redis_url: str = Field(
        default="redis://localhost:6379/0",
        description="Redis connection URL for queue and hot cache"
    )

    # Proxy Configuration (IPRoyal - from .env)
    # CRITICAL: Never hardcode proxy credentials
    proxy_url: Optional[str] = Field(
        default=None,
        description="IPRoyal proxy URL. Format: http://user:pass@geo.iproyal.com:12321"
    )

    # Rate Limiting (requests per minute per endpoint type)
    rate_limit_trending: int = Field(
        default=15,
        ge=1,
        le=30,
        description="Max requests per minute for trending endpoint (10-20 recommended)"
    )
    rate_limit_hashtag: int = Field(
        default=7,
        ge=1,
        le=15,
        description="Max requests per minute for hashtag endpoint (5-10 recommended)"
    )
    rate_limit_user: int = Field(
        default=3,
        ge=1,
        le=10,
        description="Max requests per minute for user endpoint (2-5 recommended)"
    )

    # Scraping Configuration
    scrape_batch_size: int = Field(
        default=100,
        ge=10,
        le=500,
        description="Number of videos to fetch per scrape cycle"
    )
    scrape_interval: int = Field(
        default=300,
        ge=60,
        le=3600,
        description="Seconds between scrape cycles (5 min default)"
    )
    scrape_hashtags: str = Field(
        default="viral,trending,fyp,foryou",
        description="Comma-separated list of hashtags to monitor"
    )

    # Circuit Breaker Configuration
    circuit_failure_threshold: int = Field(
        default=5,
        ge=1,
        le=20,
        description="Number of failures before circuit opens"
    )
    circuit_recovery_timeout: int = Field(
        default=300,
        ge=60,
        le=900,
        description="Seconds before circuit attempts recovery (5 min default)"
    )
    circuit_half_open_max_calls: int = Field(
        default=3,
        ge=1,
        le=10,
        description="Successful calls needed to close circuit from half-open"
    )

    # Health Check Configuration
    health_port: int = Field(
        default=8080,
        ge=1024,
        le=65535,
        description="Port for health check HTTP server"
    )
    health_check_interval: int = Field(
        default=30,
        ge=10,
        le=300,
        description="Seconds between internal health checks"
    )

    # Logging Configuration
    log_level: str = Field(
        default="INFO",
        description="Logging level: DEBUG, INFO, WARNING, ERROR"
    )
    log_format: str = Field(
        default="json",
        description="Log format: 'json' for structured, 'text' for human-readable"
    )

    # Redis Queue Configuration
    redis_video_queue: str = Field(
        default="tiktok:videos",
        description="Redis list key for video metadata queue"
    )
    redis_video_ttl: int = Field(
        default=72 * 3600,  # 72 hours
        ge=3600,
        le=168 * 3600,  # Max 7 days
        description="TTL in seconds for video data in Redis (72 hours default)"
    )

    # Scraping Modes
    enable_trending: bool = Field(
        default=True,
        description="Enable trending video scraping"
    )
    enable_hashtags: bool = Field(
        default=True,
        description="Enable hashtag-based scraping"
    )
    enable_users: bool = Field(
        default=False,
        description="Enable user-based scraping (disabled by default - more restrictive)"
    )

    # Playwright Configuration
    playwright_headless: bool = Field(
        default=True,
        description="Run Playwright in headless mode"
    )
    playwright_timeout: int = Field(
        default=30000,
        ge=5000,
        le=120000,
        description="Playwright page timeout in milliseconds"
    )

    # Retry Configuration
    retry_max_attempts: int = Field(
        default=3,
        ge=1,
        le=10,
        description="Maximum retry attempts for failed requests"
    )
    retry_min_wait: float = Field(
        default=4.0,
        ge=1.0,
        le=30.0,
        description="Minimum wait between retries in seconds"
    )
    retry_max_wait: float = Field(
        default=60.0,
        ge=10.0,
        le=300.0,
        description="Maximum wait between retries in seconds"
    )

    # Environment
    app_env: str = Field(
        default="development",
        description="Application environment: development, staging, production"
    )

    class Config:
        env_file = str(Path(__file__).parent.parent / ".env")
        env_file_encoding = "utf-8"
        case_sensitive = False
        extra = "ignore"

    @property
    def is_production(self) -> bool:
        """Check if running in production environment."""
        return self.app_env.lower() == "production"

    @property
    def is_development(self) -> bool:
        """Check if running in development environment."""
        return self.app_env.lower() == "development"

    @property
    def hashtag_list(self) -> list[str]:
        """Parse comma-separated hashtags into list."""
        return [tag.strip() for tag in self.scrape_hashtags.split(",") if tag.strip()]

    def get_rate_limit_per_second(self, endpoint_type: str) -> float:
        """Convert requests per minute to requests per second.

        Args:
            endpoint_type: 'trending', 'hashtag', or 'user'

        Returns:
            Requests per second for rate limiter
        """
        limits = {
            "trending": self.rate_limit_trending,
            "hashtag": self.rate_limit_hashtag,
            "user": self.rate_limit_user,
        }
        rpm = limits.get(endpoint_type, 10)
        return rpm / 60.0  # Convert to requests per second


@lru_cache()
def get_settings() -> ScraperSettings:
    """Get cached settings instance.

    Uses lru_cache to ensure settings are only loaded once.
    """
    return ScraperSettings()


# Global settings instance
settings = get_settings()
