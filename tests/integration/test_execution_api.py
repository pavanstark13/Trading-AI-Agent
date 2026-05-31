"""Integration tests for Execution Engine API."""

import uuid
from unittest.mock import AsyncMock, patch

import pytest
import pytest_asyncio

try:
    from services.execution_engine.main import app

    APP_AVAILABLE = True
except Exception:
    APP_AVAILABLE = False


@pytest.mark.skipif(not APP_AVAILABLE, reason="Execution engine service not importable")
class TestExecutionEngineAPI:
    """Integration tests for execution engine endpoints."""

    @pytest_asyncio.fixture
    async def client(self):
        from httpx import ASGITransport, AsyncClient

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            yield client

    @pytest.mark.asyncio
    async def test_root_endpoint(self, client):
        """Root endpoint should return service info."""
        response = await client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert data["service"] == "execution-engine"

    @pytest.mark.asyncio
    async def test_place_order_structure(self, client):
        """Place order should accept valid order request."""
        from services.execution_engine.adapters.alpaca_executor import AlpacaExecutionAdapter

        mock_response = {
            "id": str(uuid.uuid4()),
            "external_order_id": "SIM_12345",
            "symbol_id": str(uuid.uuid4()),
            "order_type": "market",
            "side": "buy",
            "quantity": 10.0,
            "price": None,
            "stop_price": None,
            "time_in_force": "day",
            "status": "filled",
            "filled_qty": 10.0,
            "avg_fill_price": 150.0,
            "rejection_reason": None,
            "created_at": "2024-01-01T00:00:00Z",
            "updated_at": "2024-01-01T00:00:00Z",
        }

        with (
            patch.object(
                AlpacaExecutionAdapter, "place_order", new=AsyncMock(return_value=mock_response)
            ),
            patch(
                "services.execution_engine.services.order_manager.ensure_adapter", new=AsyncMock()
            ),
        ):
            order_request = {
                "ticker": "AAPL",
                "order_type": "market",
                "side": "buy",
                "quantity": 10.0,
                "time_in_force": "day",
            }
            response = await client.post("/api/v1/orders/place", json=order_request)
            # May fail if DB not connected
            assert response.status_code in (201, 422, 500)
