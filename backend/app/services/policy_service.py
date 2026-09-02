import uuid
from datetime import datetime, timezone
from typing import Dict, Any, Optional
from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from app.models.revenue_event import RevenueEvent
from app.models.customer import Customer
from app.models.recovery_attempt import RecoveryAttempt
from app.models.audit_log import AuditLog
from app.services import risk_service, agent_service
from app.ai.strategy import RecoveryStrategy
from app.policies.guardrails import PolicyConfig, default_policy_config
from app.policies.stopping_rules import evaluate_stopping_rules
from app.schemas.policy import PolicyDecisionResponse, PolicyDecisionEnum, RuleIdEnum


def evaluate_policy_for_event(
    db: Session,
    event_id: str,
    custom_config: Optional[PolicyConfig] = None
) -> Dict[str, Any]:
    """
    Authoritative server-side policy evaluation.
    Evaluates ML probability, AI recommendation, and deterministic safety guardrails.
    Appends AuditLog record. Does NOT execute recovery.
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

    # 1. Obtain risk assessment (ML prediction)
    risk_dict = risk_service.get_risk_assessment_by_event_id(db, event_id=event_id)
    recovery_prob = float(risk_dict.get("recovery_probability", 0.5))

    # 2. Obtain latest agent recommendation
    rec_dict = agent_service.get_agent_recommendation(db, event_id=event_id)
    strategy_val = rec_dict.get("recommended_strategy")
    if isinstance(strategy_val, str):
        recommended_strategy = RecoveryStrategy(strategy_val)
    else:
        recommended_strategy = strategy_val

    # 3. Count previous automatic recovery attempts
    prev_attempts_count = db.query(RecoveryAttempt).filter(RecoveryAttempt.revenue_event_id == event_id).count()

    # 4. Evaluate policy pipeline
    decision, rule_id, reason, requires_human_approval = evaluate_stopping_rules(
        event=event,
        customer=customer,
        recovery_probability=recovery_prob,
        recommended_strategy=recommended_strategy,
        previous_attempts_count=prev_attempts_count,
        config=custom_config or default_policy_config
    )

    evaluated_at = datetime.now(timezone.utc)

    # 5. Append immutable AuditLog record
    audit_log = AuditLog(
        id=f"aud_{uuid.uuid4().hex[:12]}",
        revenue_event_id=event_id,
        action="POLICY_EVALUATED",
        actor="DETERMINISTIC_POLICY_ENGINE",
        policy_result=decision.value,
        details=f"Rule: {rule_id.value}. Decision: {decision.value}. Strategy: {recommended_strategy.value}. Reason: {reason}",
        amount_recovered_paise=0,
        model_version=rec_dict.get("agent_version", "v1.0.0")
    )
    db.add(audit_log)
    db.commit()

    return {
        "revenue_event_id": event.id,
        "decision": decision,
        "reason": reason,
        "rule_id": rule_id,
        "recommended_strategy": recommended_strategy,
        "requires_human_approval": requires_human_approval,
        "evaluated_at": evaluated_at
    }


def get_policy_decision(
    db: Session,
    event_id: str
) -> Dict[str, Any]:
    """Retrieve policy decision for event."""
    return evaluate_policy_for_event(db, event_id=event_id)
