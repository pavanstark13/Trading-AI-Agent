"""Loss limiter - circuit breaker for daily and trade loss limits."""

from datetime import datetime, timezone

import structlog

from services.risk_management.domain.schemas import RiskCheckRequest, RiskCheckResponse
from shared.exceptions import DailyLossLimitError, RiskLimitBreachedError
from shared.redis_client import RedisCache

logger = structlog.get_logger(__name__)


class LossLimiter:
    """
    Enforces loss limits and acts as circuit breaker.

    Checks:
    - Daily loss limit (stop trading for the day)
    - Max drawdown limit (halt all trading)
    - Maximum open positions
    - Per-trade risk limits
    """

    def __init__(
        self,
        daily_loss_limit_pct: float = 0.03,
        max_drawdown_pct: float = 0.15,
        max_open_positions: int = 10,
        max_position_size_pct: float = 0.05,
    ) -> None:
        self.daily_loss_limit_pct = daily_loss_limit_pct
        self.max_drawdown_pct = max_drawdown_pct
        self.max_open_positions = max_open_positions
        self.max_position_size_pct = max_position_size_pct
        self._cache = RedisCache(prefix="trading", ttl=86400)

    async def check_trade_allowed(self, request: RiskCheckRequest) -> RiskCheckResponse:
        """
        Comprehensive risk check before allowing a trade.
        Returns approval status with reasons.
        """
        reasons: list[str] = []
        warnings: list[str] = []

        # Check daily loss limit
        if request.account_equity > 0:
            daily_loss_pct = -request.daily_pnl / request.account_equity if request.daily_pnl < 0 else 0.0
            if daily_loss_pct >= self.daily_loss_limit_pct:
                reasons.append(
                    f"Daily loss limit reached: {daily_loss_pct:.1%} >= {self.daily_loss_limit_pct:.1%}"
                )
            elif daily_loss_pct >= self.daily_loss_limit_pct * 0.8:
                warnings.append(
                    f"Daily loss approaching limit: {daily_loss_pct:.1%} / {self.daily_loss_limit_pct:.1%}"
                )

        # Check max drawdown
        if request.current_drawdown_pct >= self.max_drawdown_pct:
            reasons.append(
                f"Max drawdown exceeded: {request.current_drawdown_pct:.1%} >= {self.max_drawdown_pct:.1%}"
            )
        elif request.current_drawdown_pct >= self.max_drawdown_pct * 0.8:
            warnings.append(
                f"Drawdown approaching max: {request.current_drawdown_pct:.1%} / {self.max_drawdown_pct:.1%}"
            )

        # Check open positions
        if request.open_positions >= self.max_open_positions:
            reasons.append(
                f"Max open positions reached: {request.open_positions} >= {self.max_open_positions}"
            )

        # Check position size
        if request.proposed_position_pct > self.max_position_size_pct:
            reasons.append(
                f"Position too large: {request.proposed_position_pct:.1%} > {self.max_position_size_pct:.1%}"
            )

        # Check circuit breaker flag in Redis
        circuit_breaker = await self._cache.get("circuit_breaker_active")
        if circuit_breaker:
            reasons.append("Circuit breaker is active - trading halted")

        approved = len(reasons) == 0
        if not approved:
            logger.warning("Trade rejected by risk check", reasons=reasons)
        elif warnings:
            logger.warning("Trade approved with warnings", warnings=warnings)

        return RiskCheckResponse(approved=approved, reasons=reasons, warnings=warnings)

    async def activate_circuit_breaker(self, reason: str) -> None:
        """Activate the circuit breaker to halt all trading."""
        await self._cache.set("circuit_breaker_active", {
            "activated_at": datetime.now(timezone.utc).isoformat(),
            "reason": reason,
        }, ttl=86400)
        logger.critical("CIRCUIT BREAKER ACTIVATED", reason=reason)

    async def deactivate_circuit_breaker(self) -> None:
        """Deactivate the circuit breaker."""
        await self._cache.delete("circuit_breaker_active")
        logger.info("Circuit breaker deactivated")

    async def is_circuit_breaker_active(self) -> bool:
        """Check if circuit breaker is currently active."""
        return await self._cache.exists("circuit_breaker_active")
