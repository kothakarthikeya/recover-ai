from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import func, cast, Date, text

from app.models.revenue_event import RevenueEvent
from app.models.customer import Customer
from app.models.risk_assessment import RiskAssessment
from app.models.recovery_attempt import RecoveryAttempt
from app.models.audit_log import AuditLog
from app.ai.strategy import RecoveryStrategy
from app.services import risk_service, agent_service, policy_service
from app.schemas.analytics import (
    OverviewAnalyticsResponse,
    PipelineStageItem,
    PipelineAnalyticsResponse,
    StrategyPerformanceItem,
    StrategyAnalyticsResponse,
    ScenarioPerformanceItem,
    ScenarioAnalyticsResponse,
    TimeSeriesDataPoint,
    TimeSeriesAnalyticsResponse,
    OpportunityDetailResponse,
    AuditSummaryItem,
    AuditSummaryResponse,
    format_paise_to_rupees,
    format_percentage
)


def get_overview_analytics(
    db: Session,
    merchant_id: Optional[str] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None
) -> OverviewAnalyticsResponse:
    query = db.query(RevenueEvent)
    if merchant_id:
        query = query.filter(RevenueEvent.merchant_id == merchant_id)
    if start_date:
        query = query.filter(RevenueEvent.event_time >= start_date)
    if end_date:
        query = query.filter(RevenueEvent.event_time <= end_date)

    total_events_count = query.count()
    events_analyzed_count = query.filter(RevenueEvent.status != "pending").count()

    total_revenue = int(query.with_entities(func.coalesce(func.sum(RevenueEvent.amount), 0)).scalar() or 0)
    
    # Revenue at Risk (unresolved: pending, risk_assessed, in_recovery, failed, escalated)
    at_risk_statuses = ["pending", "risk_assessed", "in_recovery", "failed", "escalated"]
    revenue_at_risk = int(query.filter(RevenueEvent.status.in_(at_risk_statuses)).with_entities(func.coalesce(func.sum(RevenueEvent.amount), 0)).scalar() or 0)

    # Actual Recovered (status == 'recovered')
    actual_recovered = int(query.filter(RevenueEvent.status == "recovered").with_entities(func.coalesce(func.sum(RevenueEvent.amount), 0)).scalar() or 0)
    unrecovered = total_revenue - actual_recovered

    # Attempted Recovery Amount from RecoveryAttempt
    attempt_query = db.query(RecoveryAttempt).join(RevenueEvent)
    if merchant_id:
        attempt_query = attempt_query.filter(RevenueEvent.merchant_id == merchant_id)
    if start_date:
        attempt_query = attempt_query.filter(RecoveryAttempt.initiated_at >= start_date)
    if end_date:
        attempt_query = attempt_query.filter(RecoveryAttempt.initiated_at <= end_date)

    total_attempts_count = attempt_query.count()
    succ_attempts_count = attempt_query.filter(RecoveryAttempt.status == "SUCCESS").count()

    # Attempted paise: sum of amounts for events with attempts
    attempted_events_query = query.filter(RevenueEvent.recovery_attempts.any())
    attempted_recovery_paise = int(attempted_events_query.with_entities(func.coalesce(func.sum(RevenueEvent.amount), 0)).scalar() or 0)

    # Expected Recovery from RiskAssessment (amount * recovery_probability)
    risk_query = db.query(RiskAssessment).join(RevenueEvent)
    if merchant_id:
        risk_query = risk_query.filter(RevenueEvent.merchant_id == merchant_id)
    if start_date:
        risk_query = risk_query.filter(RevenueEvent.event_time >= start_date)
    if end_date:
        risk_query = risk_query.filter(RevenueEvent.event_time <= end_date)

    risks = risk_query.all()
    expected_recovery_paise = sum(int(round(r.revenue_at_risk_paise * r.recovery_probability)) for r in risks)

    # Recovery Rate % = Actual Recovered / Attempted * 100
    recovery_rate_pct = (float(actual_recovered) / float(attempted_recovery_paise) * 100.0) if attempted_recovery_paise > 0 else 0.0

    return OverviewAnalyticsResponse(
        total_revenue_paise=total_revenue,
        revenue_at_risk_paise=revenue_at_risk,
        expected_recovery_paise=expected_recovery_paise,
        actual_recovered_paise=actual_recovered,
        unrecovered_paise=unrecovered,
        attempted_recovery_paise=attempted_recovery_paise,
        recovery_rate_percent=round(recovery_rate_pct, 2),
        total_events_count=total_events_count,
        events_analyzed_count=events_analyzed_count,
        total_recovery_attempts_count=total_attempts_count,
        successful_recoveries_count=succ_attempts_count,
        total_revenue_formatted=format_paise_to_rupees(total_revenue),
        revenue_at_risk_formatted=format_paise_to_rupees(revenue_at_risk),
        expected_recovery_formatted=format_paise_to_rupees(expected_recovery_paise),
        actual_recovered_formatted=format_paise_to_rupees(actual_recovered),
        recovery_rate_formatted=format_percentage(recovery_rate_pct / 100.0)
    )


