"""Historical data service - fetches, stores and retrieves OHLCV data."""

import uuid
from datetime import UTC, datetime

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

from services.market_data.domain.repositories import OHLCVRepository, SymbolRepository
from services.market_data.domain.schemas import OHLCVResponse, Timeframe
from services.market_data.services.data_fetcher import get_data_fetcher
from shared.exceptions import SymbolNotFoundError

logger = structlog.get_logger(__name__)


class HistoricalDataService:
    """Manages historical OHLCV data fetching and persistence."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.symbol_repo = SymbolRepository(session)
        self.ohlcv_repo = OHLCVRepository(session)
        self.fetcher = get_data_fetcher()

    async def get_bars(
        self,
        ticker: str,
        timeframe: Timeframe,
        start: datetime,
        end: datetime | None = None,
        limit: int = 500,
        refresh: bool = False,
    ) -> list[OHLCVResponse]:
        """Get historical bars, fetching from broker if needed."""
        try:
            symbol = await self.symbol_repo.get_by_ticker(ticker)
        except Exception:
            raise SymbolNotFoundError(ticker)

        # Check if we have recent data in DB
        if not refresh:
            stored = await self.ohlcv_repo.get_bars(symbol.id, timeframe.value, start, end, limit)
            if stored:
                logger.debug("Returning cached OHLCV data", ticker=ticker, count=len(stored))
                return [
                    OHLCVResponse(
                        id=b.id,
                        symbol_id=b.symbol_id,
                        timeframe=timeframe,
                        open=float(b.open),
                        high=float(b.high),
                        low=float(b.low),
                        close=float(b.close),
                        volume=float(b.volume),
                        timestamp=b.timestamp,
                        created_at=b.created_at,
                    )
                    for b in stored
                ]

        # Fetch from broker
        raw_bars = await self.fetcher.get_historical_bars(ticker, timeframe, start, end, limit)

        if raw_bars:
            # Persist to DB
            bar_dicts = [
                {
                    "symbol_id": symbol.id,
                    "timeframe": timeframe.value,
                    "open": b.open,
                    "high": b.high,
                    "low": b.low,
                    "close": b.close,
                    "volume": b.volume,
                    "timestamp": b.timestamp,
                    "created_at": datetime.now(UTC),
                }
                for b in raw_bars
            ]
            inserted = await self.ohlcv_repo.bulk_insert(bar_dicts)
            logger.info("Persisted OHLCV bars", ticker=ticker, inserted=inserted)

        return [
            OHLCVResponse(
                id=uuid.uuid4(),
                symbol_id=symbol.id,
                timeframe=timeframe,
                open=b.open,
                high=b.high,
                low=b.low,
                close=b.close,
                volume=b.volume,
                timestamp=b.timestamp,
                created_at=datetime.now(UTC),
            )
            for b in raw_bars
        ]
