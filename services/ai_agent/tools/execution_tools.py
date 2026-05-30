"""Tool definitions for trade execution agents."""

EXECUTION_TOOLS = [
    {
        "name": "place_order",
        "description": "Place a trading order with the execution engine. Returns order confirmation with status.",
        "input_schema": {
            "type": "object",
            "properties": {
                "ticker": {"type": "string", "description": "The ticker symbol"},
                "order_type": {
                    "type": "string",
                    "enum": ["market", "limit", "stop", "stop_limit"],
                    "description": "Type of order",
                },
                "side": {
                    "type": "string",
                    "enum": ["buy", "sell"],
                    "description": "Order direction",
                },
                "quantity": {"type": "number", "description": "Number of units/shares to trade"},
                "price": {"type": "number", "description": "Limit price (required for limit orders)"},
                "stop_price": {"type": "number", "description": "Stop price (for stop orders)"},
                "time_in_force": {
                    "type": "string",
                    "enum": ["day", "gtc", "ioc", "fok"],
                    "default": "day",
                },
            },
            "required": ["ticker", "order_type", "side", "quantity"],
        },
    },
    {
        "name": "cancel_order",
        "description": "Cancel an open order by its external order ID.",
        "input_schema": {
            "type": "object",
            "properties": {
                "external_order_id": {"type": "string", "description": "The broker's order ID to cancel"},
            },
            "required": ["external_order_id"],
        },
    },
    {
        "name": "get_current_price",
        "description": "Get the current market price for a ticker before executing an order.",
        "input_schema": {
            "type": "object",
            "properties": {
                "ticker": {"type": "string", "description": "The ticker symbol"},
            },
            "required": ["ticker"],
        },
    },
]
