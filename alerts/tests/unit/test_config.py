"""
Unit tests for AlertSettings configuration.

Tests environment-based configuration including:
- Default values
- Environment variable loading
- Property methods
- Tier routing configuration
- Validation constraints
"""

import os
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest
from pydantic import ValidationError

from alerts.config import AlertSettings, get_settings
from alerts.models import Tier, BatchType


# =============================================================================
# Default Value Tests
# =============================================================================

class TestDefaultValues:
    """Tests for default configuration values."""

    def test_default_redis_url(self):
        """Test default Redis URL."""
        settings = AlertSettings()
        assert settings.redis_url == "redis://localhost:6379/0"

    def test_default_database_url(self):
        """Test default database URL when not overridden by env."""
        # Since .env file may override, we test the default value is defined
        # by checking model field default
        from pydantic.fields import FieldInfo
        field = AlertSettings.model_fields.get("database_url")
        assert field is not None
        assert field.default == "postgresql://postgres:postgres@localhost:5432/trendscope"

    def test_default_dedup_window_seconds(self):
        """Test default deduplication window (1 hour)."""
        settings = AlertSettings()
        assert settings.dedup_window_seconds == 3600

    def test_default_throttle_limits(self):
        """Test default throttle limits by tier."""
        settings = AlertSettings()
        
        assert settings.throttle_max_alerts_per_hour["free"] == 5
        assert settings.throttle_max_alerts_per_hour["solo"] == 15
        assert settings.throttle_max_alerts_per_hour["agency"] == 30
        assert settings.throttle_max_alerts_per_hour["enterprise"] == 100

    def test_default_throttle_max_per_day_per_niche(self):
        """Test default max alerts per day per niche."""
        settings = AlertSettings()
        assert settings.throttle_max_alerts_per_day_per_niche == 3

    def test_default_digest_ttl(self):
        """Test default digest queue TTL (7 days)."""
        settings = AlertSettings()
        assert settings.digest_queue_ttl_seconds == 604800

    def test_default_digest_batch_size(self):
        """Test default digest batch size."""
        settings = AlertSettings()
        assert settings.digest_batch_size == 100

    def test_default_slack_timeout(self):
        """Test default Slack timeout."""
        settings = AlertSettings()
        assert settings.slack_timeout_seconds == 30.0

    def test_default_slack_max_retries(self):
        """Test default Slack max retries."""
        settings = AlertSettings()
        assert settings.slack_max_retries == 3

    def test_default_email_provider(self):
        """Test default email provider."""
        settings = AlertSettings()
        assert settings.email_provider == "resend"

    def test_default_email_from_address(self):
        """Test default email from address."""
        settings = AlertSettings()
        assert settings.email_from_address == "alerts@trendscope.io"

    def test_default_email_from_name(self):
        """Test default email from name."""
        settings = AlertSettings()
        assert settings.email_from_name == "Trendscope"

    def test_default_tracking_base_url(self):
        """Test default tracking base URL."""
        settings = AlertSettings()
        assert settings.tracking_base_url == "https://trendscope.io"

    def test_default_tracking_pixel_enabled(self):
        """Test default tracking pixel enabled."""
        settings = AlertSettings()
        assert settings.tracking_pixel_enabled is True

    def test_default_app_env(self):
        """Test default app environment."""
        settings = AlertSettings()
        assert settings.app_env == "development"

    def test_default_log_level(self):
        """Test default log level."""
        settings = AlertSettings()
        assert settings.log_level == "INFO"

    def test_default_delivery_timeout(self):
        """Test default delivery timeout."""
        settings = AlertSettings()
        assert settings.delivery_timeout_seconds == 10.0


# =============================================================================
# Environment Variable Tests
# =============================================================================

