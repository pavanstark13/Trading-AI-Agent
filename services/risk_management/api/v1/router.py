"""Risk Management - API v1 router."""

from fastapi import APIRouter

from services.risk_management.api.v1.endpoints.health import router as health_router
from services.risk_management.api.v1.endpoints.risk import router as risk_router

router = APIRouter()
router.include_router(health_router, tags=["health"])
router.include_router(risk_router, prefix="/risk", tags=["risk"])
