"""
Alerts module test fixtures and configuration.

Provides fixtures for:
- Alert model testing
- Tier configuration testing
- Deduplication testing
- Routing logic testing
- Mock notification clients
"""

import asyncio
import hashlib
import json
import os
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import AsyncGenerator, Dict, List, Optional
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
import pytest_asyncio


# =============================================================================
# Event Loop Fixture
# =============================================================================

@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


# =============================================================================
# Alert Model Fixtures
# =============================================================================

@pytest.fixture
def alert_statuses() -> Dict[str, str]:
    """Alert status constants."""
    return {
        "PENDING": "pending",
        "PROCESSING": "processing",
        "SENT": "sent",
        "FAILED": "failed",
        "SUPPRESSED": "suppressed"
    }


@pytest.fixture
def sample_alert() -> Dict:
    """Create a sample alert record."""
    return {
        "id": "alert_12345",
        "trend_id": "trend_67890",
        "hashtag": "#viraltrend",
        "tier": "hot",
        "status": "pending",
        "priority": 1,
        "title": "Hot Trend Alert: #viraltrend",
        "message": "This trend is gaining significant traction with 85% velocity",
        "data": {
            "velocity": 0.85,
            "saturation": 0.45,
            "confidence": 0.88,
            "video_count": 2500,
            "total_views": 15000000
        },
        "channels": ["slack", "email"],
        "created_at": datetime.now(timezone.utc).isoformat(),
        "sent_at": None,
        "delivered_at": None,
        "error_message": None
    }


@pytest.fixture
def alert_factory():
    """Factory function for creating alerts with customizable parameters."""
    def _create_alert(
        trend_id: str = "trend_test",
        hashtag: str = "#testtrend",
        tier: str = "hot",
        status: str = "pending",
        priority: int = 1,
        hours_old: float = 0
    ) -> Dict:
        now = datetime.now(timezone.utc)
        created_at = now - timedelta(hours=hours_old)
        
        tier_config = {
            "critical": {"velocity_min": 0.90, "priority": 0},
            "hot": {"velocity_min": 0.70, "priority": 1},
            "warming": {"velocity_min": 0.40, "priority": 2},
            "early": {"velocity_min": 0.15, "priority": 3}
        }
        
        config = tier_config.get(tier, tier_config["hot"])
        
        return {
            "id": f"alert_{trend_id}_{tier}_{int(now.timestamp())}",
            "trend_id": trend_id,
            "hashtag": hashtag,
            "tier": tier,
            "status": status,
            "priority": priority if priority != 1 else config["priority"],
            "title": f"{tier.upper()} Alert: {hashtag}",
            "message": f"Trend {hashtag} has reached {tier} status with high velocity",
            "data": {
                "velocity": config["velocity_min"] + 0.05,
                "saturation": 0.50,
                "confidence": 0.80,
                "video_count": 1000,
                "total_views": 5000000
            },
            "channels": ["slack", "email"],
            "created_at": created_at.isoformat(),
            "sent_at": None,
            "delivered_at": None,
            "error_message": None
        }
    return _create_alert


@pytest.fixture
def sample_alert_batch(alert_factory) -> List[Dict]:
    """Create a batch of sample alerts at different tiers."""
    return [
        alert_factory("trend_1", "#criticaltrend", "critical", "pending", 0, 0.1),
        alert_factory("trend_2", "#hottrend", "hot", "pending", 1, 0.2),
        alert_factory("trend_3", "#warmingtrend", "warming", "pending", 2, 0.5),
        alert_factory("trend_4", "#earlytrend", "early", "pending", 3, 1.0),
        alert_factory("trend_5", "#hottrend2", "hot", "sent", 1, 2.0),
    ]


# =============================================================================
# Tier Configuration Fixtures
# =============================================================================

@pytest.fixture
def tier_config() -> Dict[str, Dict]:
    """Complete tier configuration for testing."""
    return {
        "critical": {
            "name": "critical",
            "display_name": "🔥 Critical",
            "velocity_min": 0.90,
            "velocity_max": 1.0,
            "saturation_max": 0.80,
            "priority": 0,
            "channels": ["slack", "email", "webhook"],
            "throttle_minutes": 5,
            "description": "Explosive growth trends requiring immediate attention"
        },
        "hot": {
            "name": "hot",
            "display_name": "⚡ Hot",
            "velocity_min": 0.70,
            "velocity_max": 0.90,
            "saturation_max": 0.85,
            "priority": 1,
            "channels": ["slack", "email"],
            "throttle_minutes": 15,
            "description": "High velocity trends in peak growth phase"
        },
        "warming": {
            "name": "warming",
            "display_name": "🌡️ Warming",
            "velocity_min": 0.40,
            "velocity_max": 0.70,
            "saturation_max": 0.90,
            "priority": 2,
            "channels": ["slack"],
            "throttle_minutes": 60,
            "description": "Emerging trends showing consistent growth"
        },
        "early": {
            "name": "early",
            "display_name": "🔍 Early",
            "velocity_min": 0.15,
            "velocity_max": 0.40,
            "saturation_max": 0.50,
            "priority": 3,
            "channels": ["digest"],
            "throttle_minutes": 240,
            "description": "New trends just beginning to gain traction"
        }
    }