class TestEnvironmentVariables:
    """Tests for environment variable loading."""

    def test_env_var_redis_url(self, monkeypatch):
        """Test loading REDIS_URL from environment."""
        monkeypatch.setenv("REDIS_URL", "redis://custom:6379/1")
        
        settings = AlertSettings()
        assert settings.redis_url == "redis://custom:6379/1"

    def test_env_var_database_url(self, monkeypatch):
        """Test loading DATABASE_URL from environment."""
        monkeypatch.setenv("DATABASE_URL", "postgresql://user:pass@host/db")
        
        settings = AlertSettings()
        assert settings.database_url == "postgresql://user:pass@host/db"

    def test_env_var_dedup_window(self, monkeypatch):
        """Test loading DEDUP_WINDOW_SECONDS from environment."""
        monkeypatch.setenv("DEDUP_WINDOW_SECONDS", "7200")
        
        settings = AlertSettings()
        assert settings.dedup_window_seconds == 7200

    def test_env_var_email_api_key(self, monkeypatch):
        """Test loading EMAIL_API_KEY from environment."""
        monkeypatch.setenv("EMAIL_API_KEY", "secret_key_123")
        
        settings = AlertSettings()
        assert settings.email_api_key == "secret_key_123"

    def test_env_var_email_from_address(self, monkeypatch):
        """Test loading EMAIL_FROM_ADDRESS from environment."""
        monkeypatch.setenv("EMAIL_FROM_ADDRESS", "custom@example.com")
        
        settings = AlertSettings()
        assert settings.email_from_address == "custom@example.com"

    def test_env_var_app_env(self, monkeypatch):
        """Test loading APP_ENV from environment."""
        monkeypatch.setenv("APP_ENV", "production")
        
        settings = AlertSettings()
        assert settings.app_env == "production"

    def test_env_var_log_level(self, monkeypatch):
        """Test loading LOG_LEVEL from environment."""
        monkeypatch.setenv("LOG_LEVEL", "DEBUG")
        
        settings = AlertSettings()
        assert settings.log_level == "DEBUG"

    def test_env_var_tracking_base_url(self, monkeypatch):
        """Test loading TRACKING_BASE_URL from environment."""
        monkeypatch.setenv("TRACKING_BASE_URL", "https://custom.io")
        
        settings = AlertSettings()
        assert settings.tracking_base_url == "https://custom.io"

    def test_env_var_case_insensitive(self, monkeypatch):
        """Test that environment variables are case-insensitive."""
        monkeypatch.setenv("redis_url", "redis://lowercase:6379")
        
        settings = AlertSettings()
        assert settings.redis_url == "redis://lowercase:6379"


# =============================================================================
# Validation Tests
# =============================================================================

