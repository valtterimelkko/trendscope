"""
Alert Pipeline Data Models

Pydantic models for alert data structures, user configurations,
and pipeline results.

These models align with:
- Database schema in Project-Technical-Architecture.md
- API contracts for alert endpoints
- Stage 04 Trend model for trend data
"""

from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime
from typing import Optional, List, Dict, Any
from enum import Enum
import uuid


class AlertChannel(str, Enum):
    """Alert delivery channel."""

    EMAIL = "email"
    SLACK = "slack"
    WEBHOOK = "webhook"


class AlertStatus(str, Enum):
    """Alert lifecycle status.

    Status flow:
    PENDING -> SENT -> DELIVERED -> (OPENED/CLICKED)
                    -> FAILED
    """

    PENDING = "pending"      # Queued for delivery
    SENT = "sent"            # Delivered to channel
    DELIVERED = "delivered"  # Confirmed received
    FAILED = "failed"        # Delivery failed


class Tier(str, Enum):
    """User subscription tier."""

    FREE = "free"
    SOLO = "solo"
    AGENCY = "agency"
    ENTERPRISE = "enterprise"


class BatchType(str, Enum):
    """Type of batching for alert delivery."""

    REALTIME = "realtime"  # Immediate delivery (Enterprise)
    HOURLY = "hourly"      # Hourly digest (Solo, Agency)
    DAILY = "daily"        # Daily digest (Free)
    WEEKLY = "weekly"      # Weekly digest (Free fallback)


class Alert(BaseModel):
    """Alert record.

    Represents an alert that has been triggered for a user
    based on a detected trend.

    Maps to 'alerts' table in PostgreSQL.
    """

    model_config = ConfigDict(populate_by_name=True)

    id: uuid.UUID = Field(
        default_factory=uuid.uuid4,
        description="Unique alert identifier"
    )
    user_id: uuid.UUID = Field(
        ...,
        description="User who will receive the alert"
    )
    trend_id: uuid.UUID = Field(
        ...,
        description="Trend that triggered the alert"
    )
    channel: AlertChannel = Field(
        ...,
        description="Delivery channel (email, slack, webhook)"
    )
    status: AlertStatus = Field(
        default=AlertStatus.PENDING,
        description="Current alert status"
    )

    # Timestamps
    sent_at: Optional[datetime] = Field(
        default=None,
        description="When alert was sent"
    )
    opened_at: Optional[datetime] = Field(
        default=None,
        description="When alert was opened (email)"
    )
    clicked_at: Optional[datetime] = Field(
        default=None,
        description="When alert link was clicked"
    )

    # Tracking
    dismissed: bool = Field(
        default=False,
        description="Whether user dismissed the alert"
    )
    confidence_score: float = Field(
        default=0.0,
        ge=0.0,
        le=1.0,
        description="Confidence score for the alert"
    )

    # Metadata
    created_at: datetime = Field(
        default_factory=datetime.utcnow,
        description="Record creation timestamp"
    )


class AlertResult(BaseModel):
    """Result of alert processing.

    Returned by the pipeline after processing a trend alert.
    """

    alert_id: Optional[uuid.UUID] = Field(
        default=None,
        description="Created alert ID if persisted"
    )
    queued: bool = Field(
        default=False,
        description="Whether alert was queued for digest"
    )
    sent: bool = Field(
        default=False,
        description="Whether alert was sent immediately"
    )
    skipped: bool = Field(
        default=False,
        description="Whether alert was skipped (duplicate/throttled)"
    )
    skip_reason: Optional[str] = Field(
        default=None,
        description="Reason for skipping if skipped"
    )
    error: Optional[str] = Field(
        default=None,
        description="Error message if failed"
    )


class UserAlertConfig(BaseModel):
    """User alert configuration.

    Contains user preferences and integrations for alert delivery.
    """

    model_config = ConfigDict(populate_by_name=True)

    user_id: uuid.UUID = Field(
        ...,
        description="User ID"
    )
    email: str = Field(
        ...,
        description="User email address"
    )
    tier: Tier = Field(
        default=Tier.FREE,
        description="User subscription tier"
    )
    email_notifications: bool = Field(
        default=True,
        description="Whether user wants email notifications"
    )

    # Niche subscription
    niche_id: uuid.UUID = Field(
        ...,
        description="Niche ID for this alert config"
    )
    alert_enabled: bool = Field(
        default=True,
        description="Whether alerts are enabled for this niche"
    )
    velocity_threshold: int = Field(
        default=50,
        ge=0,
        le=100,
        description="Minimum velocity score for alert"
    )

    # Integration (Slack/Webhook)
    integration_id: Optional[uuid.UUID] = Field(
        default=None,
        description="Alert integration ID"
    )
    integration_type: Optional[str] = Field(
        default=None,
        description="Integration type: slack, webhook"
    )
    integration_config: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Integration configuration (webhook_url, etc.)"
    )


