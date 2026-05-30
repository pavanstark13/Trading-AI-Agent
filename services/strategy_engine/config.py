"""Strategy Engine Service configuration."""

from functools import lru_cache

from shared.config import Settings


class StrategyEngineSettings(Settings):
    service_name: str = "strategy-engine"
    service_port: int = 8002
    signal_cache_ttl: int = 60  # seconds
    min_bars_required: int = 50


@lru_cache()
def get_settings() -> StrategyEngineSettings:
    return StrategyEngineSettings()
