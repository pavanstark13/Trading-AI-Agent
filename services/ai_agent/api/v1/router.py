"""AI Agent Service - API v1 router."""

from fastapi import APIRouter

from services.ai_agent.api.v1.endpoints.agent import router as agent_router
from services.ai_agent.api.v1.endpoints.health import router as health_router
from services.ai_agent.api.v1.endpoints.market import router as market_router
from services.ai_agent.api.v1.endpoints.portfolio import router as portfolio_router

router = APIRouter()
router.include_router(health_router, tags=["health"])
router.include_router(agent_router, prefix="/agent", tags=["agent"])
router.include_router(market_router, prefix="/market", tags=["market"])
router.include_router(portfolio_router, prefix="/portfolio", tags=["portfolio"])
