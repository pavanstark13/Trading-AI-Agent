"""Trade logging service - records executed trades to database."""

from datetime import UTC, datetime

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

from services.execution_engine.domain.models import Trade
from services.execution_engine.domain.schemas import OrderResponse

logger = structlog.get_logger(__name__)


class TradeLogger:
    """Logs executed trades to the database for P&L tracking."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def log_fill(
        self,
        order: OrderResponse,
        fill_price: float,
        fill_qty: float,
        commission: float = 0.0,
        pnl: float | None = None,
    ) -> Trade:
        """Log a trade fill to the database."""
        trade = Trade(
            order_id=order.id,
            symbol_id=order.symbol_id,
            side=order.side,
            quantity=fill_qty,
            price=fill_price,
            commission=commission,
            pnl=pnl,
            pnl_pct=None,
            is_closing=order.side == "sell",
            executed_at=datetime.now(UTC),
            created_at=datetime.now(UTC),
        )
        self.session.add(trade)
        await self.session.flush()

        logger.info(
            "Trade logged",
            trade_id=str(trade.id),
            order_id=str(order.id),
            side=order.side,
            qty=fill_qty,
            price=fill_price,
            pnl=pnl,
        )
        return trade
