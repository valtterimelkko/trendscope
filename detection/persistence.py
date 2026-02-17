"""
Trend Repository - PostgreSQL Persistence Layer

Handles all database operations for trends and velocity history.
Uses asyncpg for async PostgreSQL operations.

Tables:
- trends: Main trend records
- trend_velocity_history: Time-series velocity snapshots
"""

import asyncpg
from typing import Optional, List
from datetime import datetime
import uuid
import json

from detection.models import (
    Trend,
    TrendType,
    TrendStatus,
    TrendVelocityHistory
)
from detection.config import settings
from detection.logging_config import get_logger

logger = get_logger(__name__)


class TrendRepository:
    """
    Database repository for trend operations.

    Provides async methods for CRUD operations on trends
    and velocity history. Uses asyncpg connection pool.

    All methods are designed to be used with async/await.
    """

    def __init__(self, pool: asyncpg.Pool):
        """
        Initialize repository with database pool.

        Args:
            pool: asyncpg connection pool
        """
        self.pool = pool

    @classmethod
    async def create(cls, database_url: str) -> "TrendRepository":
        """
        Create repository with connection pool.

        Factory method that creates a connection pool and
        returns a new repository instance.

        Args:
            database_url: PostgreSQL connection URL

        Returns:
            TrendRepository instance with initialized pool
        """
        pool = await asyncpg.create_pool(
            database_url,
            min_size=2,
            max_size=settings.database_pool_size,
            max_overflow=settings.database_max_overflow
        )
        return cls(pool)

    async def close(self) -> None:
        """Close database connection pool."""
        await self.pool.close()

    async def get_by_platform_id(
        self,
        trend_type: TrendType,
        platform_id: str
    ) -> Optional[Trend]:
        """
        Get trend by type and platform ID.

        This is the primary lookup for trend deduplication.
        Uses the unique constraint on (type, platform_id).

        Args:
            trend_type: Type of trend (sound, hashtag, format)
            platform_id: TikTok's internal ID for the trend

        Returns:
            Trend if found, None otherwise
        """
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow(
                """
                SELECT * FROM trends
                WHERE type = $1 AND platform_id = $2
                """,
                trend_type.value,
                platform_id
            )

            if row:
                return self._row_to_trend(row)
            return None

    async def get_by_id(self, trend_id: uuid.UUID) -> Optional[Trend]:
        """
        Get trend by UUID.

        Args:
            trend_id: Trend UUID

        Returns:
            Trend if found, None otherwise
        """
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow(
                "SELECT * FROM trends WHERE id = $1",
                trend_id
            )

            if row:
                return self._row_to_trend(row)
            return None

    async def get_trends(
        self,
        status: Optional[TrendStatus] = None,
        niche_id: Optional[uuid.UUID] = None,
        limit: int = 20,
        offset: int = 0,
        order_by: str = "velocity_score DESC"
    ) -> List[Trend]:
        """
        Get trends with optional filtering.

        Used for API endpoints to list trends.

        Args:
            status: Filter by status (optional)
            niche_id: Filter by niche (optional)
            limit: Maximum results (default 20, max 100)
            offset: Result offset for pagination
            order_by: Order clause (default: velocity_score DESC)

        Returns:
            List of matching trends
        """
        limit = min(limit, 100)  # Cap at 100
        conditions = []
        params = []
        param_idx = 1

        if status:
            conditions.append(f"status = ${param_idx}")
            params.append(status.value)
            param_idx += 1

        if niche_id:
            conditions.append(f"niche_id = ${param_idx}")
            params.append(niche_id)
            param_idx += 1

        where_clause = " AND ".join(conditions) if conditions else "true"

        # Validate order_by to prevent SQL injection
        valid_columns = {
            "velocity_score", "saturation_percent", "first_detected_at",
            "video_count_current", "growth_rate", "name"
        }
        order_parts = order_by.split()
        if order_parts[0] not in valid_columns:
            order_by = "velocity_score DESC"

        query = f"""
            SELECT * FROM trends
            WHERE {where_clause}
            ORDER BY {order_by}
            LIMIT ${param_idx} OFFSET ${param_idx + 1}
        """
        params.extend([limit, offset])

        async with self.pool.acquire() as conn:
            rows = await conn.fetch(query, *params)
            return [self._row_to_trend(row) for row in rows]

    async def create(self, trend: Trend) -> Trend:
        """
        Create new trend record.

        Uses ON CONFLICT DO NOTHING to handle duplicates gracefully
        based on the unique constraint (type, platform_id).

        Args:
            trend: Trend model to create

        Returns:
            Created trend (or existing trend if duplicate)
        """
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow(
                """
                INSERT INTO trends (
                    id, type, name, platform_id, niche_id,
                    first_detected_at, peak_detected_at, status,
                    velocity_score, saturation_percent,
                    video_count_start, video_count_current,
                    growth_rate, metadata, created_at, updated_at
                ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15, $16)
                ON CONFLICT (type, platform_id) DO NOTHING
                RETURNING *
                """,
                trend.id,
                trend.type.value,
                trend.name,
                trend.platform_id,
                trend.niche_id,
                trend.first_detected_at,
                trend.peak_detected_at,
                trend.status.value,
                trend.velocity_score,
                trend.saturation_percent,
                trend.video_count_start,
                trend.video_count_current,
                trend.growth_rate,
                json.dumps(trend.metadata),
                trend.created_at,
                trend.updated_at
            )

            if row:
                logger.info(
                    "trend_created",
                    trend_id=str(trend.id),
                    type=trend.type.value,
                    name=trend.name,
                    velocity_score=trend.velocity_score
                )
                return self._row_to_trend(row)

            # If conflict occurred, return existing trend
            logger.debug(
                "trend_already_exists",
                type=trend.type.value,
                platform_id=trend.platform_id
            )
            existing = await self.get_by_platform_id(trend.type, trend.platform_id)
            return existing or trend

    async def update(
        self,
        trend_id: uuid.UUID,
        updates: dict
    ) -> Trend:
        """
        Update trend record.

        Dynamically builds update query based on provided fields.
        Automatically updates updated_at timestamp.

        Args:
            trend_id: UUID of trend to update
            updates: Dict of fields to update

        Returns:
            Updated trend record

        Raises:
            ValueError: If trend not found
        """
        if not updates:
            raise ValueError("No updates provided")

        async with self.pool.acquire() as conn:
            # Build dynamic update query
            set_clauses = ["updated_at = NOW()"]  # Always update timestamp
            values = [trend_id]
            param_idx = 2

            for key, value in updates.items():
                # Convert enum values to strings
                if isinstance(value, TrendStatus):
                    value = value.value
                elif isinstance(value, TrendType):
                    value = value.value

                set_clauses.append(f"{key} = ${param_idx}")
                values.append(value)
                param_idx += 1

            query = f"""
                UPDATE trends
                SET {', '.join(set_clauses)}
                WHERE id = $1
                RETURNING *
            """

            row = await conn.fetchrow(query, *values)

            if not row:
                raise ValueError(f"Trend not found: {trend_id}")

            logger.debug(
                "trend_updated",
                trend_id=str(trend_id),
                updated_fields=list(updates.keys())
            )

            return self._row_to_trend(row)

    async def record_velocity_history(
        self,
        trend_id: uuid.UUID,
        timestamp: datetime,
        video_count: int,
        velocity_score: int,
        growth_rate: float,
        saturation_percent: int
    ) -> None:
        """
        Record velocity history for time-series analysis.

        Creates a snapshot of trend metrics at a point in time.
        Used for historical graphs and trend analysis.

        Args:
            trend_id: UUID of the trend
            timestamp: When this snapshot was taken
            video_count: Video count at this time
            velocity_score: Velocity score at this time
            growth_rate: Growth rate at this time
            saturation_percent: Saturation at this time
        """
        async with self.pool.acquire() as conn:
            await conn.execute(
                """
                INSERT INTO trend_velocity_history (
                    trend_id, timestamp, video_count,
                    velocity_score, growth_rate, saturation_percent
                ) VALUES ($1, $2, $3, $4, $5, $6)
                """,
                trend_id,
                timestamp,
                video_count,
                velocity_score,
                growth_rate,
                saturation_percent
            )

        logger.debug(
            "velocity_history_recorded",
            trend_id=str(trend_id),
            velocity_score=velocity_score
        )

    async def get_velocity_history(
        self,
        trend_id: uuid.UUID,
        hours: int = 24
    ) -> List[TrendVelocityHistory]:
        """
        Get velocity history for a trend.

        Retrieves historical snapshots within the specified time window.

        Args:
            trend_id: UUID of the trend
            hours: Hours of history to retrieve (default 24)

        Returns:
            List of velocity history records, ordered by timestamp ascending
        """
        async with self.pool.acquire() as conn:
            rows = await conn.fetch(
                """
                SELECT * FROM trend_velocity_history
                WHERE trend_id = $1
                AND timestamp > NOW() - INTERVAL '1 hour' * $2
                ORDER BY timestamp ASC
                """,
                trend_id,
                hours
            )

            return [
                TrendVelocityHistory(
                    id=row["id"],
                    trend_id=row["trend_id"],
                    timestamp=row["timestamp"],
                    video_count=row["video_count"],
                    velocity_score=row["velocity_score"],
                    growth_rate=float(row["growth_rate"]) if row["growth_rate"] else None,
                    saturation_percent=row["saturation_percent"]
                )
                for row in rows
            ]

    async def cleanup_old_velocity_history(self, hours: int = 168) -> int:
        """
        Clean up old velocity history records.

        Removes records older than the specified retention period.
        Should be called periodically to manage database size.

        Args:
            hours: Retention period in hours (default 168 = 7 days)

        Returns:
            Number of records deleted
        """
        async with self.pool.acquire() as conn:
            result = await conn.execute(
                """
                DELETE FROM trend_velocity_history
                WHERE timestamp < NOW() - INTERVAL '1 hour' * $1
                """,
                hours
            )
            # asyncpg returns "DELETE N" format
            deleted = int(result.split()[-1]) if result else 0

            if deleted > 0:
                logger.info(
                    "velocity_history_cleaned",
                    deleted_count=deleted,
                    retention_hours=hours
                )

            return deleted

    async def get_active_trend_count(self) -> dict:
        """
        Get count of trends by status.

        Useful for monitoring and dashboards.

        Returns:
            Dict with counts by status
        """
        async with self.pool.acquire() as conn:
            rows = await conn.fetch(
                """
                SELECT status, COUNT(*) as count
                FROM trends
                GROUP BY status
                """
            )

            return {row["status"]: row["count"] for row in rows}

    async def get_trends_for_alert(
        self,
        min_velocity: int = 50,
        limit: int = 10
    ) -> List[Trend]:
        """
        Get trends that are candidates for alerting.

        Returns trends with high velocity in emerging or peaking status.

        Args:
            min_velocity: Minimum velocity score (default 50)
            limit: Maximum results

        Returns:
            List of alert-eligible trends
        """
        async with self.pool.acquire() as conn:
            rows = await conn.fetch(
                """
                SELECT * FROM trends
                WHERE velocity_score >= $1
                AND status IN ('emerging', 'peaking')
                ORDER BY velocity_score DESC
                LIMIT $2
                """,
                min_velocity,
                limit
            )

            return [self._row_to_trend(row) for row in rows]

    def _row_to_trend(self, row: asyncpg.Record) -> Trend:
        """
        Convert database row to Trend model.

        Handles type conversions and nullable fields.

        Args:
            row: asyncpg Record from database

        Returns:
            Trend model instance
        """
        return Trend(
            id=row["id"],
            type=TrendType(row["type"]),
            name=row["name"],
            platform_id=row["platform_id"],
            niche_id=row["niche_id"],
            first_detected_at=row["first_detected_at"],
            peak_detected_at=row["peak_detected_at"],
            status=TrendStatus(row["status"]),
            velocity_score=row["velocity_score"],
            saturation_percent=row["saturation_percent"],
            video_count_start=row["video_count_start"],
            video_count_current=row["video_count_current"],
            growth_rate=float(row["growth_rate"]) if row["growth_rate"] else 0.0,
            metadata=row["metadata"] or {},
            created_at=row["created_at"],
            updated_at=row["updated_at"]
        )
