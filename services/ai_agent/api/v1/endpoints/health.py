"""Health check for AI Agent Service."""

from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from services.ai_agent.config import get_settings
from shared.database import get_db
from shared.redis_client import get_redis_client
from shared.schemas.base import HealthResponse

router = APIRouter()
settings = get_settings()


@router.get("/health", response_model=HealthResponse)
async def health_check(db: AsyncSession = Depends(get_db)) -> HealthResponse:
    details: dict = {"claude_model": settings.claude_model}
    try:
        await db.execute(text("SELECT 1"))
        details["database"] = "healthy"
    except Exception as e:
        details["database"] = f"unhealthy: {e}"
    try:
        await get_redis_client().ping()
        details["redis"] = "healthy"
    except Exception as e:
        details["redis"] = f"unhealthy: {e}"
    details["anthropic_configured"] = bool(settings.anthropic_api_key)
    status = "healthy" if all(v == "healthy" for k, v in details.items() if k in ("database", "redis")) else "degraded"
    return HealthResponse(service="ai-agent", status=status, details=details)
