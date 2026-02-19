"""
Slack Delivery Service

Sends trend alerts to Slack channels via webhooks.
Formats messages using Slack Block Kit for rich display.
"""

from typing import Optional, Dict, Any, List
import uuid
import httpx
import structlog

from alerts.models import TrendForAlert, SlackMessage
from alerts.config import settings


logger = structlog.get_logger(__name__)


class SlackService:
    """Sends trend alerts to Slack webhooks.

    Supports two message formats:
    - detailed: Full Block Kit message with all trend info
    - compact: Simplified message for digest batches

    Example:
        slack = SlackService()

        trend = TrendForAlert(
            id=uuid.uuid4(),
            type="sound",
            name="Trending Sound",
            velocity_score=85,
            saturation_percent=25,
            video_count_current=1500,
            growth_rate=120.5
        )

        success = await slack.send_trend_alert(
            webhook_url="https://hooks.slack.com/...",
            trend=trend
        )
    """

    # Base URL for trend details
    TREND_BASE_URL = "https://trendscope.io/trends"

    def __init__(
        self,
        timeout: Optional[float] = None,
        max_retries: Optional[int] = None
    ):
        """Initialize Slack service.

        Args:
            timeout: Request timeout in seconds
            max_retries: Maximum retry attempts
        """
        self.timeout = timeout or settings.slack_timeout_seconds
        self.max_retries = max_retries or settings.slack_max_retries

    async def send_trend_alert(
        self,
        webhook_url: str,
        trend: TrendForAlert,
        format: str = "detailed",
        alert_id: Optional[uuid.UUID] = None
    ) -> bool:
        """Send trend alert to Slack webhook.

        Args:
            webhook_url: Slack webhook URL
            trend: Trend data to send
            format: Message format ('detailed' or 'compact')
            alert_id: Optional alert ID for tracking

        Returns:
            True if sent successfully
        """
        if format == "compact":
            message = self._format_compact(trend, alert_id)
        else:
            message = self._format_detailed(trend, alert_id)

        return await self._send_webhook(webhook_url, message.model_dump(exclude_none=True))

    async def send_digest(
        self,
        webhook_url: str,
        trends: List[TrendForAlert],
        digest_type: str = "daily"
    ) -> bool:
        """Send digest message with multiple trends.

        Args:
            webhook_url: Slack webhook URL
            trends: List of trends to include
            digest_type: Type of digest ('hourly', 'daily', 'weekly')

        Returns:
            True if sent successfully
        """
        message = self._format_digest(trends, digest_type)
        return await self._send_webhook(webhook_url, message.model_dump(exclude_none=True))

    def _format_detailed(
        self,
        trend: TrendForAlert,
        alert_id: Optional[uuid.UUID] = None
    ) -> SlackMessage:
        """Format detailed Slack message using Block Kit.

        Args:
            trend: Trend data
            alert_id: Optional alert ID for tracking

        Returns:
            SlackMessage with Block Kit blocks
        """
        saturation_emoji = self._get_saturation_emoji(trend.saturation_percent)
        trend_url = f"{self.TREND_BASE_URL}/{trend.id}"

        # Add tracking params if alert_id provided
        if alert_id:
            trend_url = f"{trend_url}?ref=slack&alert_id={alert_id}"

        blocks = [
            # Header
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": f"TREND ALERT: {trend.name[:50]}",
                    "emoji": True
                }
            },
            # Main info section
            {
                "type": "section",
                "fields": [
                    {
                        "type": "mrkdwn",
                        "text": f"*Niche:*\n#{trend.niche_name or 'General'}"
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"*Growth:*\n+{trend.growth_rate:.1f}% in 3hrs"
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"*Videos:*\n{trend.video_count_current:,}"
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"*Saturation:*\n{saturation_emoji} {trend.saturation_percent}%"
                    }
                ]
            },
            # Velocity section
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*Velocity Score:* {trend.velocity_score}/100\n*Window:* ~{trend.window_hours} hours"
                }
            },
            # Action button
            {
                "type": "actions",
                "elements": [
                    {
                        "type": "button",
                        "text": {
                            "type": "plain_text",
                            "text": "View Details"
                        },
                        "url": trend_url,
                        "action_id": "view_trend_details"
                    }
                ]
            }
        ]

        # Add context with trend type
        blocks.append({
            "type": "context",
            "elements": [
                {
                    "type": "mrkdwn",
                    "text": f"Trend type: *{trend.type.title()}* | Status: *{trend.status.title()}*"
                }
            ]
        })

        return SlackMessage(
            blocks=blocks,
            text=f"TREND ALERT: {trend.name}"
        )

    def _format_compact(
        self,
        trend: TrendForAlert,
        alert_id: Optional[uuid.UUID] = None
    ) -> SlackMessage:
        """Format compact Slack message for digest.

        Args:
            trend: Trend data
            alert_id: Optional alert ID

        Returns:
            SlackMessage with minimal blocks
        """
        saturation_emoji = self._get_saturation_emoji(trend.saturation_percent)
        trend_url = f"{self.TREND_BASE_URL}/{trend.id}"

        if alert_id:
            trend_url = f"{trend_url}?ref=slack&alert_id={alert_id}"

        blocks = [
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*{trend.name[:60]}* | Velocity: {trend.velocity_score} | {saturation_emoji} {trend.saturation_percent}%"
                },
                "accessory": {
                    "type": "button",
                    "text": {
                        "type": "plain_text",
                        "text": "View"
                    },
                    "url": trend_url
                }
            }
        ]

        return SlackMessage(
            blocks=blocks,
            text=f"Trend: {trend.name}"
        )

    def _format_digest(
        self,
        trends: List[TrendForAlert],
        digest_type: str
    ) -> SlackMessage:
        """Format digest message with multiple trends.

        Args:
            trends: List of trends
            digest_type: Type of digest

        Returns:
            SlackMessage with digest blocks
        """
        digest_emoji = {
            "hourly": ":clock1:",
            "daily": ":calendar:",
            "weekly": ":calendar_week:"
        }

        emoji = digest_emoji.get(digest_type, ":bell:")

        blocks = [
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": f"{emoji} Your {digest_type.title()} Trend Digest",
                    "emoji": True
                }
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*{len(trends)} trending alerts* in your tracked niches:"
                }
            },
            {"type": "divider"}
        ]

        # Add top trends (limit to 10 for readability)
        for trend in trends[:10]:
            saturation_emoji = self._get_saturation_emoji(trend.saturation_percent)
            trend_url = f"{self.TREND_BASE_URL}/{trend.id}?ref=slack_digest"

            blocks.append({
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*{trend.name[:50]}*\n:{trend.type}: Velocity: {trend.velocity_score}/100 | {saturation_emoji} {trend.saturation_percent}% saturated"
                },
                "accessory": {
                    "type": "button",
                    "text": {
                        "type": "plain_text",
                        "text": "View"
                    },
                    "url": trend_url
                }
            })

        if len(trends) > 10:
            blocks.append({
                "type": "context",
                "elements": [
                    {
                        "type": "mrkdwn",
                        "text": f"_...and {len(trends) - 10} more trends_"
                    }
                ]
            })

        # Footer
        blocks.append({"type": "divider"})
        blocks.append({
            "type": "context",
            "elements": [
                {
                    "type": "mrkdwn",
                    "text": f"<{self.TREND_BASE_URL.replace('/trends', '')}|Trendscope> | The Bloomberg Terminal for TikTok Trends"
                }
            ]
        })

        return SlackMessage(
            blocks=blocks,
            text=f"Your {digest_type} trend digest: {len(trends)} trends"
        )

    def _get_saturation_emoji(self, saturation: int) -> str:
        """Get emoji for saturation level.

        Args:
            saturation: Saturation percentage (0-100)

        Returns:
            Emoji string
        """
        if saturation < 30:
            return ":green_circle:"  # Low - good opportunity
        elif saturation < 70:
            return ":yellow_circle:"  # Medium - still viable
        else:
            return ":red_circle:"  # High - may be saturated

    async def _send_webhook(
        self,
        webhook_url: str,
        payload: Dict[str, Any]
    ) -> bool:
        """Send webhook request to Slack.

        Args:
            webhook_url: Slack webhook URL
            payload: Message payload

        Returns:
            True if successful
        """
        # Mask webhook URL for logging
        masked_url = self._mask_webhook_url(webhook_url)

        for attempt in range(1, self.max_retries + 1):
            try:
                async with httpx.AsyncClient(timeout=self.timeout) as client:
                    response = await client.post(
                        webhook_url,
                        json=payload
                    )

                    if response.status_code == 200:
                        logger.info(
                            "slack_delivery_success",
                            masked_url=masked_url,
                            attempt=attempt
                        )
                        return True

                    # Non-200 response
                    logger.warning(
                        "slack_delivery_failed",
                        masked_url=masked_url,
                        status_code=response.status_code,
                        response_text=response.text[:200],
                        attempt=attempt
                    )

            except httpx.TimeoutException:
                logger.warning(
                    "slack_delivery_timeout",
                    masked_url=masked_url,
                    attempt=attempt,
                    timeout=self.timeout
                )

            except httpx.RequestError as e:
                logger.error(
                    "slack_delivery_error",
                    masked_url=masked_url,
                    error=str(e),
                    attempt=attempt
                )

            # Retry delay (exponential backoff)
            if attempt < self.max_retries:
                import asyncio
                await asyncio.sleep(2 ** attempt)

        logger.error(
            "slack_delivery_failed_final",
            masked_url=masked_url,
            max_retries=self.max_retries
        )
        return False

    async def test_webhook(self, webhook_url: str) -> Dict[str, Any]:
        """Test a Slack webhook connection.

        Sends a test message to verify webhook is valid.

        Args:
            webhook_url: Slack webhook URL to test

        Returns:
            Dict with test result
        """
        test_message = SlackMessage(
            blocks=[
                {
                    "type": "header",
                    "text": {
                        "type": "plain_text",
                        "text": "Trendscope Connection Test",
                        "emoji": True
                    }
                },
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": "Your Slack integration is working correctly! You'll receive trend alerts here."
                    }
                }
            ],
            text="Trendscope Connection Test"
        )

        success = await self._send_webhook(
            webhook_url,
            test_message.model_dump(exclude_none=True)
        )

        return {
            "success": success,
            "message": "Test alert sent successfully" if success else "Failed to send test alert"
        }

    def _mask_webhook_url(self, url: str) -> str:
        """Mask webhook URL for safe logging.

        Args:
            url: Full webhook URL

        Returns:
            Masked URL string with all sensitive parts hidden
        """
        if not url:
            return "<empty>"

        from urllib.parse import urlparse
        try:
            parsed = urlparse(url)
            # Only show the service name (e.g., "hooks.slack.com")
            return f"{parsed.scheme}://{parsed.netloc}/***"
        except Exception:
            return "***masked***"


# Singleton instance
_slack_service: SlackService | None = None


def get_slack_service() -> SlackService:
    """Get the singleton SlackService instance."""
    global _slack_service
    if _slack_service is None:
        _slack_service = SlackService()
    return _slack_service
