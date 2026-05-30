"""Orchestrator Agent - coordinates the multi-agent trading system."""

from datetime import datetime, timezone
from typing import Any

import structlog

from services.ai_agent.agents.base import BaseAgent
from services.ai_agent.agents.market_analyst import MarketAnalystAgent
from services.ai_agent.agents.performance_reviewer import PerformanceReviewerAgent
from services.ai_agent.agents.risk_manager import RiskManagerAgent
from services.ai_agent.agents.trade_executor import TradeExecutorAgent
from services.ai_agent.services.claude_client import get_claude_client
from services.ai_agent.services.context_builder import ContextBuilder

logger = structlog.get_logger(__name__)


class OrchestratorAgent(BaseAgent):
    """
    Multi-agent orchestrator that coordinates the trading AI system.

    Pipeline:
    1. Market Analyst: Analyzes market conditions and identifies setups
    2. Risk Manager: Evaluates risk and sizes positions
    3. Trade Executor: Places approved orders
    4. Performance Reviewer: Reviews results (triggered periodically)
    """

    def __init__(self) -> None:
        super().__init__("Orchestrator", "orchestrator")
        self._market_analyst = MarketAnalystAgent()
        self._risk_manager = RiskManagerAgent()
        self._trade_executor = TradeExecutorAgent()
        self._performance_reviewer = PerformanceReviewerAgent()
        self._context_builder = ContextBuilder()

    @property
    def system_prompt(self) -> str:
        return """You are the orchestrator of a multi-agent AI trading system.

Your role is to coordinate specialized agents to make intelligent trading decisions.

## Agent Pipeline:
1. **Market Analyst**: Identifies market conditions and trading opportunities
2. **Risk Manager**: Validates setups against risk parameters
3. **Trade Executor**: Places approved orders with optimal timing
4. **Performance Reviewer**: Analyzes results and suggests improvements

## Orchestration Principles:
- Synthesize outputs from all agents into coherent decisions
- Resolve conflicts between agent recommendations
- Ensure all risk checks are passed before execution
- Maintain trading journal for performance review

## Decision Flow:
1. Get market analysis → identify opportunities
2. Pass opportunities to risk manager → get approval/sizing
3. Pass approved trades to executor → execute
4. Log decisions for performance review

Coordinate efficiently and make decisive, well-reasoned trading decisions."""

    async def run_full_cycle(
        self,
        tickers: list[str],
        account_equity: float = 100_000.0,
        execute_trades: bool = False,
    ) -> dict[str, Any]:
        """
        Run a complete trading cycle through all agents.

        Args:
            tickers: List of tickers to analyze
            account_equity: Current account value
            execute_trades: Whether to actually place orders

        Returns:
            Complete cycle results with all agent outputs
        """
        cycle_id = f"cycle_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}"
        logger.info("Starting trading cycle", cycle_id=cycle_id, tickers=tickers)

        results: dict[str, Any] = {
            "cycle_id": cycle_id,
            "started_at": datetime.now(timezone.utc).isoformat(),
            "tickers": tickers,
            "account_equity": account_equity,
        }

        # Step 1: Market Analysis
        logger.info("Step 1: Running market analysis")
        try:
            market_context = await self._context_builder.build_full_context(tickers, account_equity)
            market_result = await self._market_analyst.run({
                "tickers": tickers,
                **market_context,
            })
            results["market_analysis"] = market_result
        except Exception as e:
            logger.error("Market analysis step failed", error=str(e))
            results["market_analysis"] = {"error": str(e)}

        # Step 2: Risk Assessment
        logger.info("Step 2: Running risk assessment")
        try:
            portfolio_context = await self._context_builder.build_portfolio_context()
            risk_result = await self._risk_manager.run({
                "account_equity": account_equity,
                "portfolio": portfolio_context,
                "proposed_trades": results.get("market_analysis", {}).get("analysis", ""),
            })
            results["risk_assessment"] = risk_result
        except Exception as e:
            logger.error("Risk assessment step failed", error=str(e))
            results["risk_assessment"] = {"error": str(e)}

        # Step 3: Trade Execution (only if enabled)
        if execute_trades:
            logger.info("Step 3: Executing trades")
            try:
                execution_result = await self._trade_executor.run({
                    "approved_trades": results.get("risk_assessment", {}).get("decision", ""),
                    "market_analysis": results.get("market_analysis", {}).get("analysis", ""),
                })
                results["execution"] = execution_result
            except Exception as e:
                logger.error("Execution step failed", error=str(e))
                results["execution"] = {"error": str(e)}
        else:
            results["execution"] = {"skipped": True, "reason": "execute_trades=False"}

        results["completed_at"] = datetime.now(timezone.utc).isoformat()
        logger.info("Trading cycle completed", cycle_id=cycle_id)
        return results

    async def run(self, context: dict[str, Any]) -> dict[str, Any]:
        """Run orchestrated cycle from context."""
        tickers = context.get("tickers", ["SPY", "QQQ", "AAPL"])
        account_equity = context.get("account_equity", 100_000.0)
        execute_trades = context.get("execute_trades", False)
        return await self.run_full_cycle(tickers, account_equity, execute_trades)

    async def review_performance(self, trade_history: list[dict], time_period: str = "last 7 days") -> dict[str, Any]:
        """Run performance review cycle."""
        portfolio = await self._context_builder.build_portfolio_context()
        return await self._performance_reviewer.run({
            "trade_history": trade_history,
            "time_period": time_period,
            "portfolio": portfolio,
        })
