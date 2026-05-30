"""Base broker adapter interface for market data."""

from abc import ABC, abstractmethod
from datetime import datetime

from services.market_data.domain.schemas import MarketQuote, OHLCVBase, Timeframe


class BaseBrokerAdapter(ABC):
    """Abstract base class for broker market data adapters."""

    @abstractmethod
    async def get_quote(self, ticker: str) -> MarketQuote:
        """Get latest quote for a symbol."""
        ...

    @abstractmethod
    async def get_quotes(self, tickers: list[str]) -> list[MarketQuote]:
        """Get latest quotes for multiple symbols."""
        ...

    @abstractmethod
    async def get_historical_bars(
        self,
        ticker: str,
        timeframe: Timeframe,
        start: datetime,
        end: datetime | None = None,
        limit: int = 500,
    ) -> list[OHLCVBase]:
        """Get historical OHLCV bars."""
        ...

    @abstractmethod
    async def connect(self) -> None:
        """Establish connection to broker API."""
        ...

    @abstractmethod
    async def disconnect(self) -> None:
        """Close connection to broker API."""
        ...

    @property
    @abstractmethod
    def name(self) -> str:
        """Adapter name."""
        ...