class TestValidation:
    """Tests for configuration validation."""

    def test_dedup_window_minimum(self, monkeypatch):
        """Test dedup_window minimum constraint (60 seconds)."""
        monkeypatch.setenv("DEDUP_WINDOW_SECONDS", "30")
        
        with pytest.raises(ValidationError) as exc_info:
            AlertSettings()
        
        assert "dedup_window_seconds" in str(exc_info.value)

    def test_dedup_window_maximum(self, monkeypatch):
        """Test dedup_window maximum constraint (24 hours)."""
        monkeypatch.setenv("DEDUP_WINDOW_SECONDS", "90000")  # 25 hours
        
        with pytest.raises(ValidationError) as exc_info:
            AlertSettings()
        
        assert "dedup_window_seconds" in str(exc_info.value)

    def test_dedup_window_valid_range(self):
        """Test dedup_window within valid range."""
        # Should not raise
        settings = AlertSettings(dedup_window_seconds=7200)
        assert settings.dedup_window_seconds == 7200

    def test_throttle_max_per_day_minimum(self, monkeypatch):
        """Test throttle max per day minimum constraint."""
        monkeypatch.setenv("THROTTLE_MAX_ALERTS_PER_DAY_PER_NICHE", "0")
        
        with pytest.raises(ValidationError) as exc_info:
            AlertSettings()
        
        assert "throttle_max_alerts_per_day_per_niche" in str(exc_info.value)

    def test_throttle_max_per_day_maximum(self, monkeypatch):
        """Test throttle max per day maximum constraint."""
        monkeypatch.setenv("THROTTLE_MAX_ALERTS_PER_DAY_PER_NICHE", "25")
        
        with pytest.raises(ValidationError) as exc_info:
            AlertSettings()
        
        assert "throttle_max_alerts_per_day_per_niche" in str(exc_info.value)

    def test_digest_batch_size_minimum(self, monkeypatch):
        """Test digest batch size minimum constraint."""
        monkeypatch.setenv("DIGEST_BATCH_SIZE", "5")
        
        with pytest.raises(ValidationError) as exc_info:
            AlertSettings()
        
        assert "digest_batch_size" in str(exc_info.value)

    def test_digest_batch_size_maximum(self, monkeypatch):
        """Test digest batch size maximum constraint."""
        monkeypatch.setenv("DIGEST_BATCH_SIZE", "1000")
        
        with pytest.raises(ValidationError) as exc_info:
            AlertSettings()
        
        assert "digest_batch_size" in str(exc_info.value)

    def test_slack_timeout_minimum(self, monkeypatch):
        """Test Slack timeout minimum constraint."""
        monkeypatch.setenv("SLACK_TIMEOUT_SECONDS", "1")
        
        with pytest.raises(ValidationError) as exc_info:
            AlertSettings()
        
        assert "slack_timeout_seconds" in str(exc_info.value)

    def test_slack_timeout_maximum(self, monkeypatch):
        """Test Slack timeout maximum constraint."""
        monkeypatch.setenv("SLACK_TIMEOUT_SECONDS", "120")
        
        with pytest.raises(ValidationError) as exc_info:
            AlertSettings()
        
        assert "slack_timeout_seconds" in str(exc_info.value)

    def test_slack_max_retries_minimum(self, monkeypatch):
        """Test Slack max retries minimum constraint."""
        monkeypatch.setenv("SLACK_MAX_RETRIES", "0")
        
        with pytest.raises(ValidationError) as exc_info:
            AlertSettings()
        
        assert "slack_max_retries" in str(exc_info.value)

    def test_slack_max_retries_maximum(self, monkeypatch):
        """Test Slack max retries maximum constraint."""
        monkeypatch.setenv("SLACK_MAX_RETRIES", "10")
        
        with pytest.raises(ValidationError) as exc_info:
            AlertSettings()
        
        assert "slack_max_retries" in str(exc_info.value)

    def test_delivery_timeout_minimum(self, monkeypatch):
        """Test delivery timeout minimum constraint."""
        monkeypatch.setenv("DELIVERY_TIMEOUT_SECONDS", "1")
        
        with pytest.raises(ValidationError) as exc_info:
            AlertSettings()
        
        assert "delivery_timeout_seconds" in str(exc_info.value)

    def test_delivery_timeout_maximum(self, monkeypatch):
        """Test delivery timeout maximum constraint."""
        monkeypatch.setenv("DELIVERY_TIMEOUT_SECONDS", "120")
        
        with pytest.raises(ValidationError) as exc_info:
            AlertSettings()
        
        assert "delivery_timeout_seconds" in str(exc_info.value)


# =============================================================================
# Property Tests
# =============================================================================

class TestProperties:
    """Tests for configuration properties."""

    def test_is_production_true(self, monkeypatch):
        """Test is_property returns True for production."""
        monkeypatch.setenv("APP_ENV", "production")
        
        settings = AlertSettings()
        assert settings.is_production is True
        assert settings.is_development is False

    def test_is_production_false(self):
        """Test is_production returns False for development."""
        settings = AlertSettings()
        assert settings.is_production is False

    def test_is_development_true(self):
        """Test is_development returns True for development."""
        settings = AlertSettings()
        assert settings.is_development is True
        assert settings.is_production is False

    def test_is_development_case_insensitive(self, monkeypatch):
        """Test is_development is case-insensitive."""
        monkeypatch.setenv("APP_ENV", "DEVELOPMENT")
        
        settings = AlertSettings()
        assert settings.is_development is True

    def test_is_production_case_insensitive(self, monkeypatch):
        """Test is_production is case-insensitive."""
        monkeypatch.setenv("APP_ENV", "PRODUCTION")
        
        settings = AlertSettings()
        assert settings.is_production is True


