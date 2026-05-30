"""Monitoring Service - API v1 router."""

from fastapi import APIRouter

from services.monitoring.api.v1.endpoints.alerts import router as alerts_router
from services.monitoring.api.v1.endpoints.health import router as health_router
from services.monitoring.api.v1.endpoints.metrics import router as metrics_router

router = APIRouter()
router.include_router(health_router, tags=["health"])
router.include_router(metrics_router, prefix="/metrics-data", tags=["metrics"])
router.include_router(alerts_router, prefix="/alerts", tags=["alerts"])
