"""Drawdown monitor - tracks equity curve and drawdown levels."""

from datetime import datetime, timezone

import structlog

from services.risk_management.domain.schemas import DrawdownStatus
from shared.exceptions import MaxDrawdownError
from shared.redis_client import RedisCache

logger = structlog.get_logger(__name__)

CACHE_KEY_PEAK_EQUITY = "risk:peak_equity"
CACHE_KEY_DAILY_START = "risk:daily_start_equity"
CACHE_KEY_EQUITY_HISTORY = "risk:equity_history"


class DrawdownMonitor:
    """
    Monitors equity drawdown in real-time.

    Tracks:
    - Current drawdown from peak equity
    - Daily P&L against daily loss limit
    - Issues alerts when thresholds are breached
    """

    def __init__(
        self,
        max_drawdown_pct: float = 0.15,
        daily_loss_limit_pct: float = 0.05,
    ) -> None:
        self.max_drawdown_pct = max_drawdown_pct
        self.daily_loss_limit_pct = daily_loss_limit_pct
        self._cache = RedisCache(prefix="trading", ttl=86400)
        self._peak_equity: float | None = None
        self._daily_start_equity: float | None = None

    async def update(self, current_equity: float) -> DrawdownStatus:
        """
        Update equity and check drawdown levels.

        Raises MaxDrawdownError if max drawdown is exceeded.
        """
        # Initialize peak on first call
        if self._peak_equity is None:
            cached = await self._cache.get(CACHE_KEY_PEAK_EQUITY)
            self._peak_equity = float(cached) if cached else current_equity

        if self._daily_start_equity is None:
            cached = await self._cache.get(CACHE_KEY_DAILY_START)
            self._daily_start_equity = float(cached) if cached else current_equity

        # Update peak
        if current_equity > self._peak_equity:
            self._peak_equity = current_equity
            await self._cache.set(CACHE_KEY_PEAK_EQUITY, current_equity)

        # Calculate drawdown
        current_drawdown = (self._peak_equity - current_equity) / self._peak_equity
        daily_loss = (self._daily_start_equity - current_equity) / self._daily_start_equity
        daily_loss = max(0.0, daily_loss)

        # Log warning levels
        if current_drawdown >= self.max_drawdown_pct * 0.8:
            logger.warning(
                "Drawdown approaching limit",
                current_drawdown_pct=round(current_drawdown * 100, 2),
                limit_pct=round(self.max_drawdown_pct * 100, 2),
            )

        if daily_loss >= self.daily_loss_limit_pct * 0.8:
            logger.warning(
                "Daily loss approaching limit",
                daily_loss_pct=round(daily_loss * 100, 2),
                limit_pct=round(self.daily_loss_limit_pct * 100, 2),
            )

        # Circuit breakers
        circuit_breaker_active = False
        if current_drawdown >= self.max_drawdown_pct:
            circuit_breaker_active = True
            logger.critical(
                "MAX DRAWDOWN EXCEEDED - CIRCUIT BREAKER ACTIVE",
                drawdown_pct=round(current_drawdown * 100, 2),
            )

        # Store equity history
        await self._cache.lpush(CACHE_KEY_EQUITY_HISTORY, {
            "equity": current_equity,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        })

        return DrawdownStatus(
            current_equity=round(current_equity, 2),
            peak_equity=round(self._peak_equity, 2),
            current_drawdown_pct=round(current_drawdown, 6),
            max_drawdown_pct=self.max_drawdown_pct,
            is_circuit_breaker_active=circuit_breaker_active,
            daily_loss_pct=round(daily_loss, 6),
            daily_loss_limit_pct=self.daily_loss_limit_pct,
        )

    async def reset_daily(self, current_equity: float) -> None:
        """Reset daily equity baseline (call at start of each trading day)."""
        self._daily_start_equity = current_equity
        await self._cache.set(CACHE_KEY_DAILY_START, current_equity, ttl=86400)
        logger.info("Daily equity reset", equity=current_equity)

    async def get_status(self, current_equity: float) -> DrawdownStatus:
        """Get current drawdown status without triggering alerts."""
        return await self.update(current_equity)
