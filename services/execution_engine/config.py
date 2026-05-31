"""Execution Engine Service configuration."""

from functools import lru_cache

from shared.config import Settings


class ExecutionEngineSettings(Settings):
    service_name: str = "execution-engine"
    service_port: int = 8004
    paper_trading: bool = True
    order_timeout_seconds: int = 30


@lru_cache
def get_settings() -> ExecutionEngineSettings:
    return ExecutionEngineSettings()
