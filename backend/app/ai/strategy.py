from enum import Enum


class RecoveryStrategy(str, Enum):
    SMART_RETRY = "SMART_RETRY"
    PAYMENT_REMINDER = "PAYMENT_REMINDER"
    PAYMENT_LINK = "PAYMENT_LINK"
    SUBSCRIPTION_RETRY = "SUBSCRIPTION_RETRY"
    ESCALATE = "ESCALATE"
    NO_ACTION = "NO_ACTION"


STRATEGY_DESCRIPTIONS = {
    RecoveryStrategy.SMART_RETRY: "Schedule automated background payment retry at peak bank authorization window.",
    RecoveryStrategy.PAYMENT_REMINDER: "Send friendly automated multi-channel reminder notification to customer.",
    RecoveryStrategy.PAYMENT_LINK: "Generate and send interactive Razorpay payment link via SMS/Email.",
    RecoveryStrategy.SUBSCRIPTION_RETRY: "Re-trigger subscription e-mandate auto-debit attempt.",
    RecoveryStrategy.ESCALATE: "Flag for priority manual review and merchant account management team intervention.",
    RecoveryStrategy.NO_ACTION: "Suppress intervention due to low recovery likelihood, customer opt-out, or policy threshold."
}
