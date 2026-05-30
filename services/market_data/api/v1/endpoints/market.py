"""Market data API endpoints."""

from datetime import datetime, timezone

import structlog
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from services.market_data.domain.repositories import SymbolRepository
from services.market_data.domain.schemas import (
    HistoricalDataRequest,
    MarketQuote,
    OHLCVResponse,
    SymbolCreate,
    SymbolResponse,
    Timeframe,
)
from services.market_data.services.data_fetcher import get_data_fetcher
from services.market_data.services.historical import HistoricalDataService
from shared.database import get_db
from shared.exceptions import RecordNotFoundError, SymbolNotFoundError
from shared.schemas.base import PaginatedResponse, SuccessResponse

router = APIRouter()
logger = structlog.get_logger(__name__)


@router.get("/symbols", response_model=list[SymbolResponse])
async def list_symbols(
    active_only: bool = Query(default=True),
    db: AsyncSession = Depends(get_db),
) -> list[SymbolResponse]:
    """List all tracked symbols."""
    repo = SymbolRepository(db)
    symbols = await repo.list_active() if active_only else await repo.list_active()
    return [SymbolResponse.model_validate(s) for s in symbols]


@router.post("/symbols", response_model=SymbolResponse, status_code=201)
async def create_symbol(
    payload: SymbolCreate,
    db: AsyncSession = Depends(get_db),
) -> SymbolResponse:
    """Add a new symbol to track."""
    repo = SymbolRepository(db)
    try:
        symbol = await repo.create(
            ticker=payload.ticker,
            name=payload.name,
            exchange=payload.exchange,
            asset_type=payload.asset_type.value,
        )
        return SymbolResponse.model_validate(symbol)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/symbols/{ticker}", response_model=SymbolResponse)
async def get_symbol(ticker: str, db: AsyncSession = Depends(get_db)) -> SymbolResponse:
    """Get symbol details by ticker."""
    repo = SymbolRepository(db)
    try:
        symbol = await repo.get_by_ticker(ticker.upper())
        return SymbolResponse.model_validate(symbol)
    except RecordNotFoundError:
        raise HTTPException(status_code=404, detail=f"Symbol '{ticker}' not found")


@router.get("/quotes/{ticker}", response_model=MarketQuote)
async def get_quote(ticker: str) -> MarketQuote:
    """Get real-time quote for a symbol."""
    fetcher = get_data_fetcher()
    try:
        return await fetcher.get_quote(ticker.upper())
    except Exception as e:
        logger.error("Failed to get quote", ticker=ticker, error=str(e))
        raise HTTPException(status_code=503, detail=f"Failed to fetch quote: {e}")


@router.get("/quotes", response_model=list[MarketQuote])
async def get_quotes(
    tickers: str = Query(..., description="Comma-separated list of tickers"),
) -> list[MarketQuote]:
    """Get real-time quotes for multiple symbols."""
    ticker_list = [t.strip().upper() for t in tickers.split(",")]
    fetcher = get_data_fetcher()
    try:
        return await fetcher.get_quotes(ticker_list)
    except Exception as e:
        raise HTTPException(status_code=503, detail=str(e))


@router.get("/historical/{ticker}", response_model=list[OHLCVResponse])
async def get_historical(
    ticker: str,
    timeframe: Timeframe = Query(default=Timeframe.H1),
    start: datetime = Query(default=None),
    end: datetime | None = Query(default=None),
    limit: int = Query(default=500, le=5000),
    refresh: bool = Query(default=False),
    db: AsyncSession = Depends(get_db),
) -> list[OHLCVResponse]:
    """Get historical OHLCV bars for a symbol."""
    if start is None:
        from datetime import timedelta  # noqa: PLC0415
        start = datetime.now(timezone.utc) - timedelta(days=30)

    service = HistoricalDataService(db)
    try:
        return await service.get_bars(
            ticker=ticker.upper(),
            timeframe=timeframe,
            start=start,
            end=end,
            limit=limit,
            refresh=refresh,
        )
    except SymbolNotFoundError:
        raise HTTPException(status_code=404, detail=f"Symbol '{ticker}' not found")
    except Exception as e:
        logger.error("Failed to get historical data", ticker=ticker, error=str(e))
        raise HTTPException(status_code=503, detail=str(e))
