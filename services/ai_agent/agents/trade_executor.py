"""Trade Executor Agent - makes final execution decisions."""

from typing import Any

import structlog

from services.ai_agent.agents.base import BaseAgent
from services.ai_agent.tools.execution_tools import EXECUTION_TOOLS

logger = structlog.get_logger(__name__)


class TradeExecutorAgent(BaseAgent):
    """
    Handles final execution decisions.

    Responsibilities:
    - Review market analyst and risk manager outputs
    - Determine optimal entry timing
    - Place orders via execution engine
    - Manage existing positions (scale in/out, move stops)
    """

    def __init__(self) -> None:
        super().__init__("TradeExecutor", "trade_executor")

    @property
    def system_prompt(self) -> str:
        return """You are a professional trade executor for an algorithmic trading system.

Your role is to execute trades efficiently based on approved signals and risk parameters.

## Execution Principles:
1. Only execute trades that have been approved by the Risk Manager
2. Use appropriate order types (market for urgent entries, limit for precise entries)
3. Check for optimal entry timing (avoid executing at extreme prices)
4. Verify execution parameters before placing orders

## Order Types:
- **Market Order**: Immediate execution at best available price (use for clear momentum)
- **Limit Order**: Execute at specific price or better (use for precision entries)
- **Stop Order**: Triggered stop loss execution

## Pre-Execution Checklist:
1. Confirm risk manager approval
2. Verify ticker and direction
3. Check current market price vs target entry
4. Confirm position size and stop loss
5. Verify no duplicate positions exist

## Post-Execution:
- Confirm order placement
- Log trade details
- Monitor for fills

Provide clear execution decisions with order details. When uncertain, request confirmation."""

    @property
    def tools(self) -> list[dict[str, Any]]:
        return EXECUTION_TOOLS

    async def execute_tool(self, tool_name: str, tool_input: dict[str, Any]) -> Any:
        """Execute trading tools."""
        import httpx  # noqa: PLC0415

        from services.ai_agent.config import get_settings  # noqa: PLC0415

        s = get_settings()
        async with httpx.AsyncClient(timeout=30.0) as client:
            if tool_name == "place_order":
                resp = await client.post(
                    f"{s.execution_engine_url}/api/v1/orders/place",
                    json=tool_input,
                )
                return resp.json() if resp.status_code in (200, 201) else {"error": resp.text}

            elif tool_name == "cancel_order":
                order_id = tool_input.get("external_order_id")
                resp = await client.delete(f"{s.execution_engine_url}/api/v1/orders/{order_id}")
                return resp.json() if resp.status_code == 200 else {"error": resp.text}

            elif tool_name == "get_current_price":
                ticker = tool_input.get("ticker")
                resp = await client.get(
                    f"{s.market_data_service_url}/api/v1/market/quotes/{ticker}"
                )
                return resp.json() if resp.status_code == 200 else {"error": resp.text}

            return {"error": f"Unknown tool: {tool_name}"}

    async def run(self, context: dict[str, Any]) -> dict[str, Any]:
        """Execute approved trades."""
        approved_trades = context.get("approved_trades", [])
        market_analysis = context.get("market_analysis", {})

        user_message = f"""Execute the following approved trades:

Approved Trades:
{approved_trades}

Market Analysis:
{market_analysis}

For each trade:
1. Verify current price is near the intended entry
2. Place the appropriate order type
3. Confirm the stop loss and take profit levels
4. Report execution results

Only execute trades that are clearly profitable setups. Do not execute if market conditions have significantly changed."""

        try:
            execution_text, tool_history = await self._decide(user_message)
            executed_orders = [t for t in tool_history if t.get("tool") == "place_order"]
            logger.info("Trade execution completed", orders_placed=len(executed_orders))

            return {
                "agent": self.name,
                "agent_type": self.agent_type,
                "execution_report": execution_text,
                "orders_placed": len(executed_orders),
                "tool_history": tool_history,
            }
        except Exception as e:
            logger.error("Trade execution failed", error=str(e))
            return {
                "agent": self.name,
                "agent_type": self.agent_type,
                "error": str(e),
                "execution_report": "Execution failed",
                "orders_placed": 0,
            }
