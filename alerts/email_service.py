"""
Email Delivery Service

Sends trend alerts via email.
Supports individual alerts and batched digests.
Currently implemented as stub for future email provider integration.
"""

from typing import Optional, List
import uuid
import structlog

from alerts.models import TrendForAlert, EmailContent
from alerts.config import settings


logger = structlog.get_logger(__name__)


class EmailService:
    """Sends trend alerts via email.

    This is a stub implementation that logs emails for development.
    In production, integrate with Resend, SendGrid, or similar provider.

    Email Types:
    - Individual trend alert
    - Batched digest (hourly, daily, weekly)

    Example:
        email = EmailService()

        trend = TrendForAlert(
            id=uuid.uuid4(),
            type="sound",
            name="Trending Sound",
            velocity_score=85,
            saturation_percent=25,
            video_count_current=1500,
            growth_rate=120.5
        )

        success = await email.send_trend_alert(
            to_email="user@example.com",
            trend=trend,
            alert_id=uuid.uuid4()
        )
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        from_email: Optional[str] = None,
        from_name: Optional[str] = None
    ):
        """Initialize email service.

        Args:
            api_key: Email provider API key
            from_email: From email address
            from_name: From display name
        """
        self.api_key = api_key or settings.email_api_key
        self.from_email = from_email or settings.email_from_address
        self.from_name = from_name or settings.email_from_name
        self.provider = settings.email_provider

    async def send_trend_alert(
        self,
        to_email: str,
        trend: TrendForAlert,
        alert_id: Optional[uuid.UUID] = None
    ) -> bool:
        """Send individual trend alert email.

        Args:
            to_email: Recipient email address
            trend: Trend data
            alert_id: Alert ID for tracking

        Returns:
            True if sent successfully
        """
        content = self._render_trend_email(trend, alert_id)

        if self.provider == "stub":
            return await self._send_stub(to_email, content)
        elif self.provider == "resend":
            return await self._send_resend(to_email, content)
        elif self.provider == "sendgrid":
            return await self._send_sendgrid(to_email, content)
        else:
            logger.warning(
                "email_unknown_provider",
                provider=self.provider,
                fallback="stub"
            )
            return await self._send_stub(to_email, content)

    async def send_digest(
        self,
        to_email: str,
        trends: List[TrendForAlert],
        digest_type: str = "daily"
    ) -> bool:
        """Send batched digest email.

        Args:
            to_email: Recipient email address
            trends: List of trends
            digest_type: Type of digest ('hourly', 'daily', 'weekly')

        Returns:
            True if sent successfully
        """
        content = self._render_digest_email(trends, digest_type)

        if self.provider == "stub":
            return await self._send_stub(to_email, content)
        elif self.provider == "resend":
            return await self._send_resend(to_email, content)
        elif self.provider == "sendgrid":
            return await self._send_sendgrid(to_email, content)
        else:
            return await self._send_stub(to_email, content)

    def _render_trend_email(
        self,
        trend: TrendForAlert,
        alert_id: Optional[uuid.UUID] = None
    ) -> EmailContent:
        """Render individual trend alert email.

        Args:
            trend: Trend data
            alert_id: Alert ID for tracking

        Returns:
            EmailContent with rendered email
        """
        trend_url = f"{settings.tracking_base_url}/trends/{trend.id}"
        tracking_pixel = ""
        click_base = settings.tracking_base_url

        # Add tracking if enabled and alert_id provided
        if settings.tracking_pixel_enabled and alert_id:
            tracking_pixel = f"<img src='{click_base}/api/alerts/track/{alert_id}/open' width='1' height='1' />"
            trend_url = f"{click_base}/api/alerts/track/{alert_id}/click?redirect={trend_url}"

        saturation_emoji = self._get_saturation_emoji(trend.saturation_percent)

        subject = f"TREND ALERT: {trend.name[:40]}"

        html_body = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <style>
                body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 30px; border-radius: 10px 10px 0 0; }}
                .content {{ background: #f9fafb; padding: 30px; border-radius: 0 0 10px 10px; }}
                .metric {{ display: inline-block; margin: 10px 20px 10px 0; }}
                .metric-label {{ color: #6b7280; font-size: 12px; text-transform: uppercase; }}
                .metric-value {{ font-size: 24px; font-weight: bold; color: #111827; }}
                .cta-button {{ display: inline-block; background: #667eea; color: white; padding: 12px 24px; border-radius: 6px; text-decoration: none; margin-top: 20px; }}
                .saturation-low {{ color: #10b981; }}
                .saturation-medium {{ color: #f59e0b; }}
                .saturation-high {{ color: #ef4444; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>Trend Alert</h1>
                    <p style="margin: 0; opacity: 0.9;">A new trend is emerging in your tracked niches</p>
                </div>
                <div class="content">
                    <h2 style="margin-top: 0;">{trend.name}</h2>

                    <div class="metric">
                        <div class="metric-label">Velocity Score</div>
                        <div class="metric-value">{trend.velocity_score}/100</div>
                    </div>

                    <div class="metric">
                        <div class="metric-label">Growth Rate</div>
                        <div class="metric-value">+{trend.growth_rate:.1f}%</div>
                    </div>

                    <div class="metric">
                        <div class="metric-label">Videos</div>
                        <div class="metric-value">{trend.video_count_current:,}</div>
                    </div>

                    <div class="metric">
                        <div class="metric-label">Saturation</div>
                        <div class="metric-value {self._get_saturation_class(trend.saturation_percent)}">
                            {saturation_emoji} {trend.saturation_percent}%
                        </div>
                    </div>

                    <div style="margin-top: 20px; padding: 15px; background: white; border-radius: 6px;">
                        <p style="margin: 0; color: #6b7280;">
                            <strong>Trend Type:</strong> {trend.type.title()}<br>
                            <strong>Niche:</strong> {trend.niche_name or 'General'}<br>
                            <strong>Status:</strong> {trend.status.title()}<br>
                            <strong>Window:</strong> ~{trend.window_hours} hours
                        </p>
                    </div>

                    <a href="{trend_url}" class="cta-button">View Trend Details</a>

                    <p style="margin-top: 30px; color: #9ca3af; font-size: 12px;">
                        You're receiving this because you track the #{trend.niche_name or 'General'} niche.
                        <a href="{settings.tracking_base_url}/settings/alerts">Manage alert preferences</a>
                    </p>
                </div>
            </div>
            {tracking_pixel}
        </body>
        </html>
        """

        text_body = f"""
TREND ALERT: {trend.name}

Velocity Score: {trend.velocity_score}/100
Growth Rate: +{trend.growth_rate:.1f}%
Videos: {trend.video_count_current:,}
Saturation: {trend.saturation_percent}%

Trend Type: {trend.type.title()}
Niche: {trend.niche_name or 'General'}
Status: {trend.status.title()}

View Details: {trend_url}

---
You're receiving this because you track the #{trend.niche_name or 'General'} niche.
Manage preferences: {settings.tracking_base_url}/settings/alerts
        """

        return EmailContent(
            subject=subject,
            html_body=html_body.strip(),
            text_body=text_body.strip(),
            tracking_pixel_url=f"{settings.tracking_base_url}/api/alerts/track/{alert_id}/open" if alert_id else None,
            tracking_link_base=settings.tracking_base_url
        )

    def _render_digest_email(
        self,
        trends: List[TrendForAlert],
        digest_type: str
    ) -> EmailContent:
        """Render digest email with multiple trends.

        Args:
            trends: List of trends
            digest_type: Type of digest

        Returns:
            EmailContent with rendered email
        """
        subject = f"Your {digest_type.title()} Trend Digest - {len(trends)} Trends"

        trend_rows = ""
        for i, trend in enumerate(trends[:20]):  # Limit to 20
            saturation_emoji = self._get_saturation_emoji(trend.saturation_percent)
            trend_url = f"{settings.tracking_base_url}/trends/{trend.id}?ref=email_digest"

            trend_rows += f"""
                <tr>
                    <td style="padding: 15px; border-bottom: 1px solid #e5e7eb;">
                        <strong>{trend.name[:50]}</strong><br>
                        <span style="color: #6b7280; font-size: 14px;">
                            Velocity: {trend.velocity_score}/100 |
                            {saturation_emoji} {trend.saturation_percent}% |
                            +{trend.growth_rate:.1f}%
                        </span>
                    </td>
                    <td style="padding: 15px; border-bottom: 1px solid #e5e7eb; text-align: right;">
                        <a href="{trend_url}" style="color: #667eea;">View</a>
                    </td>
                </tr>
            """

        if len(trends) > 20:
            trend_rows += f"""
                <tr>
                    <td colspan="2" style="padding: 15px; text-align: center; color: #6b7280;">
                        ...and {len(trends) - 20} more trends
                    </td>
                </tr>
            """

        html_body = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <style>
                body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 30px; border-radius: 10px 10px 0 0; }}
                .content {{ background: #f9fafb; padding: 20px; border-radius: 0 0 10px 10px; }}
                table {{ width: 100%; border-collapse: collapse; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>{digest_type.title()} Trend Digest</h1>
                    <p style="margin: 0; opacity: 0.9;">{len(trends)} trending alerts in your tracked niches</p>
                </div>
                <div class="content">
                    <table>
                        {trend_rows}
                    </table>
                </div>
            </div>
        </body>
        </html>
        """

        text_body = f"""
{digest_type.upper()} TREND DIGEST
{len(trends)} trending alerts

{chr(10).join(f"- {t.name[:50]} (Velocity: {t.velocity_score}, Saturation: {t.saturation_percent}%)" for t in trends[:10])}

---
Manage preferences: {settings.tracking_base_url}/settings/alerts
        """

        return EmailContent(
            subject=subject,
            html_body=html_body.strip(),
            text_body=text_body.strip()
        )

    def _get_saturation_emoji(self, saturation: int) -> str:
        """Get emoji for saturation level."""
        if saturation < 30:
            return "🟢"
        elif saturation < 70:
            return "🟡"
        else:
            return "🔴"

    def _get_saturation_class(self, saturation: int) -> str:
        """Get CSS class for saturation level."""
        if saturation < 30:
            return "saturation-low"
        elif saturation < 70:
            return "saturation-medium"
        else:
            return "saturation-high"

    async def _send_stub(
        self,
        to_email: str,
        content: EmailContent
    ) -> bool:
        """Stub implementation for development.

        Logs email content instead of sending.

        Args:
            to_email: Recipient email
            content: Email content

        Returns:
            Always True (simulated success)
        """
        # Mask email for privacy
        masked_email = self._mask_email(to_email)

        logger.info(
            "email_stub_sent",
            to=masked_email,
            subject=content.subject,
            provider="stub"
        )

        # In development, log the email for debugging
        logger.debug(
            "email_stub_content",
            to=masked_email,
            subject=content.subject,
            html_length=len(content.html_body),
            text_length=len(content.text_body)
        )

        return True

    async def _send_resend(
        self,
        to_email: str,
        content: EmailContent
    ) -> bool:
        """Send email via Resend API.

        Args:
            to_email: Recipient email
            content: Email content

        Returns:
            True if sent successfully
        """
        try:
            import resend

            resend.api_key = self.api_key

            r = resend.Emails.send({
                "from": f"{self.from_name} <{self.from_email}>",
                "to": [to_email],
                "subject": content.subject,
                "html": content.html_body,
                "text": content.text_body
            })

            logger.info(
                "email_resend_sent",
                to=self._mask_email(to_email),
                subject=content.subject,
                email_id=r.get("id")
            )
            return True

        except Exception as e:
            logger.error(
                "email_resend_failed",
                to=self._mask_email(to_email),
                error=self._sanitize_error(str(e))
            )
            return False

    async def _send_sendgrid(
        self,
        to_email: str,
        content: EmailContent
    ) -> bool:
        """Send email via SendGrid API.

        Args:
            to_email: Recipient email
            content: Email content

        Returns:
            True if sent successfully
        """
        try:
            from sendgrid import SendGridAPIClient
            from sendgrid.helpers.mail import Mail

            message = Mail(
                from_email=self.from_email,
                to_emails=to_email,
                subject=content.subject,
                html_content=content.html_body,
                plain_text_content=content.text_body
            )

            sg = SendGridAPIClient(self.api_key)
            response = sg.send(message)

            logger.info(
                "email_sendgrid_sent",
                to=self._mask_email(to_email),
                subject=content.subject,
                status_code=response.status_code
            )
            return response.status_code in (200, 201, 202)

        except Exception as e:
            logger.error(
                "email_sendgrid_failed",
                to=self._mask_email(to_email),
                error=self._sanitize_error(str(e))
            )
            return False

    def _sanitize_error(self, error: str) -> str:
        """Sanitize error messages to remove potential API keys.
        
        Args:
            error: Raw error message
            
        Returns:
            Sanitized error message with API keys redacted
        """
        import re
        
        # Mask common API key patterns
        patterns = [
            (r'[a-zA-Z0-9]{32,64}', '***KEY_REDACTED***'),  # Generic long keys
            (r'sk_[a-zA-Z0-9]{24,}', '***STRIPE_KEY_REDACTED***'),  # Stripe keys
            (r'sg_[a-zA-Z0-9_-]{20,}', '***SENDGRID_KEY_REDACTED***'),  # SendGrid
            (r're_[a-zA-Z0-9_-]{20,}', '***RESEND_KEY_REDACTED***'),  # Resend
        ]
        
        sanitized = error
        for pattern, replacement in patterns:
            sanitized = re.sub(pattern, replacement, sanitized)
        
        return sanitized

    def _mask_email(self, email: str) -> str:
        """Mask email for privacy in logs.

        Args:
            email: Email address

        Returns:
            Masked email string
        """
        if not email or "@" not in email:
            return "<invalid>"

        local, domain = email.split("@", 1)
        masked_local = local[0] + "***" if len(local) > 1 else "***"
        
        # Also mask domain for additional privacy
        domain_parts = domain.split(".")
        if len(domain_parts) > 1:
            masked_domain = f"***.{domain_parts[-1]}"
        else:
            masked_domain = "***"

        return f"{masked_local}@{masked_domain}"


# Singleton instance
_email_service: EmailService | None = None


def get_email_service() -> EmailService:
    """Get the singleton EmailService instance."""
    global _email_service
    if _email_service is None:
        _email_service = EmailService()
    return _email_service