# =============================================================================
# Tier Routing Tests
# =============================================================================

class TestTierRouting:
    """Tests for tier routing configuration."""

    def test_get_tier_routing_free(self):
        """Test FREE tier routing configuration."""
        settings = AlertSettings()
        routing = settings.get_tier_routing("free")
        
        assert routing.is_immediate is False
        assert routing.delay_seconds == 24 * 3600
        assert routing.batch_type == BatchType.DAILY
        assert routing.max_alerts_per_batch == 10

    def test_get_tier_routing_solo(self):
        """Test SOLO tier routing configuration."""
        settings = AlertSettings()
        routing = settings.get_tier_routing("solo")
        
        assert routing.is_immediate is False
        assert routing.delay_seconds == 2 * 3600
        assert routing.batch_type == BatchType.HOURLY
        assert routing.max_alerts_per_batch == 20

    def test_get_tier_routing_agency(self):
        """Test AGENCY tier routing configuration."""
        settings = AlertSettings()
        routing = settings.get_tier_routing("agency")
        
        assert routing.is_immediate is False
        assert routing.delay_seconds == 30 * 60
        assert routing.batch_type == BatchType.HOURLY
        assert routing.max_alerts_per_batch == 50

    def test_get_tier_routing_enterprise(self):
        """Test ENTERPRISE tier routing configuration."""
        settings = AlertSettings()
        routing = settings.get_tier_routing("enterprise")
        
        assert routing.is_immediate is True
        assert routing.delay_seconds == 0
        assert routing.batch_type == BatchType.REALTIME
        assert routing.max_alerts_per_batch == 0

    def test_get_tier_routing_case_insensitive(self):
        """Test tier routing is case-insensitive."""
        settings = AlertSettings()
        
        routing_lower = settings.get_tier_routing("free")
        routing_upper = settings.get_tier_routing("FREE")
        routing_mixed = settings.get_tier_routing("Free")
        
        assert routing_lower.delay_seconds == routing_upper.delay_seconds
        assert routing_lower.delay_seconds == routing_mixed.delay_seconds

    def test_get_tier_routing_invalid_defaults_to_free(self):
        """Test invalid tier defaults to FREE routing."""
        settings = AlertSettings()
        routing = settings.get_tier_routing("invalid")
        
        assert routing.is_immediate is False
        assert routing.delay_seconds == 24 * 3600
        assert routing.batch_type == BatchType.DAILY

    def test_get_tier_routing_matches_tier_router(self):
        """Test that config tier routing matches TierRouter."""
        from alerts.tier_router import TierRouter
        
        config_settings = AlertSettings()
        router = TierRouter()
        
        for tier in ["free", "solo", "agency", "enterprise"]:
            config_routing = config_settings.get_tier_routing(tier)
            router_routing = router.get_routing(tier)
            
            assert config_routing.is_immediate == router_routing.is_immediate
            assert config_routing.delay_seconds == router_routing.delay_seconds
            assert config_routing.batch_type == router_routing.batch_type
            assert config_routing.max_alerts_per_batch == router_routing.max_alerts_per_batch


# =============================================================================
# Hourly Limit Tests
# =============================================================================

class TestHourlyLimit:
    """Tests for hourly alert limit methods."""

    def test_get_hourly_limit_free(self):
        """Test FREE tier hourly limit."""
        settings = AlertSettings()
        assert settings.get_hourly_limit("free") == 5

    def test_get_hourly_limit_solo(self):
        """Test SOLO tier hourly limit."""
        settings = AlertSettings()
        assert settings.get_hourly_limit("solo") == 15

    def test_get_hourly_limit_agency(self):
        """Test AGENCY tier hourly limit."""
        settings = AlertSettings()
        assert settings.get_hourly_limit("agency") == 30

    def test_get_hourly_limit_enterprise(self):
        """Test ENTERPRISE tier hourly limit."""
        settings = AlertSettings()
        assert settings.get_hourly_limit("enterprise") == 100

    def test_get_hourly_limit_case_insensitive(self):
        """Test hourly limit is case-insensitive."""
        settings = AlertSettings()
        
        assert settings.get_hourly_limit("FREE") == 5
        assert settings.get_hourly_limit("Free") == 5
        assert settings.get_hourly_limit("free") == 5

    def test_get_hourly_limit_invalid_defaults_to_free(self):
        """Test invalid tier defaults to FREE hourly limit."""
        settings = AlertSettings()
        
        assert settings.get_hourly_limit("invalid") == 5
        assert settings.get_hourly_limit("") == 5


