"""Alpaca broker adapter for market data."""

from datetime import datetime, timezone

import structlog

from services.market_data.adapters.base import BaseBrokerAdapter
from services.market_data.domain.schemas import MarketQuote, OHLCVBase, Timeframe
from shared.config import get_settings

logger = structlog.get_logger(__name__)

TIMEFRAME_MAP: dict[Timeframe, str] = {
    Timeframe.M1: "1Min",
    Timeframe.M5: "5Min",
    Timeframe.M15: "15Min",
    Timeframe.M30: "30Min",
    Timeframe.H1: "1Hour",
    Timeframe.H4: "4Hour",
    Timeframe.D1: "1Day",
    Timeframe.W1: "1Week",
}


class AlpacaMarketDataAdapter(BaseBrokerAdapter):
    """Market data adapter for Alpaca Markets API."""

    def __init__(self) -> None:
        self._settings = get_settings()
        self._stock_client = None
        self._crypto_client = None

    @property
    def name(self) -> str:
        return "alpaca"

    async def connect(self) -> None:
        try:
            from alpaca.data.historical import CryptoHistoricalDataClient, StockHistoricalDataClient  # noqa: PLC0415

            self._stock_client = StockHistoricalDataClient(
                api_key=self._settings.alpaca_api_key,
                secret_key=self._settings.alpaca_secret_key,
            )
            self._crypto_client = CryptoHistoricalDataClient()
            logger.info("Alpaca adapter connected")
        except ImportError:
            logger.warning("alpaca-py not installed, using mock data")

    async def disconnect(self) -> None:
        self._stock_client = None
        self._crypto_client = None
        logger.info("Alpaca adapter disconnected")

    async def get_quote(self, ticker: str) -> MarketQuote:
        """Get latest quote for a symbol."""
        if self._stock_client is None:
            return self._mock_quote(ticker)
        try:
            from alpaca.data.requests import StockLatestQuoteRequest  # noqa: PLC0415

            req = StockLatestQuoteRequest(symbol_or_symbols=ticker)
            quotes = self._stock_client.get_stock_latest_quote(req)
            q = quotes[ticker]
            return MarketQuote(
                ticker=ticker,
                bid=float(q.bid_price) if q.bid_price else None,
                ask=float(q.ask_price) if q.ask_price else None,
                last=float(q.ask_price or q.bid_price or 0),
                timestamp=q.timestamp or datetime.now(timezone.utc),
            )
        except Exception as e:
            logger.warning("Failed to get quote from Alpaca, using mock", ticker=ticker, error=str(e))
            return self._mock_quote(ticker)

    async def get_quotes(self, tickers: list[str]) -> list[MarketQuote]:
        return [await self.get_quote(ticker) for ticker in tickers]

    async def get_historical_bars(
        self,
        ticker: str,
        timeframe: Timeframe,
        start: datetime,
        end: datetime | None = None,
        limit: int = 500,
    ) -> list[OHLCVBase]:
        """Get historical OHLCV bars from Alpaca."""
        if self._stock_client is None:
            return self._mock_bars(ticker, timeframe, start, end, limit)
        try:
            from alpaca.data.requests import StockBarsRequest  # noqa: PLC0415
            from alpaca.data.timeframe import TimeFrame, TimeFrameUnit  # noqa: PLC0415

            tf_str = TIMEFRAME_MAP.get(timeframe, "1Hour")
            tf_map = {
                "1Min": TimeFrame(1, TimeFrameUnit.Minute),
                "5Min": TimeFrame(5, TimeFrameUnit.Minute),
                "15Min": TimeFrame(15, TimeFrameUnit.Minute),
                "30Min": TimeFrame(30, TimeFrameUnit.Minute),
                "1Hour": TimeFrame(1, TimeFrameUnit.Hour),
                "4Hour": TimeFrame(4, TimeFrameUnit.Hour),
                "1Day": TimeFrame(1, TimeFrameUnit.Day),
                "1Week": TimeFrame(1, TimeFrameUnit.Week),
            }
            alpaca_tf = tf_map.get(tf_str, TimeFrame(1, TimeFrameUnit.Hour))

            req = StockBarsRequest(
                symbol_or_symbols=ticker,
                timeframe=alpaca_tf,
                start=start,
                end=end,
                limit=limit,
            )
            bars_response = self._stock_client.get_stock_bars(req)
            bars = bars_response[ticker]

            return [
                OHLCVBase(
                    timeframe=timeframe,
                    open=float(bar.open),
                    high=float(bar.high),
                    low=float(bar.low),
                    close=float(bar.close),
                    volume=float(bar.volume),
                    timestamp=bar.timestamp,
                )
                for bar in bars
            ]
        except Exception as e:
            logger.warning("Failed to get bars from Alpaca, using mock", ticker=ticker, error=str(e))
            return self._mock_bars(ticker, timeframe, start, end, limit)

    def _mock_quote(self, ticker: str) -> MarketQuote:
        """Return mock quote data for testing."""
        import random  # noqa: PLC0415

        price = random.uniform(100, 500)
        return MarketQuote(
            ticker=ticker,
            bid=round(price - 0.01, 2),
            ask=round(price + 0.01, 2),
            last=round(price, 2),
            change=round(random.uniform(-5, 5), 2),
            change_pct=round(random.uniform(-0.02, 0.02), 4),
            volume=round(random.uniform(100000, 10000000), 0),
            timestamp=datetime.now(timezone.utc),
        )

    def _mock_bars(
        self,
        ticker: str,
        timeframe: Timeframe,
        start: datetime,
        end: datetime | None,
        limit: int,
    ) -> list[OHLCVBase]:
        """Return mock OHLCV bars for testing."""
        import random  # noqa: PLC0415
        from datetime import timedelta  # noqa: PLC0415

        bars = []
        current = start
        price = random.uniform(100, 500)
        tf_minutes = {"1m": 1, "5m": 5, "15m": 15, "30m": 30, "1h": 60, "4h": 240, "1d": 1440, "1w": 10080}
        minutes = tf_minutes.get(timeframe.value, 60)

        for _ in range(min(limit, 100)):
            change = random.uniform(-0.02, 0.02)
            close = price * (1 + change)
            high = max(price, close) * random.uniform(1.0, 1.005)
            low = min(price, close) * random.uniform(0.995, 1.0)

            bars.append(OHLCVBase(
                timeframe=timeframe,
                open=round(price, 4),
                high=round(high, 4),
                low=round(low, 4),
                close=round(close, 4),
                volume=round(random.uniform(10000, 1000000), 0),
                timestamp=current,
            ))
            price = close
            current += timedelta(minutes=minutes)
            if end and current > end:
                break

        return bars
