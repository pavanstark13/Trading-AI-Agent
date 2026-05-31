"""Portfolio and trades endpoints — consolidated into ai-agent service."""

from datetime import datetime, timedelta, timezone

import structlog
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

router = APIRouter()
logger = structlog.get_logger(__name__)


class Position(BaseModel):
    id: str
    ticker: str
    side: str
    quantity: float
    entry_price: float
    current_price: float
    unrealized_pnl: float
    unrealized_pnl_pct: float
    asset_type: str


class Trade(BaseModel):
    id: str
    ticker: str
    side: str
    quantity: float
    price: float
    commission: float
    pnl: float | None
    executed_at: str
    asset_type: str


class AccountSummary(BaseModel):
    equity: float
    cash: float
    buying_power: float
    total_pnl: float
    total_pnl_pct: float
    day_pnl: float


def _get_alpaca_trading_client():
    from services.ai_agent.config import get_settings  # noqa: PLC0415
    s = get_settings()
    if not s.alpaca_api_key:
        return None
    try:
        from alpaca.trading.client import TradingClient  # noqa: PLC0415
        return TradingClient(
            api_key=s.alpaca_api_key,
            secret_key=s.alpaca_secret_key,
            paper=True,
        )
    except Exception as e:
        logger.warning("Alpaca trading client unavailable", error=str(e))
        return None


@router.get("/account", response_model=AccountSummary)
async def get_account() -> AccountSummary:
    """Get account summary from Alpaca paper trading."""
    client = _get_alpaca_trading_client()
    if client:
        try:
            acct = client.get_account()
            equity = float(acct.equity)
            last_equity = float(acct.last_equity)
            return AccountSummary(
                equity=equity,
                cash=float(acct.cash),
                buying_power=float(acct.buying_power),
                total_pnl=equity - 100_000,
                total_pnl_pct=(equity - 100_000) / 100_000 * 100,
                day_pnl=equity - last_equity,
            )
        except Exception as e:
            logger.warning("Failed to get Alpaca account", error=str(e))

    return AccountSummary(
        equity=100_000.0, cash=100_000.0, buying_power=200_000.0,
        total_pnl=0.0, total_pnl_pct=0.0, day_pnl=0.0,
    )


@router.get("/positions", response_model=list[Position])
async def get_positions() -> list[Position]:
    """Get open positions from Alpaca paper trading."""
    client = _get_alpaca_trading_client()
    if client:
        try:
            positions = client.get_all_positions()
            return [
                Position(
                    id=str(p.asset_id),
                    ticker=p.symbol,
                    side=p.side.value,
                    quantity=float(p.qty),
                    entry_price=float(p.avg_entry_price),
                    current_price=float(p.current_price or p.avg_entry_price),
                    unrealized_pnl=float(p.unrealized_pl or 0),
                    unrealized_pnl_pct=float(p.unrealized_plpc or 0) * 100,
                    asset_type="stock",
                )
                for p in positions
            ]
        except Exception as e:
            logger.warning("Failed to get positions", error=str(e))

    return []


@router.get("/trades", response_model=list[Trade])
async def get_trades(limit: int = Query(default=50, le=500)) -> list[Trade]:
    """Get recent trade history from Alpaca paper trading."""
    client = _get_alpaca_trading_client()
    if client:
        try:
            from alpaca.trading.requests import GetOrdersRequest  # noqa: PLC0415
            from alpaca.trading.enums import QueryOrderStatus  # noqa: PLC0415
            req = GetOrdersRequest(status=QueryOrderStatus.CLOSED, limit=limit)
            orders = client.get_orders(filter=req)
            trades = []
            for o in orders:
                if o.filled_at and o.filled_avg_price:
                    trades.append(Trade(
                        id=str(o.id),
                        ticker=o.symbol,
                        side=o.side.value,
                        quantity=float(o.filled_qty or 0),
                        price=float(o.filled_avg_price),
                        commission=0.0,
                        pnl=None,
                        executed_at=o.filled_at.isoformat(),
                        asset_type="stock",
                    ))
            return trades
        except Exception as e:
            logger.warning("Failed to get trades", error=str(e))

    return []


@router.post("/orders")
async def place_order(
    ticker: str,
    side: str,
    qty: float,
    order_type: str = "market",
) -> dict:
    """Place a paper trade order."""
    client = _get_alpaca_trading_client()
    if not client:
        raise HTTPException(status_code=503, detail="Trading client not configured")
    try:
        from alpaca.trading.requests import MarketOrderRequest  # noqa: PLC0415
        from alpaca.trading.enums import OrderSide, TimeInForce  # noqa: PLC0415
        order_side = OrderSide.BUY if side.lower() == "buy" else OrderSide.SELL
        req = MarketOrderRequest(
            symbol=ticker.upper(),
            qty=qty,
            side=order_side,
            time_in_force=TimeInForce.DAY,
        )
        order = client.submit_order(req)
        return {"id": str(order.id), "status": order.status.value, "ticker": ticker, "side": side, "qty": qty}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
