"""Metrics collection service."""

from datetime import UTC, datetime

import structlog
from prometheus_client import Counter, Gauge, Histogram
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

# Prometheus metrics
TRADE_COUNTER = Counter("trading_trades_total", "Total number of trades", ["direction", "strategy"])
SIGNAL_COUNTER = Counter("trading_signals_generated_total", "Total signals generated", ["strategy"])
ORDER_COUNTER = Counter("trading_orders_placed_total", "Total orders placed", ["type", "side"])
PORTFOLIO_VALUE = Gauge("trading_portfolio_total_value", "Current portfolio total value")
OPEN_POSITIONS = Gauge("trading_open_positions_count", "Number of open positions")
CURRENT_DRAWDOWN = Gauge("trading_current_drawdown", "Current drawdown from peak")
TOTAL_PNL_PCT = Gauge("trading_total_pnl_pct", "Total P&L percentage")
TRADES_TODAY = Gauge("trading_trades_today_total", "Number of trades today")
REQUEST_LATENCY = Histogram(
    "http_request_duration_seconds",
    "HTTP request duration",
    ["service", "method", "path"],
    buckets=[0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0],
)


class MetricsCollector:
    """Collects and records performance metrics."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def record(
        self,
        metric_name: str,
        metric_value: float,
        dimensions: dict | None = None,
    ) -> None:
        """Record a metric to the database and update Prometheus gauges."""
        from sqlalchemy import text  # noqa: PLC0415

        now = datetime.now(UTC)
        try:
            await self.session.execute(
                text("""
                    INSERT INTO performance_metrics (id, metric_name, metric_value, dimensions, recorded_at)
                    VALUES (gen_random_uuid(), :name, :value, :dims::jsonb, :now)
                """),
                {
                    "name": metric_name,
                    "value": metric_value,
                    "dims": __import__("json").dumps(dimensions or {}),
                    "now": now,
                },
            )
            await self.session.flush()
        except Exception as e:
            logger.error("Failed to persist metric", metric=metric_name, error=str(e))

        # Update Prometheus gauges
        self._update_prometheus(metric_name, metric_value, dimensions or {})

    def _update_prometheus(self, name: str, value: float, dims: dict) -> None:
        """Update Prometheus metrics based on metric name."""
        if name == "portfolio_value":
            PORTFOLIO_VALUE.set(value)
        elif name == "open_positions":
            OPEN_POSITIONS.set(value)
        elif name == "current_drawdown":
            CURRENT_DRAWDOWN.set(value)
        elif name == "total_pnl_pct":
            TOTAL_PNL_PCT.set(value)
        elif name == "trades_today":
            TRADES_TODAY.set(value)

    async def get_summary(self) -> dict:
        """Get recent metrics summary."""
        from sqlalchemy import text  # noqa: PLC0415

        result = await self.session.execute(
            text("""
                SELECT metric_name, metric_value, recorded_at
                FROM performance_metrics
                WHERE recorded_at > NOW() - INTERVAL '1 hour'
                ORDER BY recorded_at DESC
                LIMIT 50
            """)
        )
        rows = result.fetchall()
        return {
            "metrics": [
                {
                    "name": row[0],
                    "value": float(row[1]),
                    "recorded_at": row[2].isoformat() if row[2] else None,
                }
                for row in rows
            ],
            "count": len(rows),
        }

    def record_trade(self, direction: str, strategy: str) -> None:
        """Increment trade counter."""
        TRADE_COUNTER.labels(direction=direction, strategy=strategy).inc()

    def record_signal(self, strategy: str) -> None:
        """Increment signal counter."""
        SIGNAL_COUNTER.labels(strategy=strategy).inc()

    def record_order(self, order_type: str, side: str) -> None:
        """Increment order counter."""
        ORDER_COUNTER.labels(type=order_type, side=side).inc()
