"""Alert management endpoints."""

import uuid

import structlog
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from services.monitoring.services.alerting import AlertingService
from shared.database import get_db
from shared.schemas.base import BaseSchema

router = APIRouter()
logger = structlog.get_logger(__name__)


class CreateAlertRequest(BaseSchema):
    alert_type: str
    severity: str  # info, warning, critical
    message: str
    metadata: dict = {}


@router.get("/")
async def list_alerts(
    unacknowledged_only: bool = True,
    db: AsyncSession = Depends(get_db),
) -> list[dict]:
    """List alerts."""
    service = AlertingService(db)
    return await service.list_alerts(unacknowledged_only=unacknowledged_only)


@router.post("/", status_code=201)
async def create_alert(
    request: CreateAlertRequest,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Create a new alert."""
    service = AlertingService(db)
    alert = await service.create_alert(
        alert_type=request.alert_type,
        severity=request.severity,
        message=request.message,
        metadata=request.metadata,
    )
    return alert


@router.post("/{alert_id}/acknowledge")
async def acknowledge_alert(
    alert_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Acknowledge an alert."""
    service = AlertingService(db)
    success = await service.acknowledge_alert(alert_id)
    if not success:
        raise HTTPException(status_code=404, detail="Alert not found")
    return {"status": "acknowledged", "alert_id": str(alert_id)}
