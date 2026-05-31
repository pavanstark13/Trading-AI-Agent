"""Market Analyst Agent - analyzes market conditions and trends."""

from typing import Any

import structlog

from services.ai_agent.agents.base import BaseAgent
from services.ai_agent.tools.market_tools import MARKET_TOOLS

logger = structlog.get_logger(__name__)


class MarketAnalystAgent(BaseAgent):
    """
    Analyzes market conditions, trends, and opportunities.

    Responsibilities:
    - Interpret market data and signals from strategy engine
    - Identify high-probability setups
    - Assess market regime (trending, ranging, volatile)
    - Provide market outlook for trading decisions
    """

    def __init__(self) -> None:
        super().__init__("MarketAnalyst", "market_analyst")

    @property
    def system_prompt(self) -> str:
        return """You are an expert market analyst specializing in technical analysis and Smart Money Concepts (SMC).

Your role is to analyze market conditions and identify high-probability trading opportunities.

## Your Expertise:
- Smart Money Concepts (order blocks, fair value gaps, market structure)
- Technical analysis (moving averages, RSI, volume analysis)
- Market regime identification (trending, ranging, volatile)
- Multi-timeframe analysis
- Risk/reward assessment

## Analysis Framework:
1. **Market Structure**: Identify current trend (uptrend/downtrend/ranging) using higher highs/lows
2. **Key Levels**: Identify significant support/resistance (order blocks, FVGs, swing points)
3. **Momentum**: Assess RSI, volume, and price action momentum
4. **Setup Quality**: Rate each opportunity (1-10) based on confluence of signals
5. **Risk/Reward**: Only recommend setups with minimum 1:2 risk/reward ratio

## Output Format:
Provide structured analysis with:
- Market regime assessment
- Key price levels to watch
- Top trading opportunities (if any)
- Risk factors to consider
- Confidence score (0-1)

Be concise, data-driven, and focused on actionable insights.
Always prioritize capital preservation over aggressive trading."""

    @property
    def tools(self) -> list[dict[str, Any]]:
        return MARKET_TOOLS

    async def execute_tool(self, tool_name: str, tool_input: dict[str, Any]) -> Any:
        """Execute market analysis tools."""
        from services.ai_agent.services.context_builder import ContextBuilder  # noqa: PLC0415

        ctx = ContextBuilder()
        try:
            if tool_name == "get_market_quote":
                result = await ctx.build_market_context([tool_input["ticker"]])
                return result["quotes"].get(tool_input["ticker"], {})

            elif tool_name == "get_trading_signals":
                result = await ctx.build_signals_context([tool_input["ticker"]])
                return result["signals"].get(tool_input["ticker"], [])

            elif tool_name == "get_market_overview":
                tickers = tool_input.get("tickers", ["AAPL", "SPY", "QQQ"])
                return await ctx.build_market_context(tickers)

            else:
                return {"error": f"Unknown tool: {tool_name}"}
        finally:
            await ctx.close()

    async def run(self, context: dict[str, Any]) -> dict[str, Any]:
        """Analyze market and return structured assessment."""
        tickers = context.get("tickers", ["SPY", "QQQ"])
        user_message = f"""Please analyze the current market conditions for the following tickers: {", ".join(tickers)}

Market data and signals are available via the tools provided.

Provide:
1. Market regime for each ticker
2. Key levels (support/resistance)
3. Top 2-3 trading opportunities with entry, stop, target
4. Overall market sentiment and risk assessment
5. Confidence score for each recommendation"""

        try:
            analysis_text, tool_history = await self._decide(user_message)
            logger.info("Market analysis completed", tickers=tickers, tool_calls=len(tool_history))

            return {
                "agent": self.name,
                "agent_type": self.agent_type,
                "analysis": analysis_text,
                "tool_history": tool_history,
                "tickers_analyzed": tickers,
            }
        except Exception as e:
            logger.error("Market analysis failed", error=str(e))
            return {
                "agent": self.name,
                "agent_type": self.agent_type,
                "error": str(e),
                "analysis": "Analysis failed",
            }
