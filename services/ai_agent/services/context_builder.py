"""Context builder - assembles market and portfolio context for AI agents."""

from datetime import UTC, datetime
from typing import Any

import httpx
import structlog

from services.ai_agent.config import get_settings

logger = structlog.get_logger(__name__)
settings = get_settings()


class ContextBuilder:
    """
    Builds structured context for AI agents by fetching data
    from internal microservices.
    """

    def __init__(self) -> None:
        self._http = httpx.AsyncClient(timeout=30.0)

    async def build_market_context(self, tickers: list[str]) -> dict[str, Any]:
        """Fetch market data context for given tickers."""
        context: dict[str, Any] = {
            "tickers": tickers,
            "timestamp": datetime.now(UTC).isoformat(),
            "quotes": {},
            "historical_summary": {},
        }

        for ticker in tickers:
            try:
                resp = await self._http.get(
                    f"{settings.market_data_service_url}/api/v1/market/quotes/{ticker}"
                )
                if resp.status_code == 200:
                    context["quotes"][ticker] = resp.json()
            except Exception as e:
                logger.warning("Failed to fetch quote", ticker=ticker, error=str(e))
                context["quotes"][ticker] = {"error": str(e)}

        return context

    async def build_portfolio_context(self) -> dict[str, Any]:
        """Fetch current portfolio state."""
        try:
            resp = await self._http.get(f"{settings.execution_engine_url}/api/v1/orders/positions")
            positions = resp.json() if resp.status_code == 200 else []
        except Exception as e:
            logger.warning("Failed to fetch positions", error=str(e))
            positions = []

        return {
            "positions": positions,
            "open_positions_count": len(positions),
            "timestamp": datetime.now(UTC).isoformat(),
        }

    async def build_risk_context(self, account_equity: float) -> dict[str, Any]:
        """Fetch risk metrics."""
        try:
            resp = await self._http.get(
                f"{settings.risk_management_url}/api/v1/risk/drawdown/{account_equity}"
            )
            drawdown = resp.json() if resp.status_code == 200 else {}
        except Exception as e:
            logger.warning("Failed to fetch drawdown status", error=str(e))
            drawdown = {}

        try:
            cb_resp = await self._http.get(
                f"{settings.risk_management_url}/api/v1/risk/circuit-breaker/status"
            )
            circuit_breaker = cb_resp.json() if cb_resp.status_code == 200 else {}
        except Exception:
            circuit_breaker = {"is_active": False}

        return {
            "account_equity": account_equity,
            "drawdown_status": drawdown,
            "circuit_breaker": circuit_breaker,
            "timestamp": datetime.now(UTC).isoformat(),
        }

    async def build_signals_context(self, tickers: list[str]) -> dict[str, Any]:
        """Fetch latest signals from strategy engine."""
        signals = {}
        for ticker in tickers:
            try:
                resp = await self._http.post(
                    f"{settings.strategy_engine_url}/api/v1/strategy/signals/generate",
                    json={"ticker": ticker, "timeframe": "1h"},
                )
                if resp.status_code == 200:
                    signals[ticker] = resp.json()
            except Exception as e:
                logger.warning("Failed to fetch signals", ticker=ticker, error=str(e))
                signals[ticker] = []

        return {
            "signals": signals,
            "timestamp": datetime.now(UTC).isoformat(),
        }

    async def build_full_context(
        self,
        tickers: list[str],
        account_equity: float = 100_000.0,
    ) -> dict[str, Any]:
        """Build comprehensive context for the orchestrator agent."""
        market = await self.build_market_context(tickers)
        portfolio = await self.build_portfolio_context()
        risk = await self.build_risk_context(account_equity)
        signals = await self.build_signals_context(tickers)

        return {
            "market": market,
            "portfolio": portfolio,
            "risk": risk,
            "signals": signals,
            "built_at": datetime.now(UTC).isoformat(),
        }

    async def close(self) -> None:
        await self._http.aclose()