def get_pipeline_analytics(
    db: Session,
    merchant_id: Optional[str] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None
) -> PipelineAnalyticsResponse:
    query = db.query(RevenueEvent)
    if merchant_id:
        query = query.filter(RevenueEvent.merchant_id == merchant_id)
    if start_date:
        query = query.filter(RevenueEvent.event_time >= start_date)
    if end_date:
        query = query.filter(RevenueEvent.event_time <= end_date)

    # 1. DETECTED
    detected_count = query.count()
    detected_paise = int(query.with_entities(func.coalesce(func.sum(RevenueEvent.amount), 0)).scalar() or 0)

    # 2. RISK_ANALYZED
    risk_q = query.filter(RevenueEvent.risk_assessments.any())
    risk_count = risk_q.count()
    risk_paise = int(risk_q.with_entities(func.coalesce(func.sum(RevenueEvent.amount), 0)).scalar() or 0)

    # 3. AI_RECOMMENDED
    ai_q = query.filter(RevenueEvent.audit_logs.any(AuditLog.action == "AGENT_RECOMMENDATION_GENERATED"))
    ai_count = ai_q.count()
    ai_paise = int(ai_q.with_entities(func.coalesce(func.sum(RevenueEvent.amount), 0)).scalar() or 0)

    # 4. POLICY_EVALUATED
    policy_q = query.filter(RevenueEvent.audit_logs.any(AuditLog.action == "POLICY_EVALUATED"))
    policy_count = policy_q.count()
    policy_paise = int(policy_q.with_entities(func.coalesce(func.sum(RevenueEvent.amount), 0)).scalar() or 0)

    # 5. ELIGIBLE (Policy ALLOWED)
    eligible_q = query.filter(RevenueEvent.audit_logs.any((AuditLog.action == "POLICY_EVALUATED") & (AuditLog.policy_result == "ALLOW")))
    eligible_count = eligible_q.count()
    eligible_paise = int(eligible_q.with_entities(func.coalesce(func.sum(RevenueEvent.amount), 0)).scalar() or 0)

    # 6. ATTEMPTED
    attempted_q = query.filter(RevenueEvent.recovery_attempts.any())
    attempted_count = attempted_q.count()
    attempted_paise = int(attempted_q.with_entities(func.coalesce(func.sum(RevenueEvent.amount), 0)).scalar() or 0)

    # 7. RECOVERED
    recovered_q = query.filter(RevenueEvent.status == "recovered")
    recovered_count = recovered_q.count()
    recovered_paise = int(recovered_q.with_entities(func.coalesce(func.sum(RevenueEvent.amount), 0)).scalar() or 0)

    pipeline_items = [
        PipelineStageItem(stage="DETECTED", count=detected_count, amount_paise=detected_paise, amount_formatted=format_paise_to_rupees(detected_paise)),
        PipelineStageItem(stage="RISK_ANALYZED", count=risk_count, amount_paise=risk_paise, amount_formatted=format_paise_to_rupees(risk_paise)),
        PipelineStageItem(stage="AI_RECOMMENDED", count=ai_count, amount_paise=ai_paise, amount_formatted=format_paise_to_rupees(ai_paise)),
        PipelineStageItem(stage="POLICY_EVALUATED", count=policy_count, amount_paise=policy_paise, amount_formatted=format_paise_to_rupees(policy_paise)),
        PipelineStageItem(stage="ELIGIBLE", count=eligible_count, amount_paise=eligible_paise, amount_formatted=format_paise_to_rupees(eligible_paise)),
        PipelineStageItem(stage="ATTEMPTED", count=attempted_count, amount_paise=attempted_paise, amount_formatted=format_paise_to_rupees(attempted_paise)),
        PipelineStageItem(stage="RECOVERED", count=recovered_count, amount_paise=recovered_paise, amount_formatted=format_paise_to_rupees(recovered_paise))
    ]

    return PipelineAnalyticsResponse(pipeline=pipeline_items)


