"""Risk Manager Agent - makes risk management decisions."""

from typing import Any

import structlog

from services.ai_agent.agents.base import BaseAgent
from services.ai_agent.tools.risk_tools import RISK_TOOLS

logger = structlog.get_logger(__name__)


class RiskManagerAgent(BaseAgent):
    """
    Makes risk management decisions.

    Responsibilities:
    - Evaluate proposed trades against risk limits
    - Calculate appropriate position sizes
    - Monitor portfolio drawdown
    - Recommend circuit breakers when needed
    """

    def __init__(self) -> None:
        super().__init__("RiskManager", "risk_manager")

    @property
    def system_prompt(self) -> str:
        return """You are a strict risk manager for an algorithmic trading firm.

Your primary responsibility is capital preservation. You apply disciplined risk management to every trading decision.

## Risk Management Rules (NON-NEGOTIABLE):
1. Maximum risk per trade: 1% of account equity
2. Maximum daily loss: 3% of account equity
3. Maximum drawdown: 15% - activate circuit breaker if reached
4. Maximum position size: 5% of account equity
5. Maximum open positions: 10
6. Minimum risk/reward: 1:2

## Position Sizing Methods:
- **Fixed Fractional**: Standard method, risk fixed % per trade
- **Kelly Criterion**: Use only with confirmed win rate statistics (apply quarter-Kelly)

## Decision Framework:
1. Check all hard limits first (daily loss, drawdown, position limits)
2. Calculate position size using appropriate method
3. Verify risk/reward meets minimum threshold
4. Assess portfolio correlation risk
5. Provide go/no-go decision with clear reasoning

## Output Format:
Always return:
- approved: true/false
- position_size: calculated units
- risk_amount: dollar risk
- reasons: list of approval/rejection reasons
- warnings: any risk concerns

Your decisions must protect the trading account above all else. When in doubt, reject the trade."""

    @property
    def tools(self) -> list[dict[str, Any]]:
        return RISK_TOOLS

    async def execute_tool(self, tool_name: str, tool_input: dict[str, Any]) -> Any:
        """Execute risk management tools."""
        import httpx  # noqa: PLC0415
        from services.ai_agent.config import get_settings  # noqa: PLC0415

        s = get_settings()
        async with httpx.AsyncClient(timeout=30.0) as client:
            if tool_name == "calculate_position_size":
                resp = await client.post(
                    f"{s.risk_management_url}/api/v1/risk/position-size",
                    json=tool_input,
                )
                return resp.json() if resp.status_code == 200 else {"error": resp.text}

            elif tool_name == "check_risk_limits":
                resp = await client.post(
                    f"{s.risk_management_url}/api/v1/risk/check",
                    json=tool_input,
                )
                return resp.json() if resp.status_code == 200 else {"error": resp.text}

            elif tool_name == "get_drawdown_status":
                equity = tool_input.get("account_equity", 100000)
                resp = await client.get(
                    f"{s.risk_management_url}/api/v1/risk/drawdown/{equity}"
                )
                return resp.json() if resp.status_code == 200 else {"error": resp.text}

            return {"error": f"Unknown tool: {tool_name}"}

    async def run(self, context: dict[str, Any]) -> dict[str, Any]:
        """Evaluate risk for proposed trades."""
        account_equity = context.get("account_equity", 100_000.0)
        proposed_trades = context.get("proposed_trades", [])
        portfolio = context.get("portfolio", {})

        user_message = f"""Evaluate the following trading context for risk management:

Account Equity: ${account_equity:,.2f}
Open Positions: {portfolio.get('open_positions_count', 0)}

Proposed Trades:
{proposed_trades}

Portfolio Status:
{portfolio}

For each proposed trade:
1. Check if it meets all risk criteria
2. Calculate appropriate position size
3. Verify risk/reward ratio
4. Provide go/no-go recommendation

Use the available tools to get current risk metrics."""

        try:
            decision_text, tool_history = await self._decide(user_message)
            logger.info("Risk assessment completed", tool_calls=len(tool_history))

            return {
                "agent": self.name,
                "agent_type": self.agent_type,
                "decision": decision_text,
                "tool_history": tool_history,
                "account_equity": account_equity,
            }
        except Exception as e:
            logger.error("Risk assessment failed", error=str(e))
            return {
                "agent": self.name,
                "agent_type": self.agent_type,
                "error": str(e),
                "decision": "Risk assessment failed - no trades approved",
            }
