"""Order execution API endpoints."""

import structlog
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from services.execution_engine.domain.schemas import OrderResponse, PlaceOrderRequest
from services.execution_engine.services.order_manager import OrderManager
from shared.database import get_db

router = APIRouter()
logger = structlog.get_logger(__name__)


@router.post("/place", response_model=OrderResponse, status_code=201)
async def place_order(
    request: PlaceOrderRequest,
    db: AsyncSession = Depends(get_db),
) -> OrderResponse:
    """Place a new order."""
    manager = OrderManager(db)
    try:
        order = await manager.place_order(request)
        return order
    except Exception as e:
        logger.error("Order placement failed", error=str(e))
        raise HTTPException(status_code=500, detail=f"Order placement failed: {e}")


@router.delete("/{external_order_id}")
async def cancel_order(
    external_order_id: str,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Cancel an open order."""
    manager = OrderManager(db)
    success = await manager.cancel_order(external_order_id)
    if not success:
        raise HTTPException(status_code=400, detail="Failed to cancel order")
    return {"status": "cancelled", "external_order_id": external_order_id}