def get_strategy_analytics(
    db: Session,
    merchant_id: Optional[str] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None
) -> StrategyAnalyticsResponse:
    items = []
    for strategy in RecoveryStrategy:
        query = db.query(RecoveryAttempt).join(RevenueEvent).filter(RecoveryAttempt.strategy == strategy.value)
        if merchant_id:
            query = query.filter(RevenueEvent.merchant_id == merchant_id)
        if start_date:
            query = query.filter(RecoveryAttempt.initiated_at >= start_date)
        if end_date:
            query = query.filter(RecoveryAttempt.initiated_at <= end_date)

        attempts_count = query.count()
        successes_count = query.filter(RecoveryAttempt.status == "SUCCESS").count()
        failures_count = query.filter(RecoveryAttempt.status == "FAILED").count()

        # Amount attempted & recovered for this strategy
        attempted_paise = int(query.with_entities(func.coalesce(func.sum(RevenueEvent.amount), 0)).scalar() or 0)
        recovered_paise = int(query.filter(RecoveryAttempt.status == "SUCCESS").with_entities(func.coalesce(func.sum(RevenueEvent.amount), 0)).scalar() or 0)

        success_rate = (float(successes_count) / float(attempts_count) * 100.0) if attempts_count > 0 else 0.0

        items.append(StrategyPerformanceItem(
            strategy=strategy,
            attempts_count=attempts_count,
            successes_count=successes_count,
            failures_count=failures_count,
            amount_attempted_paise=attempted_paise,
            amount_recovered_paise=recovered_paise,
            success_rate_percent=round(success_rate, 2),
            amount_attempted_formatted=format_paise_to_rupees(attempted_paise),
            amount_recovered_formatted=format_paise_to_rupees(recovered_paise)
        ))

    return StrategyAnalyticsResponse(strategies=items)


