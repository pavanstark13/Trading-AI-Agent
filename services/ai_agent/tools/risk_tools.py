"""Tool definitions for risk management agents."""

RISK_TOOLS = [
    {
        "name": "calculate_position_size",
        "description": "Calculate the appropriate position size for a trade using fixed fractional or Kelly Criterion method.",
        "input_schema": {
            "type": "object",
            "properties": {
                "ticker": {"type": "string", "description": "The ticker symbol"},
                "entry_price": {"type": "number", "description": "Planned entry price"},
                "stop_loss": {"type": "number", "description": "Stop loss price"},
                "account_equity": {"type": "number", "description": "Current account equity"},
                "risk_per_trade_pct": {
                    "type": "number",
                    "description": "Risk percentage per trade (e.g., 0.01 for 1%)",
                    "default": 0.01,
                },
                "method": {
                    "type": "string",
                    "enum": ["fixed_fractional", "kelly", "percent_equity"],
                    "default": "fixed_fractional",
                },
                "win_rate": {"type": "number", "description": "Historical win rate (required for Kelly)"},
                "avg_win_loss_ratio": {"type": "number", "description": "Average win/loss ratio (required for Kelly)"},
            },
            "required": ["ticker", "entry_price", "stop_loss", "account_equity"],
        },
    },
    {
        "name": "check_risk_limits",
        "description": "Check if a proposed trade meets all risk management criteria (daily loss limit, drawdown, position limits).",
        "input_schema": {
            "type": "object",
            "properties": {
                "account_equity": {"type": "number", "description": "Current account equity"},
                "daily_pnl": {"type": "number", "description": "Today's P&L (negative = loss)"},
                "current_drawdown_pct": {"type": "number", "description": "Current drawdown from peak"},
                "open_positions": {"type": "integer", "description": "Number of open positions"},
                "proposed_position_pct": {"type": "number", "description": "Proposed position size as % of equity"},
            },
            "required": ["account_equity"],
        },
    },
    {
        "name": "get_drawdown_status",
        "description": "Get the current drawdown status including peak equity, current drawdown percentage, and whether circuit breaker is active.",
        "input_schema": {
            "type": "object",
            "properties": {
                "account_equity": {"type": "number", "description": "Current account equity"},
            },
            "required": ["account_equity"],
        },
    },
]
