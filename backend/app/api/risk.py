from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.risk import (
    RiskAssessmentResponse,
    BatchRiskAnalysisRequest,
    BatchRiskAnalysisResponse
)
from app.services import risk_service

router = APIRouter(prefix="/api/v1/risk", tags=["Risk & Prediction"])


@router.post("/analyze/{event_id}", response_model=RiskAssessmentResponse)
def analyze_single_event_risk(
    event_id: str,
    db: Session = Depends(get_db)
):
    """Analyze single revenue event risk using ML model, persist assessment & audit log."""
    res = risk_service.analyze_event_risk(db, event_id=event_id)
    return RiskAssessmentResponse(**res)


@router.post("/analyze-batch", response_model=BatchRiskAnalysisResponse)
def analyze_batch_events_risk(
    payload: BatchRiskAnalysisRequest,
    db: Session = Depends(get_db)
):
    """Analyze a batch of revenue events and summarize dynamic risk aggregate metrics."""
    return risk_service.analyze_batch_risk(db, event_ids=payload.event_ids)


@router.get("/{event_id}", response_model=RiskAssessmentResponse)
def get_risk_assessment(
    event_id: str,
    db: Session = Depends(get_db)
):
    """Get risk assessment for a revenue event."""
    res = risk_service.get_risk_assessment_by_event_id(db, event_id=event_id)
    return RiskAssessmentResponse(**res)
