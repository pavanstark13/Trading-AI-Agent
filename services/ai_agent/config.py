"""AI Agent Service configuration."""

from functools import lru_cache

from pydantic_settings import BaseSettings


class AIAgentSettings(BaseSettings):
    service_name: str = "ai-agent"
    service_port: int = 8005
    max_tokens: int = 4096
    temperature: float = 0.1

    # Provider selection: "gemini" | "claude" | "groq"
    ai_provider: str = "gemini"

    # Gemini (Google AI Studio - free tier)
    gemini_api_key: str = ""
    gemini_model: str = "gemini-1.5-flash"  # free, fast, generous limits

    # Claude / Anthropic (paid - switch when ready)
    anthropic_api_key: str = ""
    claude_model: str = "claude-sonnet-4-6"

    # Service URLs
    market_data_service_url: str = "http://market-data:8001"
    strategy_engine_url: str = "http://strategy-engine:8002"
    risk_management_url: str = "http://risk-management:8003"
    execution_engine_url: str = "http://execution-engine:8004"
    monitoring_url: str = "http://monitoring:8006"

    # Database
    database_url: str = "postgresql+asyncpg://trader:trader_pass@localhost:5432/trading_db"
    redis_url: str = "redis://localhost:6379/0"

    agent_timeout_seconds: int = 120

    class Config:
        env_file = ".env"
        case_sensitive = False


@lru_cache
def get_settings() -> AIAgentSettings:
    return AIAgentSettings()
