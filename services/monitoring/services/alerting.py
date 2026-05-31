"""Alerting service - creates and manages trading alerts."""

import uuid
from datetime import UTC, datetime

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

from shared.redis_client import RedisCache

logger = structlog.get_logger(__name__)


class AlertingService:
    """Manages trading alerts and notifications."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self._cache = RedisCache(prefix="alerts", ttl=3600)

    async def create_alert(
        self,
        alert_type: str,
        severity: str,
        message: str,
        metadata: dict | None = None,
    ) -> dict:
        """Create a new alert and publish to Redis."""
        from sqlalchemy import text  # noqa: PLC0415

        alert_id = uuid.uuid4()
        now = datetime.now(UTC)

        try:
            await self.session.execute(
                text("""
                    INSERT INTO alerts (id, alert_type, severity, message, metadata, acknowledged, created_at)
                    VALUES (:id, :type, :severity, :message, :metadata::jsonb, FALSE, :created_at)
                """),
                {
                    "id": str(alert_id),
                    "type": alert_type,
                    "severity": severity,
                    "message": message,
                    "metadata": __import__("json").dumps(metadata or {}),
                    "created_at": now,
                },
            )
            await self.session.flush()
        except Exception as e:
            logger.error("Failed to persist alert", error=str(e))

        alert = {
            "id": str(alert_id),
            "alert_type": alert_type,
            "severity": severity,
            "message": message,
            "metadata": metadata or {},
            "acknowledged": False,
            "created_at": now.isoformat(),
        }

        # Publish to Redis for real-time consumers
        await self._cache.publish(f"alert:{severity}", alert)

        if severity == "critical":
            logger.critical("CRITICAL ALERT", alert_type=alert_type, message=message)
        elif severity == "warning":
            logger.warning("Alert created", alert_type=alert_type, message=message)

        return alert

    async def acknowledge_alert(self, alert_id: uuid.UUID) -> bool:
        """Acknowledge an alert."""
        from sqlalchemy import text  # noqa: PLC0415

        now = datetime.now(UTC)
        result = await self.session.execute(
            text("UPDATE alerts SET acknowledged = TRUE, ack_at = :now WHERE id = :id"),
            {"id": str(alert_id), "now": now},
        )
        await self.session.flush()
        return result.rowcount > 0

    async def list_alerts(self, unacknowledged_only: bool = True) -> list[dict]:
        """List alerts from the database."""
        from sqlalchemy import text  # noqa: PLC0415

        query = "SELECT id, alert_type, severity, message, metadata, acknowledged, created_at FROM alerts"
        if unacknowledged_only:
            query += " WHERE acknowledged = FALSE"
        query += " ORDER BY created_at DESC LIMIT 100"

        result = await self.session.execute(text(query))
        rows = result.fetchall()

        return [
            {
                "id": str(row[0]),
                "alert_type": row[1],
                "severity": row[2],
                "message": row[3],
                "metadata": row[4],
                "acknowledged": row[5],
                "created_at": row[6].isoformat() if row[6] else None,
            }
            for row in rows
        ]
