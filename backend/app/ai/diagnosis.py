from enum import Enum
from typing import Dict, Any
from app.models.revenue_event import RevenueEvent
from app.models.customer import Customer


class DiagnosisCategory(str, Enum):
    TEMPORARY_PAYMENT_FAILURE = "TEMPORARY_PAYMENT_FAILURE"
    REPEATED_PAYMENT_FAILURE = "REPEATED_PAYMENT_FAILURE"
    CHECKOUT_ABANDONMENT = "CHECKOUT_ABANDONMENT"
    SUBSCRIPTION_RENEWAL_FAILURE = "SUBSCRIPTION_RENEWAL_FAILURE"
    OVERDUE_RECEIVABLE = "OVERDUE_RECEIVABLE"
    HIGH_VALUE_RISK = "HIGH_VALUE_RISK"
    LOW_RECOVERY_PROBABILITY = "LOW_RECOVERY_PROBABILITY"
    CUSTOMER_OPTED_OUT = "CUSTOMER_OPTED_OUT"
    ALREADY_RECOVERED = "ALREADY_RECOVERED"
    UNKNOWN = "UNKNOWN"


def diagnose_event(
    event: RevenueEvent,
    customer: Customer,
    recovery_probability: float,
    previous_attempts_count: int = 0
) -> DiagnosisCategory:
    """
    Deterministic rule-based diagnosis for revenue events.
    Enforces clear priority order before optional LLM reasoning.
    """
    opt_out = getattr(customer, "opt_out", False) or False
    status = getattr(event, "status", "pending") or "pending"
    amount = getattr(event, "amount", 0) or 0
    failed_tx_count = getattr(customer, "failed_tx_count", 0) or 0
    days_overdue = getattr(event, "days_overdue", 0) or 0

    # Rule 1: Customer Opted Out
    if opt_out:
        return DiagnosisCategory.CUSTOMER_OPTED_OUT

    # Rule 2: Already Recovered or Stopped
    if status in ["recovered", "stopped"]:
        return DiagnosisCategory.ALREADY_RECOVERED

    # Rule 3: Very Low Recovery Probability
    if recovery_probability < 0.25:
        return DiagnosisCategory.LOW_RECOVERY_PROBABILITY

    # Rule 4: High Value Risk Threshold (≥ ₹1,00,000 / 10,000,000 paise)
    if amount >= 10000000:
        return DiagnosisCategory.HIGH_VALUE_RISK

    # Rule 5: Event-type specific diagnosis
    if event.event_type == "payment_failure":
        if previous_attempts_count > 0 or failed_tx_count > 3:
            return DiagnosisCategory.REPEATED_PAYMENT_FAILURE
        return DiagnosisCategory.TEMPORARY_PAYMENT_FAILURE

    elif event.event_type == "checkout_abandonment":
        return DiagnosisCategory.CHECKOUT_ABANDONMENT

    elif event.event_type == "subscription_failure":
        return DiagnosisCategory.SUBSCRIPTION_RENEWAL_FAILURE

    elif event.event_type == "overdue_invoice":
        return DiagnosisCategory.OVERDUE_RECEIVABLE

    return DiagnosisCategory.UNKNOWN
