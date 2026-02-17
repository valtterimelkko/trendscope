"""
Alert Pipeline Module

Stage 05: Alert Delivery Pipeline

This module implements the alert delivery pipeline that notifies users
of detected trends based on their preferences and subscription tier.

Key Components:
- AlertPipeline: Main orchestration service
- TierRouter: Tier-based latency routing
- DeduplicationService: 1-hour window deduplication
- ThrottlingService: Alert fatigue prevention
- SlackService: Slack webhook delivery
- EmailService: Email delivery (stub)
- DigestWorker: Batched digest generation
- EngagementTracker: Open/click tracking

Tier Latency:
- Free: 24 hours (daily digest)
- Solo: 2 hours
- Agency: 30 minutes
- Enterprise: Real-time (0 latency)

Usage:
    from alerts import AlertPipeline, get_alert_pipeline

    # Initialize pipeline
    pipeline = get_alert_pipeline(db_pool, redis_client)

    # Process trend alert
    results = await pipeline.process_trend_alert(trend, niche_id)

    # Or use individual services
    from alerts import SlackService, DeduplicationService

    slack = SlackService()
    await slack.send_trend_alert(webhook_url, trend)
"""

# Models
from alerts.models import (
    Alert,
    AlertChannel,
    AlertStatus,
    AlertResult,
    UserAlertConfig,
    DigestEntry,
    EngagementEvent,
    EngagementStats,
    TrendForAlert,
    RoutingDecision,
    BatchType,
    Tier,
    SlackMessage,
    EmailContent,
)

# Configuration
from alerts.config import settings, get_settings

# Services
from alerts.tier_router import TierRouter, get_tier_router
from alerts.deduplication import DeduplicationService
from alerts.throttling import ThrottlingService
from alerts.slack_service import SlackService, get_slack_service
from alerts.email_service import EmailService, get_email_service
from alerts.digest_worker import DigestWorker, get_digest_worker
from alerts.engagement import EngagementTracker, get_engagement_tracker
from alerts.pipeline import AlertPipeline, get_alert_pipeline


__all__ = [
    # Models
    "Alert",
    "AlertChannel",
    "AlertStatus",
    "AlertResult",
    "UserAlertConfig",
    "DigestEntry",
    "EngagementEvent",
    "EngagementStats",
    "TrendForAlert",
    "RoutingDecision",
    "BatchType",
    "Tier",
    "SlackMessage",
    "EmailContent",

    # Configuration
    "settings",
    "get_settings",

    # Services
    "TierRouter",
    "get_tier_router",
    "DeduplicationService",
    "ThrottlingService",
    "SlackService",
    "get_slack_service",
    "EmailService",
    "get_email_service",
    "DigestWorker",
    "get_digest_worker",
    "EngagementTracker",
    "get_engagement_tracker",
    "AlertPipeline",
    "get_alert_pipeline",
]
