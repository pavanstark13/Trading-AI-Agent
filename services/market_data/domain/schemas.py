"""Market Data Service - Pydantic schemas."""

import uuid
from datetime import datetime
from enum import StrEnum

from pydantic import Field

from shared.schemas.base import BaseSchema


class AssetType(StrEnum):
    STOCK = "stock"
    ETF = "etf"
    CRYPTO = "crypto"
    FOREX = "forex"
    FUTURES = "futures"


class Timeframe(StrEnum):
    M1 = "1m"
    M5 = "5m"
    M15 = "15m"
    M30 = "30m"
    H1 = "1h"
    H4 = "4h"
    D1 = "1d"
    W1 = "1w"


class SymbolBase(BaseSchema):
    ticker: str = Field(..., max_length=20)
    name: str = Field(..., max_length=255)
    exchange: str = Field(..., max_length=50)
    asset_type: AssetType = AssetType.STOCK
    is_active: bool = True


class SymbolCreate(SymbolBase):
    pass


class SymbolResponse(SymbolBase):
    id: uuid.UUID
    created_at: datetime
    updated_at: datetime


class OHLCVBase(BaseSchema):
    timeframe: Timeframe
    open: float = Field(..., gt=0)
    high: float = Field(..., gt=0)
    low: float = Field(..., gt=0)
    close: float = Field(..., gt=0)
    volume: float = Field(..., ge=0)
    timestamp: datetime


class OHLCVCreate(OHLCVBase):
    symbol_id: uuid.UUID


class OHLCVResponse(OHLCVBase):
    id: uuid.UUID
    symbol_id: uuid.UUID
    created_at: datetime


class MarketSnapshotBase(BaseSchema):
    bid: float | None = None
    ask: float | None = None
    last: float
    volume: float | None = None
    bid_size: float | None = None
    ask_size: float | None = None
    snapshot_time: datetime


class MarketSnapshotCreate(MarketSnapshotBase):
    symbol_id: uuid.UUID


class MarketSnapshotResponse(MarketSnapshotBase):
    id: uuid.UUID
    symbol_id: uuid.UUID
    created_at: datetime


class HistoricalDataRequest(BaseSchema):
    ticker: str
    timeframe: Timeframe
    start: datetime
    end: datetime | None = None
    limit: int = Field(default=500, le=5000)


class MarketQuote(BaseSchema):
    ticker: str
    bid: float | None = None
    ask: float | None = None
    last: float
    change: float | None = None
    change_pct: float | None = None
    volume: float | None = None
    timestamp: datetime
