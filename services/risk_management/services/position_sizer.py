"""Position sizing calculations using various methods."""

import math

import structlog

from services.risk_management.domain.schemas import (
    PositionSizeMethod,
    PositionSizeRequest,
    PositionSizeResponse,
)
from shared.exceptions import ValidationError

logger = structlog.get_logger(__name__)


class PositionSizer:
    """
    Calculates position sizes using multiple methods:
    - Fixed Fractional (risk a fixed % of equity per trade)
    - Kelly Criterion (optimal position size based on edge)
    - Fixed Units
    - Percent Equity
    """

    def calculate(self, request: PositionSizeRequest) -> PositionSizeResponse:
        """Calculate position size based on the requested method."""
        if request.entry_price <= 0:
            raise ValidationError("Entry price must be positive")
        if request.stop_loss <= 0:
            raise ValidationError("Stop loss must be positive")
        if request.account_equity <= 0:
            raise ValidationError("Account equity must be positive")

        risk_per_unit = abs(request.entry_price - request.stop_loss)
        if risk_per_unit == 0:
            raise ValidationError("Entry price and stop loss cannot be equal")

        method = request.method
        quantity = 0.0

        if method == PositionSizeMethod.FIXED_FRACTIONAL:
            quantity = self._fixed_fractional(request, risk_per_unit)

        elif method == PositionSizeMethod.KELLY:
            quantity = self._kelly_criterion(request, risk_per_unit)

        elif method == PositionSizeMethod.FIXED_UNITS:
            quantity = 1.0  # Default, override via parameters

        elif method == PositionSizeMethod.PERCENT_EQUITY:
            max_position_value = request.account_equity * request.risk_per_trade_pct * 10
            quantity = max_position_value / request.entry_price

        # Ensure we don't size larger than max_position_pct of equity
        max_position_value = request.account_equity * 0.20  # Hard limit: 20% of equity
        max_qty_by_position = max_position_value / request.entry_price
        quantity = min(quantity, max_qty_by_position)
        quantity = max(0.0, quantity)

        risk_amount = quantity * risk_per_unit
        risk_pct = risk_amount / request.account_equity
        position_value = quantity * request.entry_price
        position_pct = position_value / request.account_equity

        logger.info(
            "Position size calculated",
            ticker=request.ticker,
            method=method.value,
            quantity=round(quantity, 4),
            risk_pct=round(risk_pct * 100, 2),
        )

        return PositionSizeResponse(
            ticker=request.ticker,
            method=method.value,
            entry_price=request.entry_price,
            stop_loss=request.stop_loss,
            quantity=round(quantity, 4),
            risk_amount=round(risk_amount, 2),
            risk_pct=round(risk_pct, 6),
            position_value=round(position_value, 2),
            position_pct=round(position_pct, 6),
        )

    def _fixed_fractional(self, request: PositionSizeRequest, risk_per_unit: float) -> float:
        """
        Fixed Fractional position sizing.
        Risks a fixed percentage of account equity per trade.

        quantity = (equity * risk_pct) / risk_per_unit
        """
        risk_amount = request.account_equity * request.risk_per_trade_pct
        return risk_amount / risk_per_unit

    def _kelly_criterion(self, request: PositionSizeRequest, risk_per_unit: float) -> float:
        """
        Kelly Criterion position sizing.

        Full Kelly: f = (W * R - (1-W)) / R
        where W = win rate, R = avg win/loss ratio
        Fractional Kelly: f_fractional = f_full * kelly_fraction

        Conservative: use quarter-Kelly (0.25) to reduce variance.
        """
        win_rate = request.win_rate
        avg_win_loss_ratio = request.avg_win_loss_ratio

        if win_rate is None or avg_win_loss_ratio is None:
            logger.warning("Kelly requires win_rate and avg_win_loss_ratio, falling back to fixed_fractional")
            return self._fixed_fractional(request, risk_per_unit)

        # Full Kelly formula
        r = avg_win_loss_ratio
        w = win_rate
        full_kelly_fraction = (w * r - (1 - w)) / r if r > 0 else 0.0
        full_kelly_fraction = max(0.0, full_kelly_fraction)

        # Apply fractional Kelly to reduce risk
        adjusted_fraction = full_kelly_fraction * request.kelly_fraction
        adjusted_fraction = min(adjusted_fraction, request.risk_per_trade_pct * 3)  # Cap at 3x base risk

        risk_amount = request.account_equity * adjusted_fraction
        quantity = risk_amount / risk_per_unit

        logger.debug(
            "Kelly criterion calculated",
            win_rate=win_rate,
            rr_ratio=avg_win_loss_ratio,
            full_kelly=round(full_kelly_fraction, 4),
            adjusted_kelly=round(adjusted_fraction, 4),
        )
        return quantity
