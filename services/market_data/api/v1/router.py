"""Market Data Service - API v1 router."""

from fastapi import APIRouter

from services.market_data.api.v1.endpoints.health import router as health_router
from services.market_data.api.v1.endpoints.market import router as market_router

router = APIRouter()
router.include_router(health_router, tags=["health"])
router.include_router(market_router, prefix="/market", tags=["market"])
