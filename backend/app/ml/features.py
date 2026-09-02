"""
Feature engineering module for RecoverAI.
Extracts pre-action features from RevenueEvent and Customer history.
Strictly prevents target leakage by using only pre-intervention state.
"""

from datetime import datetime
from typing import Dict, Any, List
from app.models.revenue_event import RevenueEvent
from app.models.customer import Customer

EVENT_TYPE_MAP = {
    "payment_failure": 0,
    "checkout_abandonment": 1,
    "subscription_failure": 2,
    "overdue_invoice": 3
}

FAILURE_REASON_MAP = {
    "insufficient_funds": 0,
    "card_declined_by_issuer": 1,
    "authentication_failed_3ds": 2,
    "expired_card": 3,
    "network_timeout": 4,
    "cart_abandoned_at_payment_step": 5,
    "session_expired": 6,
    "payment_window_closed_by_user": 7,
    "bank_otp_not_received": 8,
    "recurring_mandate_failed": 9,
    "card_expired_before_renewal": 10,
    "auto_debit_limit_exceeded": 11,
    "bank_account_frozen": 12,
    "invoice_past_due_15_days": 13,
    "invoice_past_due_30_days": 14,
    "invoice_past_due_60_days": 15,
    "payment_terms_exceeded": 16,
    "other": 17
}


def extract_features(event: RevenueEvent, customer: Customer, previous_attempts_count: int = 0, previous_successful_count: int = 0) -> Dict[str, Any]:
    """
    Extract pre-action features for ML recovery model.
    """
    tx_count = customer.successful_tx_count + customer.failed_tx_count
    tx_count = max(tx_count, 1)

    customer_success_rate = float(customer.successful_tx_count) / float(tx_count)
    customer_failure_rate = float(customer.failed_tx_count) / float(tx_count)
    avg_tx_amount = float(customer.total_spent_paise) / float(max(customer.successful_tx_count, 1))

    is_first_transaction = 1 if customer.successful_tx_count == 0 else 0

    event_time = event.event_time or datetime.utcnow()
    hour_of_day = event_time.hour
    day_of_week = event_time.weekday()
    is_weekend = 1 if day_of_week in (5, 6) else 0

    # Encode event_type & failure_reason
    event_type_encoded = EVENT_TYPE_MAP.get(event.event_type, 0)
    reason_clean = event.failure_reason or "other"
    failure_reason_encoded = FAILURE_REASON_MAP.get(reason_clean, FAILURE_REASON_MAP["other"])

    features = {
        "amount": float(event.amount),
        "days_overdue": float(event.days_overdue),
        "event_type_encoded": event_type_encoded,
        "failure_reason_encoded": failure_reason_encoded,
        "is_first_transaction": is_first_transaction,
        "transaction_count": float(tx_count),
        "successful_transaction_count": float(customer.successful_tx_count),
        "failed_transaction_count": float(customer.failed_tx_count),
        "customer_success_rate": customer_success_rate,
        "customer_failure_rate": customer_failure_rate,
        "average_transaction_amount": avg_tx_amount,
        "previous_recovery_attempts": float(previous_attempts_count),
        "previous_successful_recoveries": float(previous_successful_count),
        "hour_of_day": float(hour_of_day),
        "day_of_week": float(day_of_week),
        "is_weekend": is_weekend,
        "opt_out": 1 if customer.opt_out else 0
    }
    return features


FEATURE_NAMES = [
    "amount",
    "days_overdue",
    "event_type_encoded",
    "failure_reason_encoded",
    "is_first_transaction",
    "transaction_count",
    "successful_transaction_count",
    "failed_transaction_count",
    "customer_success_rate",
    "customer_failure_rate",
    "average_transaction_amount",
    "previous_recovery_attempts",
    "previous_successful_recoveries",
    "hour_of_day",
    "day_of_week",
    "is_weekend",
    "opt_out"
]


def features_to_vector(features_dict: Dict[str, Any]) -> List[float]:
    """Convert features dictionary to ordered numerical vector for model input."""
    return [float(features_dict.get(name, 0.0)) for name in FEATURE_NAMES]
