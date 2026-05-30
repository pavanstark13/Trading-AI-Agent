"""Strategy Engine - Pydantic schemas."""

import uuid
from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import Field

from shared.schemas.base import BaseSchema


class StrategyType(str, Enum):
    SMC = "smc"
    RULE_BASED = "rule_based"
    ML = "ml"
    HYBRID = "hybrid"


class SignalType(str, Enum):
    ENTRY = "entry"
    EXIT = "exit"
    SCALE_IN = "scale_in"
    SCALE_OUT = "scale_out"


class Direction(str, Enum):
    LONG = "long"
    SHORT = "short"


class StrategyCreate(BaseSchema):
    name: str = Field(..., max_length=100)
    description: str | None = None
    type: StrategyType
    parameters: dict[str, Any] = {}
    is_active: bool = False


class StrategyResponse(BaseSchema):
    id: uuid.UUID
    name: str
    description: str | None
    type: str
    parameters: dict[str, Any]
    is_active: bool
    created_at: datetime
    updated_at: datetime


class SignalCreate(BaseSchema):
    strategy_id: uuid.UUID
    symbol_id: uuid.UUID
    signal_type: SignalType
    direction: Direction
    strength: float = Field(..., ge=0, le=1)
    price: float = Field(..., gt=0)
    stop_loss: float | None = None
    take_profit: float | None = None
    timeframe: str | None = None
    metadata: dict[str, Any] = {}


class SignalResponse(BaseSchema):
    id: uuid.UUID
    strategy_id: uuid.UUID
    symbol_id: uuid.UUID
    signal_type: str
    direction: str
    strength: float
    price: float
    stop_loss: float | None
    take_profit: float | None
    timeframe: str | None
    metadata: dict[str, Any]
    is_executed: bool
    created_at: datetime


class GenerateSignalRequest(BaseSchema):
    ticker: str
    timeframe: str = "1h"
    strategy_id: uuid.UUID | None = None


class BacktestRequest(BaseSchema):
    strategy_id: uuid.UUID
    ticker: str
    timeframe: str = "1h"
    start: datetime
    end: datetime
    initial_capital: float = Field(default=100000.0, gt=0)


class BacktestResult(BaseSchema):
    strategy_id: uuid.UUID
    ticker: str
    timeframe: str
    start: datetime
    end: datetime
    total_trades: int
    winning_trades: int
    losing_trades: int
    win_rate: float
    total_return_pct: float
    max_drawdown_pct: float
    sharpe_ratio: float
    profit_factor: float
    initial_capital: float
    final_capital: float