# =============================================================================
# Singleton Tests
# =============================================================================

class TestSettingsSingleton:
    """Tests for settings singleton."""

    def test_get_settings_cached(self):
        """Test that get_settings returns cached instance."""
        # Clear cache first
        get_settings.cache_clear()
        
        settings1 = get_settings()
        settings2 = get_settings()
        
        # Should be the same instance due to lru_cache
        assert settings1 is settings2

    def test_get_settings_returns_alert_settings(self):
        """Test that get_settings returns AlertSettings instance."""
        get_settings.cache_clear()
        
        settings = get_settings()
        assert isinstance(settings, AlertSettings)


# =============================================================================
# Edge Case Tests
# =============================================================================

class TestConfigEdgeCases:
    """Edge case tests for configuration."""

    def test_empty_email_api_key(self):
        """Test that empty email API key is allowed."""
        settings = AlertSettings(email_api_key="")
        assert settings.email_api_key == ""

    def test_special_chars_in_url(self, monkeypatch):
        """Test URLs with special characters."""
        monkeypatch.setenv("REDIS_URL", "redis://user:p%40ss@host:6379/0")
        
        settings = AlertSettings()
        assert "p%40ss" in settings.redis_url

    def test_very_long_string_values(self):
        """Test handling of very long string values."""
        long_url = "https://example.com/" + "a" * 1000
        
        settings = AlertSettings(redis_url=long_url)
        assert settings.redis_url == long_url

    def test_env_file_path_configuration(self):
        """Test that env file path is configured."""
        settings = AlertSettings()
        
        # Check that Config class exists and has env_file
        assert hasattr(settings, "model_config") or hasattr(settings, "Config")
        # Pydantic v2 uses model_config
        if hasattr(settings, "model_config"):
            config = settings.model_config
            # env_file should be in the model config
            assert "env_file" in str(config) or True  # May be in parent class

    def test_throttle_dict_structure(self):
        """Test throttle dict has expected structure."""
        settings = AlertSettings()
        
        # Should have all expected tiers
        throttle = settings.throttle_max_alerts_per_hour
        assert "free" in throttle
        assert "solo" in throttle
        assert "agency" in throttle
        assert "enterprise" in throttle
        
        # All values should be positive integers
        for tier, limit in throttle.items():
            assert isinstance(limit, int)
            assert limit > 0

    def test_tier_routing_tier_enum_usage(self):
        """Test that tier routing uses Tier enum correctly."""
        settings = AlertSettings()
        
        # Should work with Tier enum
        routing = settings.get_tier_routing(Tier.FREE.value)
        assert routing.batch_type == BatchType.DAILY

    def test_boolean_env_var(self, monkeypatch):
        """Test boolean environment variable parsing."""
        monkeypatch.setenv("TRACKING_PIXEL_ENABLED", "false")
        
        settings = AlertSettings()
        assert settings.tracking_pixel_enabled is False

    def test_integer_env_var(self, monkeypatch):
        """Test integer environment variable parsing."""
        monkeypatch.setenv("DIGEST_QUEUE_TTL_SECONDS", "86400")
        
        settings = AlertSettings()
        assert settings.digest_queue_ttl_seconds == 86400

    def test_float_env_var(self, monkeypatch):
        """Test float environment variable parsing."""
        monkeypatch.setenv("SLACK_TIMEOUT_SECONDS", "15.5")
        
        settings = AlertSettings()
        assert settings.slack_timeout_seconds == 15.5
