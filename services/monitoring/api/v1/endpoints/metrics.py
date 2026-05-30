"""Metrics endpoints for the monitoring service."""

from datetime import datetime, timezone

import structlog
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from services.monitoring.services.metrics_collector import MetricsCollector
from shared.database import get_db
from shared.schemas.base import BaseSchema

router = APIRouter()
logger = structlog.get_logger(__name__)


class RecordMetricRequest(BaseSchema):
    metric_name: str
    metric_value: float
    dimensions: dict = {}


@router.post("/record")
async def record_metric(
    request: RecordMetricRequest,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Record a performance metric."""
    collector = MetricsCollector(db)
    await collector.record(request.metric_name, request.metric_value, request.dimensions)
    return {"status": "recorded", "metric": request.metric_name}


@router.get("/summary")
async def get_metrics_summary(db: AsyncSession = Depends(get_db)) -> dict:
    """Get summary of recent metrics."""
    collector = MetricsCollector(db)
    return await collector.get_summary()
