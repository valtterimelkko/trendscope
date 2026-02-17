"""
Alert Pipeline Configuration Module

Environment-based configuration using Pydantic Settings.
Provides configuration for alert delivery, throttling, and integrations.

Tier Latency Configuration:
- Free: 24 hours (daily digest)
- Solo: 2 hours
- Agency: 30 minutes
- Enterprise: Real-time (0 latency)
"""

from pydantic_settings import BaseSettings
from pydantic import Field
from typing import Dict, Any
from functools import lru_cache
from pathlib import Path
from alerts.models import Tier, RoutingDecision, BatchType


class AlertSettings(BaseSettings):
    """Alert pipeline configuration from environment variables.

    All settings can be overridden via environment variables.
    Credentials are loaded from .env file at project root.
    """

    # Redis Configuration
    redis_url: str = Field(
        default="redis://localhost:6379/0",
        description="Redis connection URL for deduplication/throttling"
    )

    # Database Configuration
    database_url: str = Field(
        default="postgresql://postgres:postgres@localhost:5432/trendscope",
        description="PostgreSQL connection URL"
    )

    # Deduplication Configuration
    dedup_window_seconds: int = Field(
        default=3600,  # 1 hour
        ge=60,
        le=86400,
        description="Deduplication window in seconds (default: 1 hour)"
    )

    # Throttling Configuration
    throttle_max_alerts_per_hour: Dict[str, int] = Field(
        default={
            "free": 5,
            "solo": 15,
            "agency": 30,
            "enterprise": 100
        },
        description="Maximum alerts per hour by tier"
    )
    throttle_max_alerts_per_day_per_niche: int = Field(
        default=3,
        ge=1,
        le=20,
        description="Maximum alerts per day per niche"
    )

    # Digest Configuration
    digest_queue_ttl_seconds: int = Field(
        default=604800,  # 7 days
        description="TTL for digest queue entries"
    )
    digest_batch_size: int = Field(
        default=100,
        ge=10,
        le=500,
        description="Maximum alerts per digest batch"
    )

    # Slack Configuration
    slack_timeout_seconds: float = Field(
        default=30.0,
        ge=5.0,
        le=60.0,
        description="Timeout for Slack webhook requests"
    )
    slack_max_retries: int = Field(
        default=3,
        ge=1,
        le=5,
        description="Maximum retries for Slack delivery"
    )

    # Email Configuration
    email_provider: str = Field(
        default="resend",
        description="Email provider: resend, sendgrid, or stub"
    )
    email_api_key: str = Field(
        default="",
        description="Email provider API key"
    )
    email_from_address: str = Field(
        default="alerts@trendscope.io",
        description="From email address for alerts"
    )
    email_from_name: str = Field(
        default="Trendscope",
        description="From name for email alerts"
    )

    # Tracking Configuration
    tracking_base_url: str = Field(
        default="https://trendscope.io",
        description="Base URL for tracking links"
    )
    tracking_pixel_enabled: bool = Field(
        default=True,
        description="Enable email open tracking pixel"
    )

    # App Configuration
    app_env: str = Field(
        default="development",
        description="Application environment"
    )
    log_level: str = Field(
        default="INFO",
        description="Logging level"
    )

    # Alert Delivery Timeout
    delivery_timeout_seconds: float = Field(
        default=10.0,
        ge=5.0,
        le=60.0,
        description="Timeout for alert delivery operations"
    )

    model_config = {
        "env_file": str(Path(__file__).parent.parent / ".env"),
        "env_file_encoding": "utf-8",
        "case_sensitive": False,
        "extra": "ignore"
    }

    @property
    def is_production(self) -> bool:
        """Check if running in production environment."""
        return self.app_env.lower() == "production"

    @property
    def is_development(self) -> bool:
        """Check if running in development environment."""
        return self.app_env.lower() == "development"

    def get_tier_routing(self, tier: str) -> RoutingDecision:
        """Get routing decision for a tier.

        Maps tier to latency and batching configuration.

        Args:
            tier: User tier (free, solo, agency, enterprise)

        Returns:
            RoutingDecision with delivery parameters
        """
        # Tier latency configuration (matches frontend feature-gates.ts)
        # Free: 24 hours (daily digest) - using 24h based on feature-gates.ts
        # Solo: 2 hours
        # Agency: 30 minutes
        # Enterprise: Real-time (0 latency)
        tier_config = {
            Tier.FREE: RoutingDecision(
                is_immediate=False,
                delay_seconds=24 * 3600,  # 24 hours (daily)
                batch_type=BatchType.DAILY,
                max_alerts_per_batch=10
            ),
            Tier.SOLO: RoutingDecision(
                is_immediate=False,
                delay_seconds=2 * 3600,  # 2 hours
                batch_type=BatchType.HOURLY,
                max_alerts_per_batch=20
            ),
            Tier.AGENCY: RoutingDecision(
                is_immediate=False,
                delay_seconds=30 * 60,  # 30 minutes
                batch_type=BatchType.HOURLY,
                max_alerts_per_batch=50
            ),
            Tier.ENTERPRISE: RoutingDecision(
                is_immediate=True,
                delay_seconds=0,
                batch_type=BatchType.REALTIME,
                max_alerts_per_batch=0  # No limit
            )
        }

        try:
            tier_enum = Tier(tier.lower())
            return tier_config[tier_enum]
        except ValueError:
            # Default to free tier for unknown tiers
            return tier_config[Tier.FREE]

    def get_hourly_limit(self, tier: str) -> int:
        """Get hourly alert limit for a tier.

        Args:
            tier: User tier

        Returns:
            Maximum alerts per hour
        """
        return self.throttle_max_alerts_per_hour.get(
            tier.lower(),
            self.throttle_max_alerts_per_hour["free"]
        )


@lru_cache()
def get_settings() -> AlertSettings:
    """Get cached settings instance.

    Uses lru_cache to ensure settings are only loaded once.
    """
    return AlertSettings()


# Global settings instance
settings = get_settings()