@pytest.fixture
def tier_thresholds() -> Dict[str, Dict]:
    """Simplified tier thresholds for quick testing."""
    return {
        "critical": {"velocity": 0.90, "priority": 0},
        "hot": {"velocity": 0.70, "priority": 1},
        "warming": {"velocity": 0.40, "priority": 2},
        "early": {"velocity": 0.15, "priority": 3}
    }


@pytest_asyncio.fixture
async def tier_router(tier_config: Dict) -> AsyncGenerator:
    """Create a tier router instance for testing."""
    try:
        from alerts.tier_router import TierRouter
        router = TierRouter(tier_config)
        yield router
    except ImportError:
        mock = MagicMock()
        mock.determine_tier = MagicMock(return_value="hot")
        mock.get_channels = MagicMock(return_value=["slack", "email"])
        mock.should_alert = MagicMock(return_value=True)
        yield mock


# =============================================================================
# Deduplication Fixtures
# =============================================================================

@pytest.fixture
def deduplication_config() -> Dict:
    """Deduplication configuration."""
    return {
        "window_hours": 24,
        "hash_algorithm": "sha256",
        "max_entries": 10000
    }


@pytest.fixture
def deduplication_window() -> timedelta:
    """Default deduplication window."""
    return timedelta(hours=24)


def generate_alert_hash(trend_id: str, tier: str, hashtag: str) -> str:
    """Generate a deduplication hash for an alert."""
    content = f"{trend_id}:{tier}:{hashtag}"
    return hashlib.sha256(content.encode()).hexdigest()[:16]


@pytest.fixture
def sample_dedup_hashes() -> List[str]:
    """Sample deduplication hashes."""
    return [
        generate_alert_hash("trend_1", "hot", "#trend1"),
        generate_alert_hash("trend_2", "critical", "#trend2"),
        generate_alert_hash("trend_3", "warming", "#trend3"),
    ]


@pytest_asyncio.fixture
async def deduplication_store(deduplication_config: Dict) -> AsyncGenerator:
    """Create a deduplication store for testing."""
    try:
        from alerts.deduplication import DeduplicationStore
        store = DeduplicationStore(**deduplication_config)
        yield store
    except ImportError:
        mock = AsyncMock()
        mock.is_duplicate = AsyncMock(return_value=False)
        mock.store_hash = AsyncMock()
        mock.cleanup = AsyncMock()
        yield mock


# =============================================================================
# Notification Channel Fixtures
# =============================================================================

@pytest.fixture
def slack_webhook_config() -> Dict:
    """Slack webhook configuration."""
    return {
        "webhook_url": "https://hooks.slack.com/services/T00/B00/XXX",
        "channel": "#trendscope-alerts",
        "username": "Trendscope Bot",
        "icon_emoji": ":fire:"
    }


@pytest.fixture
def email_config() -> Dict:
    """Email notification configuration."""
    return {
        "smtp_host": "smtp.example.com",
        "smtp_port": 587,
        "username": "alerts@trendscope.io",
        "password": "test_password",
        "from_address": "Trendscope Alerts <alerts@trendscope.io>",
        "to_addresses": ["admin@example.com"]
    }


@pytest.fixture
def webhook_config() -> Dict:
    """Generic webhook configuration."""
    return {
        "url": "https://api.example.com/webhooks/trendscope",
        "headers": {
            "Authorization": "Bearer test_token",
            "Content-Type": "application/json"
        },
        "timeout_seconds": 30
    }


@pytest_asyncio.fixture
async def mock_slack_client() -> AsyncGenerator[AsyncMock, None]:
    """Provide a mocked Slack client."""
    client = AsyncMock()
    client.send_alert = AsyncMock(return_value={"ok": True, "ts": "1234567890.123456"})
    client.send_message = AsyncMock(return_value={"ok": True})
    client.validate_webhook = AsyncMock(return_value=True)
    yield client


@pytest_asyncio.fixture
async def mock_email_client() -> AsyncGenerator[AsyncMock, None]:
    """Provide a mocked email client."""
    client = AsyncMock()
    client.send_email = AsyncMock(return_value={"message_id": "test_msg_123", "status": "sent"})
    client.validate_config = AsyncMock(return_value=True)
    yield client


@pytest_asyncio.fixture
async def mock_webhook_client() -> AsyncGenerator[AsyncMock, None]:
    """Provide a mocked webhook client."""
    client = AsyncMock()
    client.post = AsyncMock(return_value={"status": "ok", "status_code": 200})
    client.validate_endpoint = AsyncMock(return_value=True)
    yield client


# =============================================================================
# Alert Pipeline Fixtures
# =============================================================================

@pytest.fixture
def alert_pipeline_config() -> Dict:
    """Alert pipeline configuration."""
    return {
        "batch_size": 10,
        "poll_interval_seconds": 30,
        "max_retries": 3,
        "retry_delay_seconds": 60,
        "deduplication_window_hours": 24
    }