def get_scenario_analytics(
    db: Session,
    merchant_id: Optional[str] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None
) -> ScenarioAnalyticsResponse:
    scenarios = ["payment_failure", "checkout_abandonment", "subscription_failure", "overdue_invoice"]
    items = []

    for sc in scenarios:
        query = db.query(RevenueEvent).filter(RevenueEvent.event_type == sc)
        if merchant_id:
            query = query.filter(RevenueEvent.merchant_id == merchant_id)
        if start_date:
            query = query.filter(RevenueEvent.event_time >= start_date)
        if end_date:
            query = query.filter(RevenueEvent.event_time <= end_date)

        event_count = query.count()
        at_risk_statuses = ["pending", "risk_assessed", "in_recovery", "failed", "escalated"]
        amount_at_risk = int(query.filter(RevenueEvent.status.in_(at_risk_statuses)).with_entities(func.coalesce(func.sum(RevenueEvent.amount), 0)).scalar() or 0)

        # Expected recovery
        risks = db.query(RiskAssessment).join(RevenueEvent).filter(RevenueEvent.event_type == sc)
        if merchant_id:
            risks = risks.filter(RevenueEvent.merchant_id == merchant_id)
        expected_rec = sum(int(round(r.revenue_at_risk_paise * r.recovery_probability)) for r in risks.all())

        # Attempted & Recovered
        attempted_query = query.filter(RevenueEvent.recovery_attempts.any())
        amount_attempted = int(attempted_query.with_entities(func.coalesce(func.sum(RevenueEvent.amount), 0)).scalar() or 0)

        amount_recovered = int(query.filter(RevenueEvent.status == "recovered").with_entities(func.coalesce(func.sum(RevenueEvent.amount), 0)).scalar() or 0)
        rec_rate = (float(amount_recovered) / float(amount_attempted) * 100.0) if amount_attempted > 0 else 0.0

        items.append(ScenarioPerformanceItem(
            event_type=sc,
            event_count=event_count,
            amount_at_risk_paise=amount_at_risk,
            expected_recovery_paise=expected_rec,
            amount_attempted_paise=amount_attempted,
            amount_recovered_paise=amount_recovered,
            recovery_rate_percent=round(rec_rate, 2),
            amount_at_risk_formatted=format_paise_to_rupees(amount_at_risk),
            amount_recovered_formatted=format_paise_to_rupees(amount_recovered)
        ))

    return ScenarioAnalyticsResponse(scenarios=items)


def get_timeseries_analytics(
    db: Session,
    merchant_id: Optional[str] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None
) -> TimeSeriesAnalyticsResponse:
    """Group events and recoveries by date using strftime for SQLite compatibility."""
    # Use strftime for cross-DB date grouping (SQLite compatible)
    date_label = func.strftime("%Y-%m-%d", RevenueEvent.event_time).label("event_date")

    query = db.query(
        date_label,
        func.count(RevenueEvent.id).label("total_count"),
        func.coalesce(func.sum(RevenueEvent.amount), 0).label("total_amount")
    )
    if merchant_id:
        query = query.filter(RevenueEvent.merchant_id == merchant_id)
    if start_date:
        query = query.filter(RevenueEvent.event_time >= start_date)
    if end_date:
        query = query.filter(RevenueEvent.event_time <= end_date)

    daily_events = query.group_by(func.strftime("%Y-%m-%d", RevenueEvent.event_time)).order_by(func.strftime("%Y-%m-%d", RevenueEvent.event_time).asc()).all()

    points = []
    for date_str, count, total_amt in daily_events:
        # Calculate recovered amount for that date string
        rec_query = db.query(func.coalesce(func.sum(RevenueEvent.amount), 0)).filter(
            func.strftime("%Y-%m-%d", RevenueEvent.event_time) == date_str,
            RevenueEvent.status == "recovered"
        )
        if merchant_id:
            rec_query = rec_query.filter(RevenueEvent.merchant_id == merchant_id)
        recovered_amt = int(rec_query.scalar() or 0)

        # Expected recovery for that date
        exp_query = db.query(RiskAssessment).join(RevenueEvent).filter(
            func.strftime("%Y-%m-%d", RevenueEvent.event_time) == date_str
        )
        if merchant_id:
            exp_query = exp_query.filter(RevenueEvent.merchant_id == merchant_id)
        exp_amt = sum(int(round(r.revenue_at_risk_paise * r.recovery_probability)) for r in exp_query.all())

        points.append(TimeSeriesDataPoint(
            date=str(date_str),
            at_risk_paise=int(total_amt),
            expected_recovery_paise=exp_amt,
            attempted_paise=int(total_amt),
            recovered_paise=recovered_amt,
            attempts_count=int(count),
            successes_count=1 if recovered_amt > 0 else 0
        ))

    return TimeSeriesAnalyticsResponse(timeseries=points)


