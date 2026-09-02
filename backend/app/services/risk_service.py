import uuid
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from app.models.revenue_event import RevenueEvent
from app.models.customer import Customer
from app.models.risk_assessment import RiskAssessment
from app.models.recovery_attempt import RecoveryAttempt
from app.models.audit_log import AuditLog
from app.ml.predictor import predictor
from app.schemas.risk import RiskAssessmentResponse, BatchRiskAnalysisResponse


def analyze_event_risk(db: Session, event_id: str) -> Dict[str, Any]:
    """
    Run risk analysis on a single revenue event, persist RiskAssessment and AuditLog.
    """
    event = db.query(RevenueEvent).filter(RevenueEvent.id == event_id).first()
    if not event:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Revenue event with ID '{event_id}' not found"
        )

    customer = db.query(Customer).filter(Customer.id == event.customer_id).first()
    if not customer:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Associated customer '{event.customer_id}' not found"
        )

    # Previous attempts and successful recoveries count
    prev_attempts = db.query(RecoveryAttempt).filter(RecoveryAttempt.revenue_event_id == event_id).all()
    prev_attempts_count = len(prev_attempts)
    prev_success_count = sum(1 for a in prev_attempts if a.status == "successful")

    # Run ML prediction
    prediction = predictor.predict_event(
        event=event,
        customer=customer,
        previous_attempts_count=prev_attempts_count,
        previous_successful_count=prev_success_count
    )

    # Upsert or create RiskAssessment record
    existing_risk = db.query(RiskAssessment).filter(RiskAssessment.revenue_event_id == event_id).first()
    if existing_risk:
        existing_risk.risk_score = prediction["risk_score"]
        existing_risk.recovery_probability = prediction["recovery_probability"]
        existing_risk.risk_level = prediction["risk_level"]
        existing_risk.revenue_at_risk_paise = event.amount
        existing_risk.model_version = prediction["model_version"]
        risk_assessment = existing_risk
    else:
        risk_assessment = RiskAssessment(
            id=f"risk_{uuid.uuid4().hex[:12]}",
            revenue_event_id=event_id,
            risk_score=prediction["risk_score"],
            recovery_probability=prediction["recovery_probability"],
            risk_level=prediction["risk_level"],
            revenue_at_risk_paise=event.amount,
            model_version=prediction["model_version"]
        )
        db.add(risk_assessment)

    # Update RevenueEvent status to 'risk_assessed' if it was 'pending'
    if event.status == "pending":
        event.status = "risk_assessed"

    # Create immutable AuditLog entry
    audit_log = AuditLog(
        id=f"aud_{uuid.uuid4().hex[:12]}",
        revenue_event_id=event_id,
        action="RISK_ANALYZED",
        actor="ML_PREDICTION_ENGINE",
        policy_result="COMPLETED",
        details=(
            f"Evaluated recovery probability: {prediction['recovery_probability'] * 100:.1f}%, "
            f"Risk Level: {prediction['risk_level']}, Expected Recovery: ₹{prediction['expected_recovery_amount'] / 100:.2f}"
        ),
        amount_recovered_paise=0,
        model_version=prediction["model_version"]
    )
    db.add(audit_log)
    db.commit()
    db.refresh(risk_assessment)

    return {
        "id": risk_assessment.id,
        "revenue_event_id": risk_assessment.revenue_event_id,
        "risk_score": risk_assessment.risk_score,
        "recovery_probability": risk_assessment.recovery_probability,
        "risk_level": risk_assessment.risk_level,
        "revenue_at_risk_paise": risk_assessment.revenue_at_risk_paise,
        "expected_recovery_amount_paise": prediction["expected_recovery_amount"],
        "model_version": risk_assessment.model_version,
        "created_at": risk_assessment.created_at
    }


def analyze_batch_risk(db: Session, event_ids: List[str]) -> BatchRiskAnalysisResponse:
    """
    Run risk analysis on a batch of revenue events and summarize dynamic totals.
    """
    if not event_ids:
        return BatchRiskAnalysisResponse(
            events_analyzed=0,
            total_revenue_at_risk_paise=0,
            estimated_recoverable_revenue_paise=0,
            risk_level_counts={"LOW": 0, "MEDIUM": 0, "HIGH": 0, "CRITICAL": 0},
            assessments=[]
        )

    assessments_res = []
    total_at_risk = 0
    total_expected_recovery = 0
    risk_level_counts = {"LOW": 0, "MEDIUM": 0, "HIGH": 0, "CRITICAL": 0}

    for eid in event_ids:
        try:
            res_dict = analyze_event_risk(db, eid)
            assessment_obj = RiskAssessmentResponse(**res_dict)
            assessments_res.append(assessment_obj)

            total_at_risk += assessment_obj.revenue_at_risk_paise
            total_expected_recovery += assessment_obj.expected_recovery_amount_paise
            
            level = assessment_obj.risk_level
            risk_level_counts[level] = risk_level_counts.get(level, 0) + 1
        except HTTPException:
            # Skip invalid event IDs in batch analysis or raise
            continue

    return BatchRiskAnalysisResponse(
        events_analyzed=len(assessments_res),
        total_revenue_at_risk_paise=total_at_risk,
        estimated_recoverable_revenue_paise=total_expected_recovery,
        risk_level_counts=risk_level_counts,
        assessments=assessments_res
    )


def get_risk_assessment_by_event_id(db: Session, event_id: str) -> Dict[str, Any]:
    """Retrieve existing risk assessment for a revenue event or analyze if not present."""
    existing = db.query(RiskAssessment).filter(RiskAssessment.revenue_event_id == event_id).first()
    if existing:
        event = db.query(RevenueEvent).filter(RevenueEvent.id == event_id).first()
        amount = event.amount if event else existing.revenue_at_risk_paise
        expected_recovery = int(round(amount * existing.recovery_probability))
        return {
            "id": existing.id,
            "revenue_event_id": existing.revenue_event_id,
            "risk_score": existing.risk_score,
            "recovery_probability": existing.recovery_probability,
            "risk_level": existing.risk_level,
            "revenue_at_risk_paise": existing.revenue_at_risk_paise,
            "expected_recovery_amount_paise": expected_recovery,
            "model_version": existing.model_version,
            "created_at": existing.created_at
        }
    return analyze_event_risk(db, event_id)
