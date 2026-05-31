"""Market data endpoints — consolidated into ai-agent service."""

from datetime import datetime, timedelta, timezone
from enum import Enum

import structlog
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

router = APIRouter()
logger = structlog.get_logger(__name__)

# ---------------------------------------------------------------------------
# Supported assets
# ---------------------------------------------------------------------------
STOCKS = ["AAPL", "MSFT", "GOOGL", "AMZN", "NVDA", "TSLA", "META", "SPY", "QQQ", "AMD"]
CRYPTO = ["BTC/USD", "ETH/USD", "SOL/USD", "BNB/USD", "XRP/USD"]
FOREX  = ["EUR/USD", "GBP/USD", "USD/JPY", "AUD/USD"]

TIMEFRAME_MINUTES = {
    "1m": 1, "5m": 5, "15m": 15, "30m": 30,
    "1h": 60, "4h": 240, "1d": 1440, "1w": 10080,
}


class AssetType(str, Enum):
    stock  = "stock"
    crypto = "crypto"
    forex  = "forex"


class OHLCVBar(BaseModel):
    timestamp: str
    open: float
    high: float
    low: float
    close: float
    volume: float


class Quote(BaseModel):
    ticker: str
    last: float
    bid: float
    ask: float
    change: float
    change_pct: float
    volume: float
    asset_type: str
    timestamp: str


# ---------------------------------------------------------------------------
# Alpaca fetch helpers
# ---------------------------------------------------------------------------

def _get_alpaca_clients():
    from services.ai_agent.config import get_settings  # noqa: PLC0415
    s = get_settings()
    if not s.alpaca_api_key:
        return None, None
    try:
        from alpaca.data.historical import CryptoHistoricalDataClient, StockHistoricalDataClient  # noqa: PLC0415
        stock = StockHistoricalDataClient(api_key=s.alpaca_api_key, secret_key=s.alpaca_secret_key)
        crypto = CryptoHistoricalDataClient()
        return stock, crypto
    except Exception as e:
        logger.warning("Alpaca clients unavailable", error=str(e))
        return None, None


def _is_crypto(ticker: str) -> bool:
    return "/" in ticker and "USD" in ticker and ticker not in FOREX


def _mock_bars(ticker: str, timeframe: str, limit: int) -> list[OHLCVBar]:
    import random
    seed = sum(ord(c) for c in ticker)
    random.seed(seed)
    base = 180.0 if "BTC" not in ticker else 65000.0
    price = base
    bars = []
    minutes = TIMEFRAME_MINUTES.get(timeframe, 60)
    now = datetime.now(timezone.utc)
    for i in range(limit, 0, -1):
        change = (random.random() - 0.48) * base * 0.012
        open_ = price
        price = max(price + change, base * 0.5)
        high = max(open_, price) * (1 + random.random() * 0.003)
        low  = min(open_, price) * (1 - random.random() * 0.003)
        bars.append(OHLCVBar(
            timestamp=( now - timedelta(minutes=minutes * i)).isoformat(),
            open=round(open_, 4),
            high=round(high, 4),
            low=round(low, 4),
            close=round(price, 4),
            volume=round(random.uniform(500_000, 5_000_000), 0),
        ))
    return bars


def _mock_quote(ticker: str) -> Quote:
    import random
    random.seed(sum(ord(c) for c in ticker))
    base = 65000.0 if "BTC" in ticker else (3500.0 if "ETH" in ticker else 180.0)
    price = base * random.uniform(0.95, 1.05)
    change = random.uniform(-5, 5)
    atype = "crypto" if _is_crypto(ticker) else ("forex" if "/" in ticker else "stock")
    return Quote(
        ticker=ticker,
        last=round(price, 2),
        bid=round(price - 0.01, 2),
        ask=round(price + 0.01, 2),
        change=round(change, 2),
        change_pct=round(change / price * 100, 4),
        volume=round(random.uniform(1_000_000, 50_000_000), 0),
        asset_type=atype,
        timestamp=datetime.now(timezone.utc).isoformat(),
    )


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@router.get("/assets")
async def list_assets() -> dict:
    """List all supported assets across all markets."""
    return {
        "stocks": STOCKS,
        "crypto": CRYPTO,
        "forex":  FOREX,
        "total":  len(STOCKS) + len(CRYPTO) + len(FOREX),
    }


@router.get("/quotes/{ticker}", response_model=Quote)
async def get_quote(ticker: str) -> Quote:
    """Get real-time quote for any asset (stock, crypto, forex)."""
    ticker = ticker.upper()
    stock_client, crypto_client = _get_alpaca_clients()

    if stock_client and not _is_crypto(ticker) and "/" not in ticker:
        try:
            from alpaca.data.requests import StockLatestQuoteRequest  # noqa: PLC0415
            req = StockLatestQuoteRequest(symbol_or_symbols=ticker)
            quotes = stock_client.get_stock_latest_quote(req)
            q = quotes[ticker]
            price = float(q.ask_price or q.bid_price or 0)
            return Quote(
                ticker=ticker,
                last=price,
                bid=float(q.bid_price or price),
                ask=float(q.ask_price or price),
                change=0.0,
                change_pct=0.0,
                volume=0.0,
                asset_type="stock",
                timestamp=datetime.now(timezone.utc).isoformat(),
            )
        except Exception as e:
            logger.warning("Alpaca quote failed, using mock", ticker=ticker, error=str(e))

    if crypto_client and _is_crypto(ticker):
        try:
            from alpaca.data.requests import CryptoLatestQuoteRequest  # noqa: PLC0415
            symbol = ticker.replace("/", "")
            req = CryptoLatestQuoteRequest(symbol_or_symbols=symbol)
            quotes = crypto_client.get_crypto_latest_quote(req)
            q = quotes[symbol]
            price = float(q.ask_price or q.bid_price or 0)
            return Quote(
                ticker=ticker,
                last=price,
                bid=float(q.bid_price or price),
                ask=float(q.ask_price or price),
                change=0.0,
                change_pct=0.0,
                volume=0.0,
                asset_type="crypto",
                timestamp=datetime.now(timezone.utc).isoformat(),
            )
        except Exception as e:
            logger.warning("Alpaca crypto quote failed, using mock", ticker=ticker, error=str(e))

    return _mock_quote(ticker)


