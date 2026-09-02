from app.ai.strategy import RecoveryStrategy
from app.ai.diagnosis import DiagnosisCategory


def generate_business_explanation(
    diagnosis: DiagnosisCategory,
    strategy: RecoveryStrategy,
    event_type: str,
    amount_paise: int,
    recovery_prob: float,
    customer_name: str,
    success_count: int
) -> str:
    """
    Generate human-readable merchant explanation in natural business language.
    Avoids raw technical numbers or raw code symbols.
    """
    amount_rupees = f"₹{amount_paise / 100:,.2f}"
    pct = f"{recovery_prob * 100:.0f}%"

    if diagnosis == DiagnosisCategory.CUSTOMER_OPTED_OUT:
        return f"{customer_name} has previously opted out of recovery communications. Per compliance rules, no recovery action will be taken."

    if diagnosis == DiagnosisCategory.ALREADY_RECOVERED:
        return f"This transaction of {amount_rupees} has already been successfully recovered or resolved."

    if diagnosis == DiagnosisCategory.LOW_RECOVERY_PROBABILITY:
        return f"The estimated recovery likelihood is low ({pct}). Automatic recovery interventions have been suppressed to protect customer experience."

    if diagnosis == DiagnosisCategory.HIGH_VALUE_RISK:
        return f"This high-value transaction of {amount_rupees} presents a high risk. It has been escalated for priority manual review by your team."

    if strategy == RecoveryStrategy.SMART_RETRY:
        return (
            f"{customer_name} has a reliable payment history with {success_count} successful transactions. "
            f"The payment failure appears to be temporary, and a Smart Retry has a high likelihood ({pct}) of recovering {amount_rupees}."
        )

    if strategy == RecoveryStrategy.PAYMENT_LINK:
        return (
            f"An interactive Razorpay Payment Link for {amount_rupees} is recommended to allow {customer_name} "
            f"to complete the payment using an alternate payment method."
        )

    if strategy == RecoveryStrategy.PAYMENT_REMINDER:
        return (
            f"A polite multi-channel payment reminder for {amount_rupees} is recommended to prompt {customer_name} "
            f"to return and complete their purchase."
        )

    if strategy == RecoveryStrategy.SUBSCRIPTION_RETRY:
        return (
            f"The recurring subscription mandate for {customer_name} experienced a temporary processing error. "
            f"Scheduling a subscription auto-debit retry has a {pct} expected recovery rate."
        )

    if strategy == RecoveryStrategy.ESCALATE:
        return (
            f"Due to repeated failures or high-risk transaction context, this {amount_rupees} event is recommended "
            f"for manual review by your merchant operations team."
        )

    return f"RecoverAI recommends suppressing automatic action based on event characteristics and recovery probability ({pct})."