class RoutingDecision(BaseModel):
    """Routing decision for an alert.

    Determines how an alert should be delivered based on tier.
    """

    is_immediate: bool = Field(
        ...,
        description="Whether to send immediately (Enterprise)"
    )
    delay_seconds: int = Field(
        ...,
        ge=0,
        description="Delay before delivery (0 for immediate)"
    )
    batch_type: BatchType = Field(
        ...,
        description="Type of batching"
    )
    max_alerts_per_batch: int = Field(
        ...,
        ge=0,
        description="Maximum alerts per batch (0 = unlimited)"
    )


class TrendForAlert(BaseModel):
    """Trend data formatted for alert message.

    Contains all information needed to render an alert message.
    """

    model_config = ConfigDict(populate_by_name=True)

    id: uuid.UUID = Field(
        ...,
        description="Trend ID"
    )
    type: str = Field(
        ...,
        description="Trend type: sound, hashtag, format"
    )
    name: str = Field(
        ...,
        description="Trend name"
    )
    velocity_score: int = Field(
        ...,
        ge=0,
        le=100,
        description="Velocity score (0-100)"
    )
    saturation_percent: int = Field(
        ...,
        ge=0,
        le=100,
        description="Saturation percentage"
    )
    video_count_current: int = Field(
        ...,
        ge=0,
        description="Current video count"
    )
    growth_rate: float = Field(
        ...,
        ge=0.0,
        description="Growth rate percentage"
    )
    niche_name: Optional[str] = Field(
        default=None,
        description="Niche name"
    )
    first_detected_at: datetime = Field(
        default_factory=datetime.utcnow,
        description="When trend was first detected"
    )
    status: str = Field(
        default="emerging",
        description="Trend status"
    )

    # Computed window for display
    window_hours: str = Field(
        default="6-8",
        description="Estimated window in hours"
    )


class DigestEntry(BaseModel):
    """Entry in a digest batch.

    Stored in Redis for batched alert delivery.
    """

    trend_id: str = Field(
        ...,
        description="Trend UUID as string"
    )
    trend_name: str = Field(
        ...,
        description="Trend name"
    )
    velocity_score: int = Field(
        ...,
        ge=0,
        le=100,
        description="Velocity score"
    )
    saturation_percent: int = Field(
        ...,
        ge=0,
        le=100,
        description="Saturation percentage"
    )
    growth_rate: float = Field(
        ...,
        ge=0.0,
        description="Growth rate"
    )
    niche_name: Optional[str] = Field(
        default=None,
        description="Niche name"
    )
    queued_at: datetime = Field(
        default_factory=datetime.utcnow,
        description="When queued for digest"
    )
    niche_id: Optional[str] = Field(
        default=None,
        description="Niche UUID for grouping"
    )


class EngagementEvent(BaseModel):
    """Engagement tracking event.

    Records when users open or click alerts.
    """

    alert_id: uuid.UUID = Field(
        ...,
        description="Alert ID"
    )
    event_type: str = Field(
        ...,
        description="Event type: open, click"
    )
    timestamp: datetime = Field(
        default_factory=datetime.utcnow,
        description="Event timestamp"
    )
    user_agent: Optional[str] = Field(
        default=None,
        description="User agent (for email opens)"
    )
    ip_address: Optional[str] = Field(
        default=None,
        description="IP address (masked for privacy)"
    )
    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Additional event metadata"
    )


class EngagementStats(BaseModel):
    """Engagement statistics for a user.

    Aggregated metrics for the dashboard.
    """

    total_alerts: int = Field(
        default=0,
        ge=0,
        description="Total alerts in period"
    )
    opened: int = Field(
        default=0,
        ge=0,
        description="Number opened"
    )
    clicked: int = Field(
        default=0,
        ge=0,
        description="Number clicked"
    )
    open_rate: float = Field(
        default=0.0,
        ge=0.0,
        le=100.0,
        description="Open rate percentage"
    )
    click_rate: float = Field(
        default=0.0,
        ge=0.0,
        le=100.0,
        description="Click rate percentage"
    )


class SlackMessage(BaseModel):
    """Slack Block Kit message format."""

    blocks: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="Slack Block Kit blocks"
    )
    text: Optional[str] = Field(
        default=None,
        description="Fallback text for notifications"
    )


class EmailContent(BaseModel):
    """Email content for alert delivery."""

    subject: str = Field(
        ...,
        description="Email subject line"
    )
    html_body: str = Field(
        ...,
        description="HTML email body"
    )
    text_body: str = Field(
        ...,
        description="Plain text email body"
    )
    tracking_pixel_url: Optional[str] = Field(
        default=None,
        description="URL for open tracking pixel"
    )
    tracking_link_base: Optional[str] = Field(
        default=None,
        description="Base URL for click tracking redirects"
    )
