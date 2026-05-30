"""Strategy Engine - API v1 router."""

from fastapi import APIRouter

from services.strategy_engine.api.v1.endpoints.health import router as health_router
from services.strategy_engine.api.v1.endpoints.strategy import router as strategy_router

router = APIRouter()
router.include_router(health_router, tags=["health"])
router.include_router(strategy_router, prefix="/strategy", tags=["strategy"])
