"""AI Agent Service configuration."""

from functools import lru_cache

from shared.config import Settings


class AIAgentSettings(Settings):
    service_name: str = "ai-agent"
    service_port: int = 8005
    max_tokens: int = 4096
    temperature: float = 0.1  # Low temp for trading decisions
    agent_timeout_seconds: int = 120


@lru_cache()
def get_settings() -> AIAgentSettings:
    return AIAgentSettings()
