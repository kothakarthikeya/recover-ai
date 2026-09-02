from datetime import datetime
from typing import Optional
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.revenue import (
    RevenueOverviewResponse,
    RevenueEventListResponse,
    RevenueEventResponse,
    RevenueImportRequest,
    RevenueImportResponse
)
from app.services import revenue_service

router = APIRouter(prefix="/api/v1/revenue", tags=["Revenue"])


@router.get("/overview", response_model=RevenueOverviewResponse)
def get_revenue_overview(
    merchant_id: Optional[str] = Query(None, description="Optional merchant filter"),
    db: Session = Depends(get_db)
):
    """Retrieve dynamic calculated aggregate revenue metrics from database."""
    return revenue_service.get_revenue_overview(db, merchant_id=merchant_id)


@router.get("/events", response_model=RevenueEventListResponse)
def get_revenue_events(
    merchant_id: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    event_type: Optional[str] = Query(None, description="Filter by payment_failure, checkout_abandonment, subscription_failure, overdue_invoice"),
    status: Optional[str] = Query(None, description="Filter by event status"),
    min_amount: Optional[int] = Query(None, ge=0, description="Minimum amount in paise"),
    max_amount: Optional[int] = Query(None, ge=0, description="Maximum amount in paise"),
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    db: Session = Depends(get_db)
):
    """Retrieve paginated and filtered list of revenue events."""
    return revenue_service.get_revenue_events(
        db,
        merchant_id=merchant_id,
        page=page,
        page_size=page_size,
        event_type=event_type,
        status_val=status,
        min_amount=min_amount,
        max_amount=max_amount,
        start_date=start_date,
        end_date=end_date
    )


@router.get("/events/{id}", response_model=RevenueEventResponse)
def get_revenue_event_by_id(
    id: str,
    db: Session = Depends(get_db)
):
    """Retrieve complete event details along with customer background history."""
    return revenue_service.get_revenue_event_by_id(db, event_id=id)


@router.post("/import", response_model=RevenueImportResponse, status_code=status.HTTP_201_CREATED)
def import_revenue_events(
    payload: RevenueImportRequest,
    db: Session = Depends(get_db)
):
    """Import batch synthetic/demo revenue events safely with strict validation."""
    count = revenue_service.import_revenue_events(
        db,
        merchant_id=payload.merchant_id,
        events=payload.events
    )
    return RevenueImportResponse(
        imported_count=count,
        message=f"Successfully imported {count} revenue events."
    )