@pytest_asyncio.fixture
async def alert_processor(alert_pipeline_config: Dict) -> AsyncGenerator:
    """Create an alert processor for testing."""
    try:
        from alerts.processor import AlertProcessor
        processor = AlertProcessor(**alert_pipeline_config)
        yield processor
    except ImportError:
        mock = AsyncMock()
        mock.process_alert = AsyncMock(return_value=True)
        mock.process_batch = AsyncMock(return_value=[])
        mock.send_to_channels = AsyncMock(return_value={"slack": True, "email": True})
        yield mock


# =============================================================================
# Throttling Fixtures
# =============================================================================

@pytest.fixture
def throttle_config() -> Dict[str, int]:
    """Throttle configuration per tier (in minutes)."""
    return {
        "critical": 5,
        "hot": 15,
        "warming": 60,
        "early": 240
    }


@pytest.fixture
def throttle_windows() -> Dict[str, timedelta]:
    """Throttle windows as timedelta objects."""
    return {
        "critical": timedelta(minutes=5),
        "hot": timedelta(minutes=15),
        "warming": timedelta(hours=1),
        "early": timedelta(hours=4)
    }


@pytest_asyncio.fixture
async def throttle_store() -> AsyncGenerator[AsyncMock, None]:
    """Provide a mock throttle store."""
    store = AsyncMock()
    store.is_throttled = AsyncMock(return_value=False)
    store.record_send = AsyncMock()
    store.get_last_sent = AsyncMock(return_value=None)
    yield store


# =============================================================================
# Alert Template Fixtures
# =============================================================================

@pytest.fixture
def alert_templates() -> Dict[str, str]:
    """Alert message templates by tier."""
    return {
        "critical": """🔥 *CRITICAL: {hashtag}*
Velocity: {velocity:.1%} | Saturation: {saturation:.1%}
Videos: {video_count:,} | Views: {total_views:,}
This trend is exploding! Act now!
""",
        "hot": """⚡ *HOT: {hashtag}*
Velocity: {velocity:.1%} | Saturation: {saturation:.1%}
Videos: {video_count:,} | Views: {total_views:,}
High-growth trend detected.
""",
        "warming": """🌡️ *WARMING: {hashtag}*
Velocity: {velocity:.1%} | Saturation: {saturation:.1%}
Videos: {video_count:,} | Views: {total_views:,}
Consistent growth pattern.
""",
        "early": """🔍 *EARLY: {hashtag}*
Velocity: {velocity:.1%} | Saturation: {saturation:.1%}
Videos: {video_count:,} | Views: {total_views:,}
New trend emerging.
"""
    }


@pytest.fixture
def render_alert_message():
    """Function to render alert messages from templates."""
    def _render(template: str, data: Dict) -> str:
        return template.format(**data)
    return _render


# =============================================================================
# Mock Trend Data for Alerting
# =============================================================================

@pytest.fixture
def incoming_trend_for_alert() -> Dict:
    """Sample incoming trend data that would trigger an alert."""
    return {
        "id": "trend_incoming_123",
        "hashtag": "#breakingtrend",
        "status": "peaking",
        "velocity": 0.82,
        "saturation": 0.55,
        "confidence": 0.88,
        "first_seen": (datetime.now(timezone.utc) - timedelta(hours=8)).isoformat(),
        "last_seen": datetime.now(timezone.utc).isoformat(),
        "video_count": 3200,
        "total_views": 18500000,
        "metadata": {
            "top_videos": ["vid1", "vid2", "vid3"],
            "velocity_history": [
                {"timestamp": (datetime.now(timezone.utc) - timedelta(hours=i)).isoformat(), 
                 "velocity": 0.82 - (i * 0.02)}
                for i in range(8)
            ]
        }
    }


# =============================================================================
# Environment & Configuration Fixtures
# =============================================================================

@pytest.fixture
def alerts_env_vars(monkeypatch) -> Dict[str, str]:
    """Set up mock environment variables for alerts module."""
    env_vars = {
        "SLACK_WEBHOOK_URL": "https://hooks.slack.com/services/test",
        "EMAIL_SMTP_HOST": "smtp.test.com",
        "EMAIL_FROM": "test@trendscope.io",
        "REDIS_URL": "redis://localhost:6379/0",
        "ALERT_DEDUP_WINDOW_HOURS": "24",
        "LOG_LEVEL": "DEBUG"
    }
    
    for key, value in env_vars.items():
        monkeypatch.setenv(key, value)
    
    return env_vars


@pytest.fixture
def temp_alert_storage(tmp_path: Path) -> Path:
    """Provide a temporary directory for alert storage."""
    storage_dir = tmp_path / "alerts"
    storage_dir.mkdir()
    return storage_dir


# =============================================================================
# Cleanup Fixtures
# =============================================================================

@pytest.fixture(autouse=True)
def cleanup_alert_fixtures():
    """Clean up any resources after alert tests."""
    yield
    # Cleanup handled by other fixtures
