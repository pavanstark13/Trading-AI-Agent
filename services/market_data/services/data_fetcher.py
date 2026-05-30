"""Market Data fetcher service - broker API abstraction layer."""

from datetime import datetime

import structlog

from services.market_data.adapters.alpaca_adapter import AlpacaMarketDataAdapter
from services.market_data.adapters.base import BaseBrokerAdapter
from services.market_data.domain.schemas import MarketQuote, OHLCVBase, Timeframe

logger = structlog.get_logger(__name__)


class DataFetcherService:
    """Manages broker adapters and fetches market data."""

    def __init__(self) -> None:
        self._adapters: dict[str, BaseBrokerAdapter] = {}
        self._primary_adapter: str = "alpaca"

    def register_adapter(self, adapter: BaseBrokerAdapter) -> None:
        self._adapters[adapter.name] = adapter

    async def startup(self) -> None:
        """Initialize and connect all adapters."""
        alpaca = AlpacaMarketDataAdapter()
        self.register_adapter(alpaca)
        for name, adapter in self._adapters.items():
            try:
                await adapter.connect()
                logger.info("Adapter connected", adapter=name)
            except Exception as e:
                logger.error("Failed to connect adapter", adapter=name, error=str(e))

    async def shutdown(self) -> None:
        """Disconnect all adapters."""
        for name, adapter in self._adapters.items():
            try:
                await adapter.disconnect()
                logger.info("Adapter disconnected", adapter=name)
            except Exception as e:
                logger.error("Failed to disconnect adapter", adapter=name, error=str(e))

    def _get_adapter(self, broker: str | None = None) -> BaseBrokerAdapter:
        name = broker or self._primary_adapter
        adapter = self._adapters.get(name)
        if not adapter:
            raise ValueError(f"Adapter '{name}' not registered")
        return adapter

    async def get_quote(self, ticker: str, broker: str | None = None) -> MarketQuote:
        adapter = self._get_adapter(broker)
        return await adapter.get_quote(ticker)

    async def get_quotes(self, tickers: list[str], broker: str | None = None) -> list[MarketQuote]:
        adapter = self._get_adapter(broker)
        return await adapter.get_quotes(tickers)

    async def get_historical_bars(
        self,
        ticker: str,
        timeframe: Timeframe,
        start: datetime,
        end: datetime | None = None,
        limit: int = 500,
        broker: str | None = None,
    ) -> list[OHLCVBase]:
        adapter = self._get_adapter(broker)
        bars = await adapter.get_historical_bars(ticker, timeframe, start, end, limit)
        logger.info("Fetched historical bars", ticker=ticker, timeframe=timeframe, count=len(bars))
        return bars


# Singleton instance
_fetcher: DataFetcherService | None = None


def get_data_fetcher() -> DataFetcherService:
    global _fetcher  # noqa: PLW0603
    if _fetcher is None:
        _fetcher = DataFetcherService()
    return _fetcher
