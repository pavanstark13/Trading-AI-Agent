"""Strategy Engine API endpoints."""

from datetime import UTC, datetime

import structlog
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from services.strategy_engine.domain.schemas import (
    BacktestRequest,
    BacktestResult,
    GenerateSignalRequest,
)
from services.strategy_engine.services.backtest import BacktestEngine
from services.strategy_engine.services.signal_generator import (
    STRATEGY_REGISTRY,
    SignalGeneratorService,
)
from shared.database import get_db

router = APIRouter()
logger = structlog.get_logger(__name__)


@router.get("/available", response_model=list[str])
async def list_available_strategies() -> list[str]:
    """List all available strategy names."""
    return list(STRATEGY_REGISTRY.keys())


@router.post("/signals/generate", response_model=list[dict])
async def generate_signals(
    request: GenerateSignalRequest,
    db: AsyncSession = Depends(get_db),
) -> list[dict]:
    """Generate trading signals for a ticker using configured strategies."""
    # In production, this would fetch candles from market-data service
    # For now we return a demonstration with mock data
    import random  # noqa: PLC0415
    from datetime import timedelta  # noqa: PLC0415

    mock_candles = []
    price = 100.0
    now = datetime.now(UTC)
    for i in range(100):
        change = random.uniform(-0.02, 0.02)
        close = price * (1 + change)
        high = max(price, close) * random.uniform(1.001, 1.005)
        low = min(price, close) * random.uniform(0.995, 0.999)
        mock_candles.append(
            {
                "timestamp": now - timedelta(hours=100 - i),
                "open": round(price, 4),
                "high": round(high, 4),
                "low": round(low, 4),
                "close": round(close, 4),
                "volume": round(random.uniform(10000, 500000), 0),
            }
        )
        price = close

    service = SignalGeneratorService(db)
    signals = service.generate_signals(mock_candles)
    aggregated = service.aggregate_signals(signals)

    return [
        {
            "signal_type": s.signal_type,
            "direction": s.direction,
            "strength": s.strength,
            "price": s.price,
            "stop_loss": s.stop_loss,
            "take_profit": s.take_profit,
            "metadata": s.metadata,
        }
        for s in aggregated
    ]


@router.post("/backtest", response_model=BacktestResult)
async def run_backtest(
    request: BacktestRequest,
    db: AsyncSession = Depends(get_db),
) -> BacktestResult:
    """Run a backtest for a strategy on historical data."""
    import random  # noqa: PLC0415
    from datetime import timedelta  # noqa: PLC0415

    # Mock OHLCV data for demonstration
    mock_candles = []
    price = 100.0
    current = request.start
    while current <= request.end and len(mock_candles) < 500:
        change = random.uniform(-0.02, 0.02)
        close = price * (1 + change)
        high = max(price, close) * random.uniform(1.001, 1.005)
        low = min(price, close) * random.uniform(0.995, 0.999)
        mock_candles.append(
            {
                "timestamp": current,
                "open": round(price, 4),
                "high": round(high, 4),
                "low": round(low, 4),
                "close": round(close, 4),
                "volume": round(random.uniform(50000, 2000000), 0),
            }
        )
        price = close
        current += timedelta(hours=1)

    engine = BacktestEngine(initial_capital=request.initial_capital)
    try:
        results = engine.run(mock_candles)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    return BacktestResult(
        strategy_id=request.strategy_id,
        ticker=request.ticker,
        timeframe=request.timeframe,
        start=request.start,
        end=request.end,
        **results,
    )
