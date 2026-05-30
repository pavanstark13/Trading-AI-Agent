"""Monitoring Service configuration."""

from functools import lru_cache
from shared.config import Settings


class MonitoringSettings(Settings):
    service_name: str = "monitoring"
    service_port: int = 8006
    alert_cooldown_seconds: int = 300


@lru_cache()
def get_settings() -> MonitoringSettings:
    return MonitoringSettings()
