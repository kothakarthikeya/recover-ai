from typing import List, Optional
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.recovery import (
    RecoveryExecuteResponse,
    BatchRecoveryRequest,
    BatchRecoveryResponse,
    OpportunityResponse
)
from app.services import recovery_service

router = APIRouter(prefix="/api/v1/recovery", tags=["Recovery Execution Engine"])


@router.get("/opportunities", response_model=List[OpportunityResponse])
def get_recovery_opportunities_endpoint(
    merchant_id: Optional[str] = Query(None),
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db)
):
    """Retrieve recovery opportunities sorted by expected recovery amount, recovery probability, and event age."""
    return recovery_service.get_recovery_opportunities(db, merchant_id=merchant_id, limit=limit)


@router.post("/execute-batch", response_model=BatchRecoveryResponse)
def execute_batch_recovery_endpoint(
    payload: BatchRecoveryRequest,
    db: Session = Depends(get_db)
):
    """Execute batch recovery across eligible events authorized by Policy Engine."""
    return recovery_service.execute_batch_recovery(db, merchant_id=payload.merchant_id, limit=payload.limit or 50)


@router.get("/{event_id}", response_model=RecoveryExecuteResponse)
def get_recovery_event_status_endpoint(
    event_id: str,
    db: Session = Depends(get_db)
):
    """Get recovery status or evaluate execution for a single revenue event."""
    res = recovery_service.execute_recovery(db, event_id=event_id)
    return RecoveryExecuteResponse(**res)


@router.post("/{event_id}/execute", response_model=RecoveryExecuteResponse)
def execute_single_recovery_endpoint(
    event_id: str,
    db: Session = Depends(get_db)
):
    """Execute bounded recovery workflow for a single revenue event (server-side policy re-checked)."""
    res = recovery_service.execute_recovery(db, event_id=event_id)
    return RecoveryExecuteResponse(**res)


@router.post("/{event_id}/approve", response_model=RecoveryExecuteResponse)
def approve_and_execute_recovery_endpoint(
    event_id: str,
    db: Session = Depends(get_db)
):
    """Merchant manual approval for high-value / ESCALATED revenue events."""
    res = recovery_service.approve_and_execute_recovery(db, event_id=event_id)
    return RecoveryExecuteResponse(**res)


@router.post("/{event_id}/stop", response_model=RecoveryExecuteResponse)
def stop_recovery_endpoint(
    event_id: str,
    db: Session = Depends(get_db)
):
    """Manually stop and suppress recovery workflow for a revenue event."""
    res = recovery_service.stop_recovery(db, event_id=event_id)
    return RecoveryExecuteResponse(**res)
