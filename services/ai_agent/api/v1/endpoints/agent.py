"""AI Agent API endpoints."""

from typing import Any

import structlog
from fastapi import APIRouter, HTTPException

from services.ai_agent.agents.orchestrator import OrchestratorAgent
from shared.schemas.base import BaseSchema

router = APIRouter()
logger = structlog.get_logger(__name__)


class RunCycleRequest(BaseSchema):
    tickers: list[str] = ["SPY", "QQQ", "AAPL"]
    account_equity: float = 100_000.0
    execute_trades: bool = False


class AnalyzeRequest(BaseSchema):
    tickers: list[str]
    account_equity: float = 100_000.0


class PerformanceReviewRequest(BaseSchema):
    trade_history: list[dict[str, Any]] = []
    time_period: str = "last 7 days"


@router.post("/cycle/run")
async def run_trading_cycle(request: RunCycleRequest) -> dict:
    """Run a complete multi-agent trading cycle."""
    orchestrator = OrchestratorAgent()
    try:
        result = await orchestrator.run_full_cycle(
            tickers=request.tickers,
            account_equity=request.account_equity,
            execute_trades=request.execute_trades,
        )
        return {"status": "completed", "result": result}
    except Exception as e:
        logger.error("Trading cycle failed", error=str(e))
        raise HTTPException(status_code=500, detail=f"Trading cycle failed: {e}")


@router.post("/analyze")
async def analyze_market(request: AnalyzeRequest) -> dict:
    """Run market analysis only (no execution)."""
    from services.ai_agent.agents.market_analyst import MarketAnalystAgent  # noqa: PLC0415
    from services.ai_agent.services.context_builder import ContextBuilder  # noqa: PLC0415

    analyst = MarketAnalystAgent()
    ctx_builder = ContextBuilder()
    try:
        context = await ctx_builder.build_full_context(request.tickers, request.account_equity)
        result = await analyst.run({"tickers": request.tickers, **context})
        return {"status": "completed", "result": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        await ctx_builder.close()


@router.post("/performance/review")
async def review_performance(request: PerformanceReviewRequest) -> dict:
    """Run performance review."""
    orchestrator = OrchestratorAgent()
    try:
        result = await orchestrator.review_performance(
            trade_history=request.trade_history,
            time_period=request.time_period,
        )
        return {"status": "completed", "result": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
