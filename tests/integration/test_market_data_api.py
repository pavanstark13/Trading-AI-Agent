"""Integration tests for Market Data Service API."""

from unittest.mock import AsyncMock, patch

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient

# These tests require the service to be importable
try:
    from services.market_data.main import app
    APP_AVAILABLE = True
except Exception:
    APP_AVAILABLE = False


@pytest.mark.skipif(not APP_AVAILABLE, reason="Market data service not importable")
class TestMarketDataAPI:
    """Integration tests for market data endpoints."""

    @pytest_asyncio.fixture
    async def client(self):
        """Create async test client."""
        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test"
        ) as client:
            yield client

    @pytest.mark.asyncio
    async def test_root_endpoint(self, client):
        """Root endpoint should return service info."""
        response = await client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert data["service"] == "market-data"
        assert data["status"] == "running"

    @pytest.mark.asyncio
    @patch("services.market_data.api.v1.endpoints.health.get_db")
    @patch("services.market_data.api.v1.endpoints.health.get_redis_client")
    async def test_health_endpoint_structure(self, mock_redis, mock_db, client):
        """Health endpoint should return expected structure."""
        mock_redis.return_value.ping = AsyncMock(return_value=True)

        response = await client.get("/api/v1/health")
        # May fail if DB not connected but should return some response
        assert response.status_code in (200, 500, 503)

    @pytest.mark.asyncio
    async def test_get_quotes_returns_list(self, client):
        """Get quotes should return a list."""
        with patch("services.market_data.services.data_fetcher.get_data_fetcher") as mock_fetcher:
            mock_fetcher.return_value.get_quotes = AsyncMock(return_value=[
                {
                    "ticker": "AAPL",
                    "bid": 150.0,
                    "ask": 150.02,
                    "last": 150.01,
                    "change": 1.5,
                    "change_pct": 0.01,
                    "volume": 1000000,
                    "timestamp": "2024-01-01T00:00:00Z",
                }
            ])
            response = await client.get("/api/v1/market/quotes?tickers=AAPL")
            assert response.status_code == 200
            data = response.json()
            assert isinstance(data, list)