@router.get("/quotes")
async def get_quotes(
    tickers: str = Query(..., description="Comma-separated tickers e.g. AAPL,BTC/USD,EUR/USD"),
) -> list[Quote]:
    """Get quotes for multiple assets."""
    ticker_list = [t.strip().upper() for t in tickers.split(",")]
    return [await get_quote(t) for t in ticker_list]


@router.get("/historical/{ticker}", response_model=list[OHLCVBar])
async def get_historical(
    ticker: str,
    timeframe: str = Query(default="1h", description="1m,5m,15m,30m,1h,4h,1d,1w"),
    limit: int = Query(default=200, le=1000),
    start: datetime | None = Query(default=None),
    end: datetime | None = Query(default=None),
) -> list[OHLCVBar]:
    """Get historical OHLCV bars for stocks, crypto or forex."""
    ticker = ticker.upper()
    if start is None:
        minutes = TIMEFRAME_MINUTES.get(timeframe, 60)
        start = datetime.now(timezone.utc) - timedelta(minutes=minutes * limit)

    stock_client, crypto_client = _get_alpaca_clients()

    # --- Stocks ---
    if stock_client and not _is_crypto(ticker) and "/" not in ticker:
        try:
            from alpaca.data.requests import StockBarsRequest  # noqa: PLC0415
            from alpaca.data.timeframe import TimeFrame, TimeFrameUnit  # noqa: PLC0415
            tf_map = {
                "1m": TimeFrame(1, TimeFrameUnit.Minute),
                "5m": TimeFrame(5, TimeFrameUnit.Minute),
                "15m": TimeFrame(15, TimeFrameUnit.Minute),
                "30m": TimeFrame(30, TimeFrameUnit.Minute),
                "1h": TimeFrame(1, TimeFrameUnit.Hour),
                "4h": TimeFrame(4, TimeFrameUnit.Hour),
                "1d": TimeFrame(1, TimeFrameUnit.Day),
                "1w": TimeFrame(1, TimeFrameUnit.Week),
            }
            req = StockBarsRequest(
                symbol_or_symbols=ticker,
                timeframe=tf_map.get(timeframe, TimeFrame(1, TimeFrameUnit.Hour)),
                start=start, end=end, limit=limit,
            )
            bars_resp = stock_client.get_stock_bars(req)
            bars = bars_resp[ticker]
            return [
                OHLCVBar(
                    timestamp=bar.timestamp.isoformat(),
                    open=float(bar.open), high=float(bar.high),
                    low=float(bar.low),   close=float(bar.close),
                    volume=float(bar.volume),
                )
                for bar in bars
            ]
        except Exception as e:
            logger.warning("Alpaca bars failed, using mock", ticker=ticker, error=str(e))

    # --- Crypto ---
    if crypto_client and _is_crypto(ticker):
        try:
            from alpaca.data.requests import CryptoBarsRequest  # noqa: PLC0415
            from alpaca.data.timeframe import TimeFrame, TimeFrameUnit  # noqa: PLC0415
            symbol = ticker.replace("/", "")
            tf_map = {
                "1m": TimeFrame(1, TimeFrameUnit.Minute),
                "5m": TimeFrame(5, TimeFrameUnit.Minute),
                "1h": TimeFrame(1, TimeFrameUnit.Hour),
                "4h": TimeFrame(4, TimeFrameUnit.Hour),
                "1d": TimeFrame(1, TimeFrameUnit.Day),
            }
            req = CryptoBarsRequest(
                symbol_or_symbols=symbol,
                timeframe=tf_map.get(timeframe, TimeFrame(1, TimeFrameUnit.Hour)),
                start=start, end=end, limit=limit,
            )
            bars_resp = crypto_client.get_crypto_bars(req)
            bars = bars_resp[symbol]
            return [
                OHLCVBar(
                    timestamp=bar.timestamp.isoformat(),
                    open=float(bar.open), high=float(bar.high),
                    low=float(bar.low),   close=float(bar.close),
                    volume=float(bar.volume),
                )
                for bar in bars
            ]
        except Exception as e:
            logger.warning("Alpaca crypto bars failed, using mock", ticker=ticker, error=str(e))

    return _mock_bars(ticker, timeframe, limit)


@router.get("/market-status")
async def market_status() -> dict:
    """Get current market status for all asset classes."""
    now = datetime.now(timezone.utc)
    weekday = now.weekday()
    hour = now.hour
    stock_open = weekday < 5 and 13 <= hour < 20
    return {
        "stocks":  {"open": stock_open, "hours": "09:30-16:00 ET (Mon-Fri)"},
        "crypto":  {"open": True,        "hours": "24/7"},
        "forex":   {"open": weekday < 5, "hours": "24/5 (Mon-Fri)"},
        "timestamp": now.isoformat(),
    }
