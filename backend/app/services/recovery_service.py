import uuid
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import func
from fastapi import HTTPException, status

from app.models.revenue_event import RevenueEvent
from app.models.customer import Customer
from app.models.risk_assessment import RiskAssessment
from app.models.recovery_attempt import RecoveryAttempt
from app.models.recovery_event import RecoveryEvent
from app.models.audit_log import AuditLog
from app.services import risk_service, agent_service, policy_service
from app.services.razorpay_service import get_recovery_provider
from app.ai.strategy import RecoveryStrategy
from app.schemas.policy import PolicyDecisionEnum, RuleIdEnum
from app.schemas.recovery import (
    RecoveryAttemptStatusEnum,
    RecoveryExecuteResponse,
    BatchRecoveryResponse,
    OpportunityResponse
)


def execute_recovery(db: Session, event_id: str) -> Dict[str, Any]:
    """
    Execute bounded recovery workflow for a single revenue event.
    Must re-evaluate policy server-side and enforce strict idempotency.
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

    # 1. Idempotency Check: Prevent duplicate execution if already recovered
    existing_success = (
        db.query(RecoveryAttempt)
        .filter(RecoveryAttempt.revenue_event_id == event_id, RecoveryAttempt.status == "SUCCESS")
        .first()
    )
    if event.status == "recovered" or existing_success:
        return {
            "revenue_event_id": event.id,
            "attempt_id": existing_success.id if existing_success else f"att_cached_{event.id[:8]}",
            "strategy": RecoveryStrategy(existing_success.strategy) if existing_success else RecoveryStrategy.NO_ACTION,
            "policy_decision": PolicyDecisionEnum.NO_ACTION,
            "attempt_status": RecoveryAttemptStatusEnum.SUCCESS,
            "event_status": "recovered",
            "amount_attempted_paise": event.amount,
            "amount_recovered_paise": existing_success.audit_logs[0].amount_recovered_paise if existing_success and existing_success.audit_logs else event.amount,
            "provider_reference": existing_success.result_code if existing_success else "IDEMPOTENT_ALREADY_RECOVERED",
            "message": "Revenue has already been recovered.",
            "requires_human_approval": False,
            "executed_at": datetime.now(timezone.utc)
        }

    # 2. Authoritative Server-Side Policy Recheck
    policy_res = policy_service.evaluate_policy_for_event(db, event_id=event_id)
    policy_decision = policy_res["decision"]
    recommended_strategy = policy_res["recommended_strategy"]
    rule_id = policy_res["rule_id"]
    reason = policy_res["reason"]

    prev_attempts_count = db.query(RecoveryAttempt).filter(RecoveryAttempt.revenue_event_id == event_id).count()
    attempt_num = prev_attempts_count + 1

    # 3. Handle Non-ALLOW Policy Decisions (BLOCK, ESCALATE, NO_ACTION)
    if policy_decision != PolicyDecisionEnum.ALLOW:
        attempt_status = RecoveryAttemptStatusEnum.BLOCKED
        if policy_decision == PolicyDecisionEnum.ESCALATE:
            attempt_status = RecoveryAttemptStatusEnum.ESCALATED
            event.status = "escalated"
        elif policy_decision == PolicyDecisionEnum.NO_ACTION:
            attempt_status = RecoveryAttemptStatusEnum.STOPPED
            event.status = "stopped"
        else:
            event.status = "failed"

        attempt = RecoveryAttempt(
            id=f"att_{uuid.uuid4().hex[:12]}",
            revenue_event_id=event_id,
            strategy=recommended_strategy.value,
            status=attempt_status.value,
            attempt_number=attempt_num,
            initiated_at=datetime.now(timezone.utc),
            completed_at=datetime.now(timezone.utc),
            result_code=rule_id.value,
            error_message=reason
        )
        db.add(attempt)

        audit_action = f"RECOVERY_{attempt_status.value}"
        audit = AuditLog(
            id=f"aud_{uuid.uuid4().hex[:12]}",
            revenue_event_id=event_id,
            recovery_attempt_id=attempt.id,
            action=audit_action,
            actor="RECOVERY_EXECUTION_ENGINE",
            policy_result=policy_decision.value,
            details=f"Execution blocked by Policy Engine. Reason: {reason}",
            amount_recovered_paise=0
        )
        db.add(audit)
        db.commit()

        return {
            "revenue_event_id": event.id,
            "attempt_id": attempt.id,
            "strategy": recommended_strategy,
            "policy_decision": policy_decision,
            "attempt_status": attempt_status,
            "event_status": event.status,
            "amount_attempted_paise": event.amount,
            "amount_recovered_paise": 0,
            "provider_reference": None,
            "message": f"Execution suppressed by Policy Engine: {reason}",
            "requires_human_approval": policy_res["requires_human_approval"],
            "executed_at": datetime.now(timezone.utc)
        }

    # 4. Policy ALLOWED: Execute Recovery Attempt
    attempt = RecoveryAttempt(
        id=f"att_{uuid.uuid4().hex[:12]}",
        revenue_event_id=event_id,
        strategy=recommended_strategy.value,
        status="IN_PROGRESS",
        attempt_number=attempt_num,
        initiated_at=datetime.now(timezone.utc)
    )
    db.add(attempt)

    event.status = "in_recovery"

    db.add(AuditLog(
        id=f"aud_{uuid.uuid4().hex[:12]}",
        revenue_event_id=event_id,
        recovery_attempt_id=attempt.id,
        action="RECOVERY_STARTED",
        actor="RECOVERY_EXECUTION_ENGINE",
        policy_result="ALLOW",
        details=f"Initiating {recommended_strategy.value} recovery attempt #{attempt_num}.",
        amount_recovered_paise=0
    ))
    db.commit()

    # 5. Call Provider Abstraction
    risk_dict = risk_service.get_risk_assessment_by_event_id(db, event_id=event_id)
    recovery_prob = float(risk_dict.get("recovery_probability", 0.5))

    provider = get_recovery_provider()
    status_str, result_code, error_msg, provider_ref, amount_recovered_paise = provider.execute_recovery(
        event=event,
        customer=customer,
        strategy=recommended_strategy,
        recovery_probability=recovery_prob,
        attempt_number=attempt_num
    )

    # 6. Update Attempt & Event Outcome
    attempt.completed_at = datetime.now(timezone.utc)
    attempt.status = status_str
    attempt.result_code = result_code
    attempt.error_message = error_msg

    rec_event = RecoveryEvent(
        id=f"recevt_{uuid.uuid4().hex[:12]}",
        recovery_attempt_id=attempt.id,
        event_type=f"recovery_{status_str.lower()}",
        payload_json=f'{{"provider_ref": "{provider_ref}", "result_code": "{result_code}"}}'
    )
    db.add(rec_event)

    if status_str == "SUCCESS":
        event.status = "recovered"
        msg = f"The payment was successfully recovered using {recommended_strategy.value}."
        audit_action = "RECOVERY_SUCCEEDED"
    else:
        event.status = "failed"
        msg = f"Recovery attempt failed: {error_msg or result_code}"
        audit_action = "RECOVERY_FAILED"

    db.add(AuditLog(
        id=f"aud_{uuid.uuid4().hex[:12]}",
        revenue_event_id=event_id,
        recovery_attempt_id=attempt.id,
        action=audit_action,
        actor="RECOVERY_EXECUTION_ENGINE",
        policy_result=status_str,
        details=msg,
        amount_recovered_paise=amount_recovered_paise
    ))
    db.commit()

    return {
        "revenue_event_id": event.id,
        "attempt_id": attempt.id,
        "strategy": recommended_strategy,
        "policy_decision": policy_decision,
        "attempt_status": RecoveryAttemptStatusEnum(status_str),
        "event_status": event.status,
        "amount_attempted_paise": event.amount,
        "amount_recovered_paise": amount_recovered_paise,
        "provider_reference": provider_ref,
        "message": msg,
        "requires_human_approval": False,
        "executed_at": datetime.now(timezone.utc)
    }


def approve_and_execute_recovery(db: Session, event_id: str) -> Dict[str, Any]:
    """
    Merchant approval endpoint for ESCALATED events.
    Must re-check policy server-side before executing.
    """
    event = db.query(RevenueEvent).filter(RevenueEvent.id == event_id).first()
    if not event:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Revenue event '{event_id}' not found")

    customer = db.query(Customer).filter(Customer.id == event.customer_id).first()

    # Recheck policy with high-value approval overridden
    from app.policies.guardrails import default_policy_config, PolicyConfig
    approved_config = PolicyConfig(require_human_approval_for_high_value=False)

    policy_res = policy_service.evaluate_policy_for_event(db, event_id=event_id, custom_config=approved_config)
    if policy_res["decision"] != PolicyDecisionEnum.ALLOW:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Approval denied: Policy evaluation result is {policy_res['decision'].value} ({policy_res['reason']})"
        )

    # Policy allowed after approval -> Execute
    prev_attempts_count = db.query(RecoveryAttempt).filter(RecoveryAttempt.revenue_event_id == event_id).count()
    attempt_num = prev_attempts_count + 1
    strategy = policy_res["recommended_strategy"]

    attempt = RecoveryAttempt(
        id=f"att_{uuid.uuid4().hex[:12]}",
        revenue_event_id=event_id,
        strategy=strategy.value,
        status="IN_PROGRESS",
        attempt_number=attempt_num,
        initiated_at=datetime.now(timezone.utc)
    )
    db.add(attempt)
    db.commit()

    risk_dict = risk_service.get_risk_assessment_by_event_id(db, event_id=event_id)
    provider = get_recovery_provider()
    status_str, result_code, error_msg, provider_ref, amount_recovered_paise = provider.execute_recovery(
        event=event,
        customer=customer,
        strategy=strategy,
        recovery_probability=float(risk_dict.get("recovery_probability", 0.5)),
        attempt_number=attempt_num
    )

    attempt.completed_at = datetime.now(timezone.utc)
    attempt.status = status_str
    attempt.result_code = result_code
    attempt.error_message = error_msg

    if status_str == "SUCCESS":
        event.status = "recovered"
        msg = f"Approved recovery successfully executed using {strategy.value}."
    else:
        event.status = "failed"
        msg = f"Approved recovery attempt failed: {error_msg}"

    db.add(AuditLog(
        id=f"aud_{uuid.uuid4().hex[:12]}",
        revenue_event_id=event_id,
        recovery_attempt_id=attempt.id,
        action="HUMAN_APPROVAL_EXECUTED",
        actor="MERCHANT_ADMIN",
        policy_result=status_str,
        details=msg,
        amount_recovered_paise=amount_recovered_paise
    ))
    db.commit()

    return {
        "revenue_event_id": event.id,
        "attempt_id": attempt.id,
        "strategy": strategy,
        "policy_decision": PolicyDecisionEnum.ALLOW,
        "attempt_status": RecoveryAttemptStatusEnum(status_str),
        "event_status": event.status,
        "amount_attempted_paise": event.amount,
        "amount_recovered_paise": amount_recovered_paise,
        "provider_reference": provider_ref,
        "message": msg,
        "requires_human_approval": False,
        "executed_at": datetime.now(timezone.utc)
    }


def stop_recovery(db: Session, event_id: str) -> Dict[str, Any]:
    """Manually stop/suppress recovery workflow for an event."""
    event = db.query(RevenueEvent).filter(RevenueEvent.id == event_id).first()
    if not event:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Revenue event '{event_id}' not found")

    event.status = "stopped"

    attempt = RecoveryAttempt(
        id=f"att_{uuid.uuid4().hex[:12]}",
        revenue_event_id=event_id,
        strategy=RecoveryStrategy.NO_ACTION.value,
        status="STOPPED",
        initiated_at=datetime.now(timezone.utc),
        completed_at=datetime.now(timezone.utc),
        result_code="MANUALLY_STOPPED"
    )
    db.add(attempt)

    db.add(AuditLog(
        id=f"aud_{uuid.uuid4().hex[:12]}",
        revenue_event_id=event_id,
        recovery_attempt_id=attempt.id,
        action="RECOVERY_STOPPED",
        actor="MERCHANT_ADMIN",
        policy_result="STOPPED",
        details="Recovery workflow manually stopped by merchant.",
        amount_recovered_paise=0
    ))
    db.commit()

    return {
        "revenue_event_id": event.id,
        "attempt_id": attempt.id,
        "strategy": RecoveryStrategy.NO_ACTION,
        "policy_decision": PolicyDecisionEnum.NO_ACTION,
        "attempt_status": RecoveryAttemptStatusEnum.STOPPED,
        "event_status": "stopped",
        "amount_attempted_paise": event.amount,
        "amount_recovered_paise": 0,
        "provider_reference": None,
        "message": "Recovery workflow manually stopped.",
        "requires_human_approval": False,
        "executed_at": datetime.now(timezone.utc)
    }


def get_recovery_opportunities(
    db: Session,
    merchant_id: Optional[str] = None,
    limit: int = 50
) -> List[OpportunityResponse]:
    """
    Get eligible recovery opportunities sorted by business priority:
    1. Highest expected recovery amount
    2. Highest recovery probability
    3. Event age
    Excludes already recovered/stopped events.
    """
    query = db.query(RevenueEvent).filter(RevenueEvent.status.notin_(["recovered", "stopped"]))
    if merchant_id:
        query = query.filter(RevenueEvent.merchant_id == merchant_id)

    events = query.limit(limit * 2).all()
    opportunities = []

    for e in events:
        cust = db.query(Customer).filter(Customer.id == e.customer_id).first()
        if not cust or cust.opt_out:
            continue

        risk_dict = risk_service.get_risk_assessment_by_event_id(db, event_id=e.id)
        agent_dict = agent_service.get_agent_recommendation(db, event_id=e.id)
        policy_dict = policy_service.evaluate_policy_for_event(db, event_id=e.id)

        prob = float(risk_dict.get("recovery_probability", 0.5))
        exp_amount = int(round(e.amount * prob))

        opportunities.append(OpportunityResponse(
            revenue_event_id=e.id,
            merchant_id=e.merchant_id,
            customer_name=cust.name,
            event_type=e.event_type,
            amount_paise=e.amount,
            recovery_probability=prob,
            expected_recovery_amount_paise=exp_amount,
            risk_level=risk_dict.get("risk_level", "MEDIUM"),
            recommended_strategy=agent_dict["recommended_strategy"],
            policy_decision=policy_dict["decision"],
            event_time=e.event_time
        ))

    # Priority sorting: expected_recovery_amount desc, probability desc
    opportunities.sort(
        key=lambda x: (x.expected_recovery_amount_paise, x.recovery_probability),
        reverse=True
    )
    return opportunities[:limit]


def execute_batch_recovery(
    db: Session,
    merchant_id: Optional[str] = None,
    limit: int = 50
) -> BatchRecoveryResponse:
    """
    Execute batch recovery across eligible opportunities.
    Evaluates policy server-side and executes only ALLOW events.
    """
    opportunities = get_recovery_opportunities(db, merchant_id=merchant_id, limit=limit)

    results = []
    executed_count = 0
    successful_count = 0
    failed_count = 0
    blocked_count = 0
    escalated_count = 0
    total_attempted = 0
    total_recovered = 0
    total_expected = 0

    for opp in opportunities:
        total_expected += opp.expected_recovery_amount_paise
        res = execute_recovery(db, event_id=opp.revenue_event_id)
        res_obj = RecoveryExecuteResponse(**res)
        results.append(res_obj)

        if res_obj.attempt_status == RecoveryAttemptStatusEnum.SUCCESS:
            executed_count += 1
            successful_count += 1
            total_attempted += res_obj.amount_attempted_paise
            total_recovered += res_obj.amount_recovered_paise
        elif res_obj.attempt_status == RecoveryAttemptStatusEnum.FAILED:
            executed_count += 1
            failed_count += 1
            total_attempted += res_obj.amount_attempted_paise
        elif res_obj.attempt_status == RecoveryAttemptStatusEnum.ESCALATED:
            escalated_count += 1
        else:
            blocked_count += 1

    recovery_rate = (float(total_recovered) / float(total_attempted) * 100.0) if total_attempted > 0 else 0.0

    return BatchRecoveryResponse(
        total_opportunities=len(opportunities),
        eligible_count=len(opportunities),
        executed_count=executed_count,
        successful_count=successful_count,
        failed_count=failed_count,
        blocked_count=blocked_count,
        escalated_count=escalated_count,
        total_amount_attempted_paise=total_attempted,
        total_amount_recovered_paise=total_recovered,
        expected_recovery_amount_paise=total_expected,
        recovery_rate_percent=round(recovery_rate, 2),
        results=results
    )
