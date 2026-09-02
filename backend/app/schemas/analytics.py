from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, ConfigDict
from app.ai.strategy import RecoveryStrategy
from app.schemas.policy import PolicyDecisionEnum


def format_paise_to_rupees(paise: int) -> str:
    """Format integer paise to Indian Rupee string representation (e.g. 1250000 -> ₹12,500.00)."""
    rupees = paise / 100.0
    return f"₹{rupees:,.2f}"


def format_percentage(prob_or_rate: float) -> str:
    """Format decimal/rate to percentage string (e.g. 0.74 -> 74.0%)."""
    return f"{prob_or_rate * 100.0:.1f}%"


class OverviewAnalyticsResponse(BaseModel):
    total_revenue_paise: int
    revenue_at_risk_paise: int
    expected_recovery_paise: int
    actual_recovered_paise: int
    unrecovered_paise: int
    attempted_recovery_paise: int
    recovery_rate_percent: float
    total_events_count: int
    events_analyzed_count: int
    total_recovery_attempts_count: int
    successful_recoveries_count: int

    # Formatted representations for merchant UI
    total_revenue_formatted: str
    revenue_at_risk_formatted: str
    expected_recovery_formatted: str
    actual_recovered_formatted: str
    recovery_rate_formatted: str

    model_config = ConfigDict(from_attributes=True)


class PipelineStageItem(BaseModel):
    stage: str  # DETECTED, RISK_ANALYZED, AI_RECOMMENDED, POLICY_EVALUATED, ELIGIBLE, ATTEMPTED, RECOVERED
    count: int
    amount_paise: int
    amount_formatted: str


class PipelineAnalyticsResponse(BaseModel):
    pipeline: List[PipelineStageItem]


class StrategyPerformanceItem(BaseModel):
    strategy: RecoveryStrategy
    attempts_count: int
    successes_count: int
    failures_count: int
    amount_attempted_paise: int
    amount_recovered_paise: int
    success_rate_percent: float
    amount_attempted_formatted: str
    amount_recovered_formatted: str


class StrategyAnalyticsResponse(BaseModel):
    strategies: List[StrategyPerformanceItem]


class ScenarioPerformanceItem(BaseModel):
    event_type: str  # payment_failure, checkout_abandonment, subscription_failure, overdue_invoice
    event_count: int
    amount_at_risk_paise: int
    expected_recovery_paise: int
    amount_attempted_paise: int
    amount_recovered_paise: int
    recovery_rate_percent: float
    amount_at_risk_formatted: str
    amount_recovered_formatted: str


class ScenarioAnalyticsResponse(BaseModel):
    scenarios: List[ScenarioPerformanceItem]


class TimeSeriesDataPoint(BaseModel):
    date: str  # YYYY-MM-DD
    at_risk_paise: int
    expected_recovery_paise: int
    attempted_paise: int
    recovered_paise: int
    attempts_count: int
    successes_count: int


class TimeSeriesAnalyticsResponse(BaseModel):
    timeseries: List[TimeSeriesDataPoint]


class OpportunityDetailResponse(BaseModel):
    revenue_event_id: str
    customer_name: str
    event_type: str
    amount_paise: int
    amount_formatted: str
    recovery_probability: float
    recovery_probability_formatted: str
    expected_recovery_paise: int
    expected_recovery_formatted: str
    risk_level: str
    diagnosis: str
    recommended_strategy: RecoveryStrategy
    policy_decision: PolicyDecisionEnum
    policy_reason: str
    recommended_next_action: str
    event_time: datetime

    model_config = ConfigDict(from_attributes=True)


class AuditSummaryItem(BaseModel):
    id: str
    revenue_event_id: str
    action: str
    actor: str
    policy_result: str
    details: Optional[str] = None
    amount_recovered_paise: int
    created_at: datetime


class AuditSummaryResponse(BaseModel):
    total_recommendations: int
    total_policy_evaluations: int
    total_executions: int
    total_successes: int
    total_failures: int
    total_escalations: int
    total_blocks: int
    recent_logs: List[AuditSummaryItem]
