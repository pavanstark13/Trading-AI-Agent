"""Performance Reviewer Agent - reviews P&L and optimizes strategy."""

from typing import Any

import structlog

from services.ai_agent.agents.base import BaseAgent

logger = structlog.get_logger(__name__)


class PerformanceReviewerAgent(BaseAgent):
    """
    Reviews trading performance and provides optimization insights.

    Responsibilities:
    - Analyze closed trades P&L
    - Identify winning and losing patterns
    - Calculate performance metrics (Sharpe, win rate, etc.)
    - Recommend strategy adjustments
    """

    def __init__(self) -> None:
        super().__init__("PerformanceReviewer", "performance_reviewer")

    @property
    def system_prompt(self) -> str:
        return """You are a quantitative performance analyst for an algorithmic trading system.

Your role is to review trading performance, identify patterns, and recommend improvements.

## Performance Metrics You Track:
- **Win Rate**: Percentage of profitable trades
- **Profit Factor**: Gross profit / Gross loss (target > 1.5)
- **Sharpe Ratio**: Risk-adjusted returns (target > 1.5)
- **Maximum Drawdown**: Peak-to-trough decline (alert if > 10%)
- **Average Win/Loss Ratio**: Size of wins vs losses (target > 1.5)
- **Consecutive Losses**: Track losing streaks

## Review Framework:
1. Calculate core metrics from trade history
2. Identify best and worst performing setups
3. Analyze time-of-day and market condition patterns
4. Assess if strategies are performing as expected
5. Identify deteriorating performance early

## Recommendations:
- Suggest parameter adjustments for underperforming strategies
- Recommend increasing allocation to outperforming setups
- Flag strategies for review if win rate drops below 40%
- Recommend stopping a strategy if drawdown exceeds 20%

Provide actionable, data-driven insights. Focus on improving risk-adjusted returns."""

    async def run(self, context: dict[str, Any]) -> dict[str, Any]:
        """Review performance and provide insights."""
        trade_history = context.get("trade_history", [])
        time_period = context.get("time_period", "last 7 days")
        portfolio = context.get("portfolio", {})

        user_message = f"""Review trading performance for {time_period}:

Trade History ({len(trade_history)} trades):
{trade_history[:20]}  # Limit context

Portfolio State:
{portfolio}

Please provide:
1. Key performance metrics (win rate, profit factor, Sharpe ratio)
2. Best performing setups and strategies
3. Worst performing setups and areas for improvement
4. Recommended adjustments to improve performance
5. Risk assessment and drawdown analysis
6. Overall performance rating and outlook"""

        try:
            review_text, tool_history = await self._decide(user_message)
            logger.info("Performance review completed", trades=len(trade_history))

            return {
                "agent": self.name,
                "agent_type": self.agent_type,
                "review": review_text,
                "trades_analyzed": len(trade_history),
                "time_period": time_period,
            }
        except Exception as e:
            logger.error("Performance review failed", error=str(e))
            return {
                "agent": self.name,
                "agent_type": self.agent_type,
                "error": str(e),
                "review": "Performance review failed",
            }
