from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.analytics import (
    OverviewAnalyticsResponse,
    PipelineAnalyticsResponse,
    StrategyAnalyticsResponse,
    ScenarioAnalyticsResponse,
    TimeSeriesAnalyticsResponse,
    OpportunityDetailResponse,
    AuditSummaryResponse
)
from app.services import analytics_service

router = APIRouter(prefix="/api/v1/analytics", tags=["Analytics & Intelligence"])


@router.get("/overview", response_model=OverviewAnalyticsResponse)
def get_analytics_overview(
    merchant_id: Optional[str] = Query(None),
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    db: Session = Depends(get_db)
):
    """Retrieve core revenue recovery aggregate metrics and calculated KPIs."""
    return analytics_service.get_overview_analytics(
        db, merchant_id=merchant_id, start_date=start_date, end_date=end_date
    )


@router.get("/pipeline", response_model=PipelineAnalyticsResponse)
def get_analytics_pipeline(
    merchant_id: Optional[str] = Query(None),
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    db: Session = Depends(get_db)
):
    """Retrieve recovery funnel pipeline stage metrics."""
    return analytics_service.get_pipeline_analytics(
        db, merchant_id=merchant_id, start_date=start_date, end_date=end_date
    )


@router.get("/strategies", response_model=StrategyAnalyticsResponse)
def get_analytics_strategies(
    merchant_id: Optional[str] = Query(None),
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    db: Session = Depends(get_db)
):
    """Retrieve performance breakdown by recovery strategy."""
    return analytics_service.get_strategy_analytics(
        db, merchant_id=merchant_id, start_date=start_date, end_date=end_date
    )


@router.get("/scenarios", response_model=ScenarioAnalyticsResponse)
def get_analytics_scenarios(
    merchant_id: Optional[str] = Query(None),
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    db: Session = Depends(get_db)
):
    """Retrieve metrics broken down by 4 revenue loss scenarios."""
    return analytics_service.get_scenario_analytics(
        db, merchant_id=merchant_id, start_date=start_date, end_date=end_date
    )


@router.get("/timeseries", response_model=TimeSeriesAnalyticsResponse)
def get_analytics_timeseries(
    merchant_id: Optional[str] = Query(None),
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    db: Session = Depends(get_db)
):
    """Retrieve daily time-series aggregation for dashboard charts."""
    return analytics_service.get_timeseries_analytics(
        db, merchant_id=merchant_id, start_date=start_date, end_date=end_date
    )


@router.get("/opportunities", response_model=List[OpportunityDetailResponse])
def get_analytics_top_opportunities(
    merchant_id: Optional[str] = Query(None),
    limit: int = Query(10, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """Retrieve top recovery opportunities prioritized by expected recovery, probability, and risk amount."""
    return analytics_service.get_top_opportunities(db, merchant_id=merchant_id, limit=limit)


@router.get("/audit-summary", response_model=AuditSummaryResponse)
def get_analytics_audit_summary(
    merchant_id: Optional[str] = Query(None),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """Retrieve audit statistics and recent audit logs."""
    return analytics_service.get_audit_summary(db, merchant_id=merchant_id, limit=limit)
