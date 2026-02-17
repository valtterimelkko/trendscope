"""
Detection Engine Configuration Module

Environment-based configuration using Pydantic Settings.
Provides configuration for trend detection, velocity calculation,
and persistence layer.

CRITICAL: Database and Redis credentials should be in .env file.
"""

from pydantic_settings import BaseSettings
from pydantic import Field
from typing import Optional
from functools import lru_cache
from pathlib import Path


class DetectionSettings(BaseSettings):
    """Detection engine configuration from environment variables.

    All settings can be overridden via environment variables.
    Credentials are loaded from .env file at project root.
    """

    # Database Configuration
    database_url: str = Field(
        default="postgresql://postgres:postgres@localhost:5432/trendscope",
        description="PostgreSQL connection URL for trend persistence"
    )
    database_pool_size: int = Field(
        default=10,
        ge=1,
        le=50,
        description="Database connection pool size"
    )
    database_max_overflow: int = Field(
        default=20,
        ge=0,
        le=50,
        description="Maximum overflow connections for pool"
    )

    # Redis Configuration
    redis_url: str = Field(
        default="redis://localhost:6379/0",
        description="Redis connection URL for queue consumption"
    )
    redis_video_queue: str = Field(
        default="tiktok:videos",
        description="Redis list key for video metadata queue (from Stage 03)"
    )

    # Consumer Configuration
    consumer_batch_size: int = Field(
        default=50,
        ge=10,
        le=200,
        description="Number of videos to process per batch"
    )
    consumer_idle_wait: float = Field(
        default=5.0,
        ge=1.0,
        le=60.0,
        description="Seconds to wait when queue is empty"
    )
    consumer_error_wait: float = Field(
        default=30.0,
        ge=5.0,
        le=300.0,
        description="Seconds to wait after an error"
    )
    consumer_max_retries: int = Field(
        default=3,
        ge=1,
        le=10,
        description="Max retries for failed video processing"
    )

    # Velocity Thresholds (from TECH_FEASIBILITY.md Section 2)
    velocity_r_squared_threshold: float = Field(
        default=0.85,
        ge=0.5,
        le=1.0,
        description="R-squared threshold for exponential growth classification"
    )
    velocity_min_data_points: int = Field(
        default=3,
        ge=2,
        le=10,
        description="Minimum data points needed for velocity calculation"
    )
    velocity_max_data_points: int = Field(
        default=168,  # 7 days of hourly data
        ge=24,
        le=720,
        description="Maximum data points to keep in memory (7 days)"
    )
    trend_min_velocity_score: int = Field(
        default=30,
        ge=0,
        le=100,
        description="Minimum velocity score to persist a trend"
    )

    # Growth Rate Thresholds (from TECH_FEASIBILITY.md)
    growth_rate_early_warning: float = Field(
        default=0.5,
        ge=0.1,
        le=2.0,
        description="Growth rate for early warning (50%)"
    )
    growth_rate_high_priority: float = Field(
        default=1.0,
        ge=0.5,
        le=3.0,
        description="Growth rate for high priority alert (100%)"
    )
    growth_rate_critical: float = Field(
        default=2.0,
        ge=1.0,
        le=5.0,
        description="Growth rate for critical alert (200%)"
    )

    # Lifecycle Transition Thresholds
    emerging_to_peaking_velocity: int = Field(
        default=80,
        ge=50,
        le=100,
        description="Velocity score to transition from emerging to peaking"
    )
    peaking_to_saturated_saturation: int = Field(
        default=70,
        ge=50,
        le=90,
        description="Saturation percent to transition from peaking to saturated"
    )
    saturated_to_expired_velocity: int = Field(
        default=20,
        ge=0,
        le=40,
        description="Velocity score to transition from saturated to expired"
    )
    saturated_to_expired_saturation: int = Field(
        default=90,
        ge=70,
        le=100,
        description="Saturation percent to transition from saturated to expired"
    )
    emerging_to_expired_saturation: int = Field(
        default=90,
        ge=70,
        le=100,
        description="Saturation percent to transition directly from emerging to expired"
    )

    # Saturation Scoring Weights
    saturation_weight_acceleration: float = Field(
        default=0.30,
        ge=0.0,
        le=1.0,
        description="Weight for acceleration in saturation calculation"
    )
    saturation_weight_time: float = Field(
        default=0.25,
        ge=0.0,
        le=1.0,
        description="Weight for time since detection in saturation"
    )
    saturation_weight_velocity: float = Field(
        default=0.25,
        ge=0.0,
        le=1.0,
        description="Weight for velocity score in saturation"
    )
    saturation_weight_volume: float = Field(
        default=0.20,
        ge=0.0,
        le=1.0,
        description="Weight for data volume in saturation"
    )

    # Velocity History Configuration
    velocity_history_retention_hours: int = Field(
        default=168,  # 7 days
        ge=24,
        le=720,
        description="Hours to retain velocity history records"
    )
    velocity_history_record_interval: int = Field(
        default=60,
        ge=15,
        le=360,
        description="Minutes between velocity history records"
    )

    # Adaptive Threshold Configuration
    adaptive_threshold_window_days: int = Field(
        default=7,
        ge=1,
        le=30,
        description="Rolling window days for adaptive percentile thresholds"
    )
    adaptive_threshold_min_samples: int = Field(
        default=10,
        ge=5,
        le=100,
        description="Minimum samples needed for adaptive thresholds"
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

    # Health Check Configuration
    health_check_interval: int = Field(
        default=60,
        ge=10,
        le=300,
        description="Seconds between health check logs"
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

    @property
    def is_production(self) -> bool:
        """Check if running in production environment."""
        return self.app_env.lower() == "production"

    @property
    def is_development(self) -> bool:
        """Check if running in development environment."""
        return self.app_env.lower() == "development"

    def validate_saturation_weights(self) -> bool:
        """Validate that saturation weights sum to 1.0."""
        total = (
            self.saturation_weight_acceleration +
            self.saturation_weight_time +
            self.saturation_weight_velocity +
            self.saturation_weight_volume
        )
        return abs(total - 1.0) < 0.01


@lru_cache()
def get_settings() -> DetectionSettings:
    """Get cached settings instance.

    Uses lru_cache to ensure settings are only loaded once.
    """
    return DetectionSettings()


# Global settings instance
settings = get_settings()
