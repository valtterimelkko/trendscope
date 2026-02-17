"""
Engagement Tracking Service

Tracks alert engagement for analytics.
Records when users open emails or click alert links.
"""

from datetime import datetime
from typing import Optional, List, Dict, Any
import uuid
import structlog

from alerts.models import EngagementEvent, EngagementStats, AlertStatus
from alerts.config import settings


logger = structlog.get_logger(__name__)


class EngagementTracker:
    """Tracks when users open/click alerts.

    Provides methods for recording and querying engagement events.
    Events are persisted to the database via the alerts table.

    Example:
        tracker = EngagementTracker(db_pool)

        # Record email open
        await tracker.record_opened(alert_id)

        # Record link click
        await tracker.record_clicked(alert_id)

        # Get engagement stats
        stats = await tracker.get_engagement_stats(user_id)
    """

    def __init__(self, db_pool):
        """Initialize engagement tracker.

        Args:
            db_pool: Database connection pool (asyncpg)
        """
        self.db = db_pool

    async def record_sent(self, alert_id: uuid.UUID) -> bool:
        """Record that alert was sent.

        Updates alert status to 'sent' and sets sent_at timestamp.

        Args:
            alert_id: Alert UUID

        Returns:
            True if updated successfully
        """
        try:
            await self.db.execute("""
                UPDATE alerts
                SET status = 'sent', sent_at = NOW()
                WHERE id = $1
            """, alert_id)

            logger.debug(
                "engagement_recorded_sent",
                alert_id=str(alert_id)
            )

            return True

        except Exception as e:
            logger.error(
                "engagement_record_sent_failed",
                alert_id=str(alert_id),
                error=str(e)
            )
            return False

    async def record_opened(
        self,
        alert_id: uuid.UUID,
        user_agent: Optional[str] = None,
        ip_address: Optional[str] = None
    ) -> bool:
        """Record that alert was opened.

        Updates alert with opened_at timestamp.
        This is typically called by the tracking pixel endpoint.

        Args:
            alert_id: Alert UUID
            user_agent: Optional user agent string
            ip_address: Optional IP address (should be masked)

        Returns:
            True if recorded successfully
        """
        try:
            # Only update if not already opened (prevent duplicate tracking)
            result = await self.db.fetchrow("""
                UPDATE alerts
                SET opened_at = COALESCE(opened_at, NOW()),
                    status = CASE
                        WHEN status = 'sent' THEN 'delivered'
                        ELSE status
                    END
                WHERE id = $1
                AND opened_at IS NULL
                RETURNING id
            """, alert_id)

            if result:
                logger.info(
                    "engagement_recorded_opened",
                    alert_id=str(alert_id),
                    user_agent=user_agent[:50] if user_agent else None,
                    ip_masked=self._mask_ip(ip_address) if ip_address else None
                )

            return True

        except Exception as e:
            logger.error(
                "engagement_record_opened_failed",
                alert_id=str(alert_id),
                error=str(e)
            )
            return False

    async def record_clicked(
        self,
        alert_id: uuid.UUID,
        redirect_url: Optional[str] = None
    ) -> bool:
        """Record that alert link was clicked.

        Updates alert with clicked_at timestamp.

        Args:
            alert_id: Alert UUID
            redirect_url: URL being redirected to (for logging)

        Returns:
            True if recorded successfully
        """
        try:
            result = await self.db.fetchrow("""
                UPDATE alerts
                SET clicked_at = COALESCE(clicked_at, NOW()),
                    status = 'delivered'
                WHERE id = $1
                AND clicked_at IS NULL
                RETURNING id
            """, alert_id)

            if result:
                logger.info(
                    "engagement_recorded_clicked",
                    alert_id=str(alert_id),
                    redirect_domain=self._extract_domain(redirect_url) if redirect_url else None
                )

            return True

        except Exception as e:
            logger.error(
                "engagement_record_clicked_failed",
                alert_id=str(alert_id),
                error=str(e)
            )
            return False

    async def get_engagement_stats(
        self,
        user_id: uuid.UUID,
        days: int = 30
    ) -> EngagementStats:
        """Get engagement statistics for a user.

        Args:
            user_id: User UUID
            days: Number of days to look back (default 30)

        Returns:
            EngagementStats with metrics
        """
        try:
            row = await self.db.fetchrow("""
                SELECT
                    COUNT(*) as total_alerts,
                    COUNT(opened_at) as opened,
                    COUNT(clicked_at) as clicked
                FROM alerts
                WHERE user_id = $1
                AND created_at > NOW() - INTERVAL '%s days'
            """ % days, user_id)

            if row and row["total_alerts"] > 0:
                total = row["total_alerts"]
                opened = row["opened"] or 0
                clicked = row["clicked"] or 0

                return EngagementStats(
                    total_alerts=total,
                    opened=opened,
                    clicked=clicked,
                    open_rate=round((opened / total) * 100, 1),
                    click_rate=round((clicked / total) * 100, 1)
                )

            return EngagementStats()

        except Exception as e:
            logger.error(
                "engagement_stats_failed",
                user_id=str(user_id),
                error=str(e)
            )
            return EngagementStats()

    async def get_engagement_by_niche(
        self,
        user_id: uuid.UUID,
        days: int = 30
    ) -> List[Dict[str, Any]]:
        """Get engagement statistics grouped by niche.

        Args:
            user_id: User UUID
            days: Number of days to look back

        Returns:
            List of dicts with niche engagement data
        """
        try:
            rows = await self.db.fetch("""
                SELECT
                    n.name as niche_name,
                    n.id as niche_id,
                    COUNT(a.id) as total_alerts,
                    COUNT(a.opened_at) as opened,
                    COUNT(a.clicked_at) as clicked
                FROM alerts a
                JOIN trends t ON a.trend_id = t.id
                LEFT JOIN niches n ON t.niche_id = n.id
                WHERE a.user_id = $1
                AND a.created_at > NOW() - INTERVAL '%s days'
                GROUP BY n.id, n.name
                ORDER BY total_alerts DESC
            """ % days, user_id)

            result = []
            for row in rows:
                total = row["total_alerts"] or 0
                opened = row["opened"] or 0
                clicked = row["clicked"] or 0

                result.append({
                    "niche_id": str(row["niche_id"]) if row["niche_id"] else None,
                    "niche_name": row["niche_name"] or "General",
                    "total_alerts": total,
                    "opened": opened,
                    "clicked": clicked,
                    "open_rate": round((opened / total) * 100, 1) if total > 0 else 0,
                    "click_rate": round((clicked / total) * 100, 1) if total > 0 else 0
                })

            return result

        except Exception as e:
            logger.error(
                "engagement_by_niche_failed",
                user_id=str(user_id),
                error=str(e)
            )
            return []

    async def get_recent_engagement_events(
        self,
        user_id: uuid.UUID,
        limit: int = 50
    ) -> List[EngagementEvent]:
        """Get recent engagement events for a user.

        Args:
            user_id: User UUID
            limit: Maximum events to return

        Returns:
            List of EngagementEvent objects
        """
        try:
            rows = await self.db.fetch("""
                SELECT
                    a.id as alert_id,
                    a.sent_at,
                    a.opened_at,
                    a.clicked_at,
                    t.name as trend_name
                FROM alerts a
                JOIN trends t ON a.trend_id = t.id
                WHERE a.user_id = $1
                AND (a.opened_at IS NOT NULL OR a.clicked_at IS NOT NULL)
                ORDER BY COALESCE(a.clicked_at, a.opened_at) DESC
                LIMIT $2
            """, user_id, limit)

            events = []
            for row in rows:
                # Create open event if opened
                if row["opened_at"]:
                    events.append(EngagementEvent(
                        alert_id=row["alert_id"],
                        event_type="open",
                        timestamp=row["opened_at"],
                        metadata={"trend_name": row["trend_name"]}
                    ))

                # Create click event if clicked
                if row["clicked_at"]:
                    events.append(EngagementEvent(
                        alert_id=row["alert_id"],
                        event_type="click",
                        timestamp=row["clicked_at"],
                        metadata={"trend_name": row["trend_name"]}
                    ))

            return events

        except Exception as e:
            logger.error(
                "engagement_events_failed",
                user_id=str(user_id),
                error=str(e)
            )
            return []

    async def get_alert_engagement(self, alert_id: uuid.UUID) -> Optional[Dict]:
        """Get engagement data for a specific alert.

        Args:
            alert_id: Alert UUID

        Returns:
            Dict with engagement data or None
        """
        try:
            row = await self.db.fetchrow("""
                SELECT
                    id,
                    status,
                    sent_at,
                    opened_at,
                    clicked_at,
                    EXTRACT(EPOCH FROM (opened_at - sent_at)) as time_to_open_seconds,
                    EXTRACT(EPOCH FROM (clicked_at - sent_at)) as time_to_click_seconds
                FROM alerts
                WHERE id = $1
            """, alert_id)

            if row:
                return {
                    "alert_id": str(row["id"]),
                    "status": row["status"],
                    "sent_at": row["sent_at"].isoformat() if row["sent_at"] else None,
                    "opened_at": row["opened_at"].isoformat() if row["opened_at"] else None,
                    "clicked_at": row["clicked_at"].isoformat() if row["clicked_at"] else None,
                    "time_to_open_seconds": row["time_to_open_seconds"],
                    "time_to_click_seconds": row["time_to_click_seconds"],
                    "is_opened": row["opened_at"] is not None,
                    "is_clicked": row["clicked_at"] is not None
                }

            return None

        except Exception as e:
            logger.error(
                "alert_engagement_failed",
                alert_id=str(alert_id),
                error=str(e)
            )
            return None

    async def get_global_engagement_stats(self, days: int = 7) -> Dict:
        """Get global engagement statistics across all users.

        Useful for admin dashboards and system monitoring.

        Args:
            days: Number of days to look back

        Returns:
            Dict with global stats
        """
        try:
            row = await self.db.fetchrow("""
                SELECT
                    COUNT(*) as total_alerts,
                    COUNT(opened_at) as total_opened,
                    COUNT(clicked_at) as total_clicked,
                    COUNT(DISTINCT user_id) as unique_users
                FROM alerts
                WHERE created_at > NOW() - INTERVAL '%s days'
            """ % days)

            total = row["total_alerts"] or 0
            opened = row["total_opened"] or 0
            clicked = row["total_clicked"] or 0

            return {
                "period_days": days,
                "total_alerts": total,
                "total_opened": opened,
                "total_clicked": clicked,
                "unique_users": row["unique_users"] or 0,
                "open_rate": round((opened / total) * 100, 1) if total > 0 else 0,
                "click_rate": round((clicked / total) * 100, 1) if total > 0 else 0
            }

        except Exception as e:
            logger.error(
                "global_engagement_stats_failed",
                error=str(e)
            )
            return {
                "period_days": days,
                "total_alerts": 0,
                "total_opened": 0,
                "total_clicked": 0,
                "unique_users": 0,
                "open_rate": 0,
                "click_rate": 0
            }

    def _mask_ip(self, ip_address: str) -> str:
        """Mask IP address for privacy.

        Args:
            ip_address: Full IP address

        Returns:
            Masked IP (e.g., "192.168.***.***")
        """
        if not ip_address:
            return "<empty>"

        parts = ip_address.split(".")
        if len(parts) == 4:
            return f"{parts[0]}.{parts[1]}.***.***"

        return "***masked***"

    def _extract_domain(self, url: str) -> str:
        """Extract domain from URL for logging.

        Args:
            url: Full URL

        Returns:
            Domain only
        """
        if not url:
            return "<empty>"

        try:
            # Simple extraction without urllib for speed
            if "://" in url:
                url = url.split("://", 1)[1]
            domain = url.split("/", 1)[0]
            return domain[:50]  # Limit length
        except Exception:
            return "<invalid>"


# Singleton instance
_engagement_tracker: EngagementTracker | None = None


def get_engagement_tracker(db_pool=None) -> EngagementTracker:
    """Get the singleton EngagementTracker instance.

    Args:
        db_pool: Database pool (required on first call)

    Returns:
        EngagementTracker instance
    """
    global _engagement_tracker
    if _engagement_tracker is None:
        if db_pool is None:
            raise ValueError("Database pool required for first initialization")
        _engagement_tracker = EngagementTracker(db_pool)
    return _engagement_tracker
