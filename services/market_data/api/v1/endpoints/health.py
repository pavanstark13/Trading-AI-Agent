"""Health check endpoint for Market Data Service."""

import structlog
from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from shared.database import get_db
from shared.redis_client import get_redis_client
from shared.schemas.base import HealthResponse

router = APIRouter()
logger = structlog.get_logger(__name__)


@router.get("/health", response_model=HealthResponse)
async def health_check(db: AsyncSession = Depends(get_db)) -> HealthResponse:
    """Check service health including DB and Redis connectivity."""
    details: dict = {}

    # Check DB
    try:
        await db.execute(text("SELECT 1"))
        details["database"] = "healthy"
    except Exception as e:
        details["database"] = f"unhealthy: {e}"

    # Check Redis
    try:
        redis = get_redis_client()
        await redis.ping()
        details["redis"] = "healthy"
    except Exception as e:
        details["redis"] = f"unhealthy: {e}"

    status = "healthy" if all(v == "healthy" for v in details.values()) else "degraded"

    return HealthResponse(service="market-data", status=status, details=details)
