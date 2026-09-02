from typing import Dict, Set
from app.ai.strategy import RecoveryStrategy

EVENT_STRATEGY_COMPATIBILITY_MATRIX: Dict[str, Set[RecoveryStrategy]] = {
    "payment_failure": {
        RecoveryStrategy.SMART_RETRY,
        RecoveryStrategy.PAYMENT_LINK,
        RecoveryStrategy.ESCALATE,
        RecoveryStrategy.NO_ACTION
    },
    "checkout_abandonment": {
        RecoveryStrategy.PAYMENT_REMINDER,
        RecoveryStrategy.PAYMENT_LINK,
        RecoveryStrategy.ESCALATE,
        RecoveryStrategy.NO_ACTION
    },
    "subscription_failure": {
        RecoveryStrategy.SUBSCRIPTION_RETRY,
        RecoveryStrategy.PAYMENT_LINK,
        RecoveryStrategy.ESCALATE,
        RecoveryStrategy.NO_ACTION
    },
    "overdue_invoice": {
        RecoveryStrategy.PAYMENT_REMINDER,
        RecoveryStrategy.PAYMENT_LINK,
        RecoveryStrategy.ESCALATE,
        RecoveryStrategy.NO_ACTION
    }
}


def is_strategy_compatible(event_type: str, strategy: RecoveryStrategy) -> bool:
    """Validate whether the strategy is allowed for the given revenue event type."""
    allowed = EVENT_STRATEGY_COMPATIBILITY_MATRIX.get(event_type, {RecoveryStrategy.NO_ACTION, RecoveryStrategy.ESCALATE})
    return strategy in allowed
