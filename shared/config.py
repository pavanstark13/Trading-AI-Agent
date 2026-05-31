"""Shared configuration using Pydantic BaseSettings."""

from functools import lru_cache

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Database
    database_url: str = "postgresql+asyncpg://trader:trader_pass@localhost:5432/trading_db"
    database_pool_size: int = 10
    database_max_overflow: int = 20

    # Redis
    redis_url: str = "redis://localhost:6379/0"
    redis_max_connections: int = 50

    # Services
    market_data_service_url: str = "http://market-data:8001"
    strategy_engine_url: str = "http://strategy-engine:8002"
    risk_management_url: str = "http://risk-management:8003"
    execution_engine_url: str = "http://execution-engine:8004"
    ai_agent_url: str = "http://ai-agent:8005"
    monitoring_url: str = "http://monitoring:8006"

    # AI
    anthropic_api_key: str = ""
    claude_model: str = "claude-sonnet-4-6"

    # Broker
    alpaca_api_key: str = ""
    alpaca_secret_key: str = ""
    alpaca_base_url: str = "https://paper-api.alpaca.markets"

    # Security
    secret_key: str = "dev_secret_key_change_in_production"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30

    # Cloud database/cache SSL settings
    # Neon requires SSL; Upstash requires TLS (rediss://)
    # Both are handled automatically by the connection strings,
    # but asyncpg needs ssl="require" explicitly for Neon.
    database_ssl: bool = True  # set False for local dev without SSL

    # App
    debug: bool = False
    environment: str = "development"
    log_level: str = "INFO"

    model_config = {"env_file": ".env", "case_sensitive": False, "extra": "ignore"}


@lru_cache
def get_settings() -> Settings:
    return Settings()
