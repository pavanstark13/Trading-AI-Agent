"""Execution Engine - Pydantic schemas."""

import uuid
from datetime import datetime
from enum import Enum

from pydantic import Field

from shared.schemas.base import BaseSchema


class OrderType(str, Enum):
    MARKET = "market"
    LIMIT = "limit"
    STOP = "stop"
    STOP_LIMIT = "stop_limit"


class OrderSide(str, Enum):
    BUY = "buy"
    SELL = "sell"


class OrderStatus(str, Enum):
    PENDING = "pending"
    SUBMITTED = "submitted"
    PARTIAL = "partial"
    FILLED = "filled"
    CANCELLED = "cancelled"
    REJECTED = "rejected"


class TimeInForce(str, Enum):
    DAY = "day"
    GTC = "gtc"
    IOC = "ioc"
    FOK = "fok"


class PlaceOrderRequest(BaseSchema):
    ticker: str
    order_type: OrderType
    side: OrderSide
    quantity: float = Field(..., gt=0)
    price: float | None = Field(default=None, gt=0)
    stop_price: float | None = Field(default=None, gt=0)
    time_in_force: TimeInForce = TimeInForce.DAY
    strategy_id: uuid.UUID | None = None
    signal_id: uuid.UUID | None = None


class OrderResponse(BaseSchema):
    id: uuid.UUID
    external_order_id: str | None
    symbol_id: uuid.UUID
    order_type: str
    side: str
    quantity: float
    price: float | None
    stop_price: float | None
    time_in_force: str
    status: str
    filled_qty: float
    avg_fill_price: float | None
    rejection_reason: str | None
    created_at: datetime
    updated_at: datetime


class TradeResponse(BaseSchema):
    id: uuid.UUID
    order_id: uuid.UUID
    symbol_id: uuid.UUID
    side: str
    quantity: float
    price: float
    commission: float
    pnl: float | None
    pnl_pct: float | None
    executed_at: datetime


class PositionResponse(BaseSchema):
    id: uuid.UUID
    symbol_id: uuid.UUID
    side: str
    quantity: float
    avg_entry_price: float
    current_price: float | None
    unrealized_pnl: float | None
    unrealized_pnl_pct: float | None
    realized_pnl: float
    opened_at: datetime
