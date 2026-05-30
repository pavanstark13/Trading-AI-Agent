"""AI Agent Service - FastAPI application entry point."""

from contextlib import asynccontextmanager
from typing import AsyncGenerator

import structlog
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from prometheus_client import make_asgi_app

from services.ai_agent.api.v1.router import router
from services.ai_agent.config import get_settings
from shared.database import engine
from shared.logging_config import configure_logging
from shared.middleware import LoggingMiddleware, RequestIDMiddleware, TimingMiddleware
from shared.redis_client import close_redis_pool, get_redis_client

settings = get_settings()
configure_logging(settings.log_level, settings.service_name)
logger = structlog.get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    logger.info("Starting AI Agent Service")
    async with engine.connect() as conn:
        await conn.execute(__import__("sqlalchemy").text("SELECT 1"))
    await get_redis_client().ping()
    logger.info("AI Agent Service ready", model=settings.claude_model)
    yield
    await engine.dispose()
    await close_redis_pool()


app = FastAPI(
    title="AI Agent Service",
    description="Multi-agent AI system for trading decisions using Claude",
    version="0.1.0",
    lifespan=lifespan,
)
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])
app.add_middleware(LoggingMiddleware)
app.add_middleware(TimingMiddleware)
app.add_middleware(RequestIDMiddleware)
app.include_router(router, prefix="/api/v1")
metrics_app = make_asgi_app()
app.mount("/metrics", metrics_app)


@app.get("/")
async def root() -> dict:
    return {"service": "ai-agent", "status": "running", "model": settings.claude_model}
