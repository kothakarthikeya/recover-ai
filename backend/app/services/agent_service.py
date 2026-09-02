import uuid
from datetime import datetime, timezone
from typing import Dict, Any
from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from app.models.revenue_event import RevenueEvent
from app.models.customer import Customer
from app.models.recovery_attempt import RecoveryAttempt
from app.models.audit_log import AuditLog
from app.services import risk_service
from app.ai.agent import agent_instance


def analyze_and_recommend(db: Session, event_id: str) -> Dict[str, Any]:
    """
    Run AI Agent diagnosis & recommendation workflow on a revenue event.
    Appends an immutable AuditLog entry explicitly marked 'RECOMMENDATION — NOT EXECUTED'.
    Does NOT execute payment actions.
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

    # 1. Get or calculate ML risk assessment
    risk_dict = risk_service.get_risk_assessment_by_event_id(db, event_id=event_id)

    # 2. Count previous recovery attempts
    prev_attempts_count = db.query(RecoveryAttempt).filter(RecoveryAttempt.revenue_event_id == event_id).count()

    # 3. Generate AI agent recommendation
    rec = agent_instance.recommend(
        event=event,
        customer=customer,
        risk_data=risk_dict,
        previous_attempts_count=prev_attempts_count
    )

    rec["created_at"] = datetime.now(timezone.utc)

    # 4. Append immutable AuditLog entry
    audit_log = AuditLog(
        id=f"aud_{uuid.uuid4().hex[:12]}",
        revenue_event_id=event_id,
        action="AGENT_RECOMMENDATION_GENERATED",
        actor="AI_RECOVERY_AGENT",
        policy_result="RECOMMENDATION — NOT EXECUTED",
        details=(
            f"Diagnosis: {rec['diagnosis']}, "
            f"Recommended Strategy: {rec['recommended_strategy'].value}, "
            f"Expected Recovery: ₹{rec['expected_recovery_amount_paise'] / 100:.2f}. "
            f"Reasoning: {rec['reasoning']}"
        ),
        amount_recovered_paise=0,
        model_version=rec["agent_version"]
    )
    db.add(audit_log)
    db.commit()

    return rec


def get_agent_recommendation(db: Session, event_id: str) -> Dict[str, Any]:
    """Retrieve existing agent recommendation or calculate new recommendation."""
    # Check if an audit log recommendation exists
    audit = (
        db.query(AuditLog)
        .filter(AuditLog.revenue_event_id == event_id, AuditLog.action == "AGENT_RECOMMENDATION_GENERATED")
        .order_by(AuditLog.created_at.desc())
        .first()
    )
    if audit:
        # Re-run or return recommendation
        return analyze_and_recommend(db, event_id)

    return analyze_and_recommend(db, event_id)
