from datetime import datetime, timezone
from typing import Tuple, Optional, Dict, Any
from app.models.revenue_event import RevenueEvent
from app.models.customer import Customer
from app.ai.strategy import RecoveryStrategy
from app.schemas.policy import PolicyDecisionEnum, RuleIdEnum
from app.policies.guardrails import PolicyConfig, default_policy_config
from app.policies.eligibility import is_strategy_compatible


def evaluate_stopping_rules(
    event: RevenueEvent,
    customer: Customer,
    recovery_probability: float,
    recommended_strategy: RecoveryStrategy,
    previous_attempts_count: int = 0,
    config: Optional[PolicyConfig] = None
) -> Tuple[PolicyDecisionEnum, RuleIdEnum, str, bool]:
    """
    Deterministic rule priority evaluation pipeline.
    
    Priority Order:
    1. Already recovered -> NO_ACTION
    2. Customer opt-out -> NO_ACTION
    3. Recovery window expired -> BLOCK
    4. Maximum attempts exceeded -> BLOCK
    5. Low recovery probability -> NO_ACTION
    6. High-value transaction -> ESCALATE
    7. Strategy compatibility -> BLOCK
    8. Standard eligibility -> ALLOW
    """
    cfg = config or default_policy_config

    # Rule 1: Already recovered or stopped
    if event.status in ["recovered", "stopped"]:
        return (
            PolicyDecisionEnum.NO_ACTION,
            RuleIdEnum.ALREADY_RECOVERED,
            "Revenue has already been recovered or resolved.",
            False
        )

    # Rule 2: Customer Opt-out
    if customer.opt_out:
        return (
            PolicyDecisionEnum.NO_ACTION,
            RuleIdEnum.CUSTOMER_OPT_OUT,
            "Customer has opted out of recovery communications.",
            False
        )

    # Rule 3: Recovery Window Expired
    event_time = event.event_time or datetime.now(timezone.utc)
    if event_time.tzinfo is None:
        event_time = event_time.replace(tzinfo=timezone.utc)
    now_utc = datetime.now(timezone.utc)
    hours_since_event = (now_utc - event_time).total_seconds() / 3600.0

    if hours_since_event > cfg.recovery_window_hours:
        return (
            PolicyDecisionEnum.BLOCK,
            RuleIdEnum.RECOVERY_WINDOW_EXPIRED,
            f"Recovery window has expired ({hours_since_event:.1f} hours elapsed, max {cfg.recovery_window_hours} hours).",
            False
        )

    # Rule 4: Maximum Attempts Exceeded
    if previous_attempts_count >= cfg.max_automatic_attempts:
        return (
            PolicyDecisionEnum.BLOCK,
            RuleIdEnum.MAX_ATTEMPTS_EXCEEDED,
            f"Maximum automatic recovery attempts reached ({previous_attempts_count}/{cfg.max_automatic_attempts}).",
            False
        )

    # Rule 5: Low Recovery Probability
    if recovery_probability < cfg.minimum_recovery_probability:
        return (
            PolicyDecisionEnum.NO_ACTION,
            RuleIdEnum.LOW_RECOVERY_PROBABILITY,
            f"Recovery probability ({recovery_probability * 100:.1f}%) is below the minimum threshold ({cfg.minimum_recovery_probability * 100:.1f}%).",
            False
        )

    # Rule 6: High-Value Transaction Threshold
    if event.amount >= cfg.high_value_threshold_paise and cfg.require_human_approval_for_high_value:
        return (
            PolicyDecisionEnum.ESCALATE,
            RuleIdEnum.HIGH_VALUE_TRANSACTION,
            f"High-value revenue (₹{event.amount / 100:,.2f}) requires human approval.",
            True
        )

    # Rule 7: Strategy Compatibility Matrix Check
    if not is_strategy_compatible(event.event_type, recommended_strategy):
        return (
            PolicyDecisionEnum.BLOCK,
            RuleIdEnum.STRATEGY_INCOMPATIBLE,
            f"Recommended strategy '{recommended_strategy.value}' is not valid for event type '{event.event_type}'.",
            False
        )

    # Rule 8: Standard Eligibility Passed
    return (
        PolicyDecisionEnum.ALLOW,
        RuleIdEnum.STANDARD_ELIGIBILITY,
        "Event is eligible for the recommended recovery strategy.",
        False
    )