def get_top_opportunities(
    db: Session,
    merchant_id: Optional[str] = None,
    limit: int = 10
) -> List[OpportunityDetailResponse]:
    """Retrieve top recovery opportunities sorted by expected recovery, probability, and risk amount."""
    query = db.query(RevenueEvent).filter(RevenueEvent.status.notin_(["recovered", "stopped"]))
    if merchant_id:
        query = query.filter(RevenueEvent.merchant_id == merchant_id)

    events = query.limit(limit * 3).all()
    results = []

    for e in events:
        cust = db.query(Customer).filter(Customer.id == e.customer_id).first()
        if not cust or cust.opt_out:
            continue

        risk_dict = risk_service.get_risk_assessment_by_event_id(db, event_id=e.id)
        agent_dict = agent_service.get_agent_recommendation(db, event_id=e.id)
        policy_dict = policy_service.evaluate_policy_for_event(db, event_id=e.id)

        prob = float(risk_dict.get("recovery_probability", 0.5))
        exp_paise = int(round(e.amount * prob))

        results.append(OpportunityDetailResponse(
            revenue_event_id=e.id,
            customer_name=cust.name,
            event_type=e.event_type,
            amount_paise=e.amount,
            amount_formatted=format_paise_to_rupees(e.amount),
            recovery_probability=prob,
            recovery_probability_formatted=format_percentage(prob),
            expected_recovery_paise=exp_paise,
            expected_recovery_formatted=format_paise_to_rupees(exp_paise),
            risk_level=risk_dict.get("risk_level", "MEDIUM"),
            diagnosis=agent_dict["diagnosis"],
            recommended_strategy=agent_dict["recommended_strategy"],
            policy_decision=policy_dict["decision"],
            policy_reason=policy_dict["reason"],
            recommended_next_action=agent_dict["next_step"],
            event_time=e.event_time
        ))

    results.sort(
        key=lambda x: (x.expected_recovery_paise, x.recovery_probability, x.amount_paise),
        reverse=True
    )
    return results[:limit]


def get_audit_summary(
    db: Session,
    merchant_id: Optional[str] = None,
    limit: int = 20
) -> AuditSummaryResponse:
    query = db.query(AuditLog)
    if merchant_id:
        query = query.join(RevenueEvent).filter(RevenueEvent.merchant_id == merchant_id)

    total_recommendations = query.filter(AuditLog.action == "AGENT_RECOMMENDATION_GENERATED").count()
    total_policy_evaluations = query.filter(AuditLog.action == "POLICY_EVALUATED").count()
    total_executions = query.filter(AuditLog.action == "RECOVERY_STARTED").count()
    total_successes = query.filter(AuditLog.action == "RECOVERY_SUCCEEDED").count()
    total_failures = query.filter(AuditLog.action == "RECOVERY_FAILED").count()
    total_escalations = query.filter(AuditLog.policy_result == "ESCALATE").count()
    total_blocks = query.filter(AuditLog.policy_result == "BLOCK").count()

    recent = query.order_by(AuditLog.created_at.desc()).limit(limit).all()
    recent_items = [
        AuditSummaryItem(
            id=a.id,
            revenue_event_id=a.revenue_event_id,
            action=a.action,
            actor=a.actor,
            policy_result=a.policy_result,
            details=a.details,
            amount_recovered_paise=a.amount_recovered_paise,
            created_at=a.created_at
        )
        for a in recent
    ]

    return AuditSummaryResponse(
        total_recommendations=total_recommendations,
        total_policy_evaluations=total_policy_evaluations,
        total_executions=total_executions,
        total_successes=total_successes,
        total_failures=total_failures,
        total_escalations=total_escalations,
        total_blocks=total_blocks,
        recent_logs=recent_items
    )
