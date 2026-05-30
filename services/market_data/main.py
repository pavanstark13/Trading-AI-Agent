"""Market Data Service - FastAPI application entry point."""

from contextlib import asynccontextmanager
from typing import AsyncGenerator

import structlog
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from prometheus_client import make_asgi_app

from services.market_data.api.v1.router import router
from services.market_data.config import get_settings
from shared.database import engine
from shared.logging_config import configure_logging
from shared.middleware import LoggingMiddleware, RequestIDMiddleware, TimingMiddleware
from shared.redis_client import close_redis_pool, get_redis_client

settings = get_settings()
configure_logging(settings.log_level, settings.service_name)
logger = structlog.get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan handler."""
    logger.info("Starting Market Data Service", port=settings.service_port)

    # Verify DB connection
    async with engine.connect() as conn:
        await conn.execute(__import__("sqlalchemy").text("SELECT 1"))
    logger.info("Database connection verified")

    # Verify Redis connection
    redis = get_redis_client()
    await redis.ping()
    logger.info("Redis connection verified")

    yield

    logger.info("Shutting down Market Data Service")
    await engine.dispose()
    await close_redis_pool()


app = FastAPI(
    title="Market Data Service",
    description="Real-time and historical market data provider",
    version="0.1.0",
    lifespan=lifespan,
)

# Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(LoggingMiddleware)
app.add_middleware(TimingMiddleware)
app.add_middleware(RequestIDMiddleware)

# Routes
app.include_router(router, prefix="/api/v1")

# Prometheus metrics endpoint
metrics_app = make_asgi_app()
app.mount("/metrics", metrics_app)


@app.get("/")
async def root() -> dict:
    return {"service": "market-data", "status": "running", "version": "0.1.0"}
