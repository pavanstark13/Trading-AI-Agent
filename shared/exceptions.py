"""Custom exception hierarchy for the AI Trading Agent Platform."""

from typing import Any


class TradingBaseException(Exception):
    """Base exception for all trading platform exceptions."""

    def __init__(
        self, message: str, code: str = "TRADING_ERROR", details: dict[str, Any] | None = None
    ) -> None:
        super().__init__(message)
        self.message = message
        self.code = code
        self.details = details or {}


# ── Data Layer Exceptions ────────────────────────────────────────────────────


class DatabaseError(TradingBaseException):
    """Database operation error."""

    def __init__(self, message: str, details: dict[str, Any] | None = None) -> None:
        super().__init__(message, code="DATABASE_ERROR", details=details)


class RecordNotFoundError(DatabaseError):
    """Record not found in database."""

    def __init__(self, entity: str, identifier: Any) -> None:
        super().__init__(
            f"{entity} with id '{identifier}' not found",
            details={"entity": entity, "identifier": str(identifier)},
        )
        self.code = "NOT_FOUND"


class DuplicateRecordError(DatabaseError):
    """Duplicate record error."""

    def __init__(self, entity: str, field: str, value: Any) -> None:
        super().__init__(
            f"{entity} with {field}='{value}' already exists",
            details={"entity": entity, "field": field, "value": str(value)},
        )
        self.code = "DUPLICATE_RECORD"


# ── Market Data Exceptions ───────────────────────────────────────────────────


class MarketDataError(TradingBaseException):
    """Market data service error."""

    def __init__(self, message: str, details: dict[str, Any] | None = None) -> None:
        super().__init__(message, code="MARKET_DATA_ERROR", details=details)


class SymbolNotFoundError(MarketDataError):
    """Symbol not found."""

    def __init__(self, ticker: str) -> None:
        super().__init__(f"Symbol '{ticker}' not found", details={"ticker": ticker})
        self.code = "SYMBOL_NOT_FOUND"


class DataFetchError(MarketDataError):
    """Error fetching data from broker API."""

    def __init__(self, message: str, broker: str = "unknown") -> None:
        super().__init__(message, details={"broker": broker})
        self.code = "DATA_FETCH_ERROR"


# ── Strategy Exceptions ──────────────────────────────────────────────────────


class StrategyError(TradingBaseException):
    """Strategy engine error."""

    def __init__(self, message: str, strategy_name: str | None = None) -> None:
        details = {"strategy": strategy_name} if strategy_name else {}
        super().__init__(message, code="STRATEGY_ERROR", details=details)


class InsufficientDataError(StrategyError):
    """Not enough data to compute strategy signals."""

    def __init__(self, required: int, available: int) -> None:
        super().__init__(
            f"Insufficient data: required {required}, available {available}",
            strategy_name=None,
        )
        self.code = "INSUFFICIENT_DATA"
        self.details.update({"required": required, "available": available})


# ── Risk Management Exceptions ───────────────────────────────────────────────


class RiskError(TradingBaseException):
    """Risk management error."""

    def __init__(self, message: str, details: dict[str, Any] | None = None) -> None:
        super().__init__(message, code="RISK_ERROR", details=details)


class RiskLimitBreachedError(RiskError):
    """Risk limit has been breached."""

    def __init__(self, limit_type: str, current_value: float, limit_value: float) -> None:
        super().__init__(
            f"Risk limit breached: {limit_type} is {current_value:.4f}, limit is {limit_value:.4f}",
            details={"limit_type": limit_type, "current": current_value, "limit": limit_value},
        )
        self.code = "RISK_LIMIT_BREACHED"


class DailyLossLimitError(RiskLimitBreachedError):
    """Daily loss limit exceeded."""

    def __init__(self, current_loss: float, limit: float) -> None:
        super().__init__("daily_loss", current_loss, limit)
        self.code = "DAILY_LOSS_LIMIT"


class MaxDrawdownError(RiskLimitBreachedError):
    """Maximum drawdown exceeded."""

    def __init__(self, current_drawdown: float, max_drawdown: float) -> None:
        super().__init__("max_drawdown", current_drawdown, max_drawdown)
        self.code = "MAX_DRAWDOWN_EXCEEDED"


# ── Execution Exceptions ─────────────────────────────────────────────────────


class ExecutionError(TradingBaseException):
    """Order execution error."""

    def __init__(self, message: str, order_id: str | None = None) -> None:
        details = {"order_id": order_id} if order_id else {}
        super().__init__(message, code="EXECUTION_ERROR", details=details)


class OrderRejectedError(ExecutionError):
    """Order was rejected by the broker."""

    def __init__(self, reason: str, order_id: str | None = None) -> None:
        super().__init__(f"Order rejected: {reason}", order_id=order_id)
        self.code = "ORDER_REJECTED"
        self.details["reason"] = reason


class BrokerConnectionError(ExecutionError):
    """Cannot connect to the broker API."""

    def __init__(self, broker: str, message: str) -> None:
        super().__init__(f"Broker connection error ({broker}): {message}")
        self.code = "BROKER_CONNECTION_ERROR"
        self.details["broker"] = broker


# ── AI Agent Exceptions ──────────────────────────────────────────────────────


class AgentError(TradingBaseException):
    """AI agent error."""

    def __init__(self, message: str, agent_type: str | None = None) -> None:
        details = {"agent_type": agent_type} if agent_type else {}
        super().__init__(message, code="AGENT_ERROR", details=details)


class ClaudeAPIError(AgentError):
    """Claude API error."""

    def __init__(self, message: str, status_code: int | None = None) -> None:
        super().__init__(message)
        self.code = "CLAUDE_API_ERROR"
        if status_code:
            self.details["status_code"] = status_code


class ContextBuildError(AgentError):
    """Error building context for AI agent."""

    def __init__(self, message: str) -> None:
        super().__init__(message)
        self.code = "CONTEXT_BUILD_ERROR"


# ── Validation Exceptions ────────────────────────────────────────────────────


class ValidationError(TradingBaseException):
    """Input validation error."""

    def __init__(self, message: str, field: str | None = None) -> None:
        details = {"field": field} if field else {}
        super().__init__(message, code="VALIDATION_ERROR", details=details)


class ConfigurationError(TradingBaseException):
    """Configuration error."""

    def __init__(self, message: str, setting: str | None = None) -> None:
        details = {"setting": setting} if setting else {}
        super().__init__(message, code="CONFIGURATION_ERROR", details=details)
