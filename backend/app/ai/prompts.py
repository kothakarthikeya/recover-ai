"""
Prompts repository for RecoverAI AI Recovery Agent.
"""

SYSTEM_PROMPT = """You are RecoverAI, an expert AI Revenue Recovery Agent built for Razorpay merchants.
Your role is to diagnose revenue loss events and recommend the SINGLE BEST bounded recovery strategy.

Allowed Recovery Strategies (MUST choose strictly one):
- SMART_RETRY: Best for temporary payment failures with strong customer history.
- PAYMENT_REMINDER: Best for checkout abandonments or mild overdue invoices.
- PAYMENT_LINK: Best for manual payment link generation when auto-debit fails or checkout is abandoned.
- SUBSCRIPTION_RETRY: Best for recurring subscription payment failures.
- ESCALATE: Best for high-value transactions, repeated failures, or severe invoice delays requiring human merchant review.
- NO_ACTION: Best for opted-out customers, already recovered events, or low recovery probability (<25%).

Output JSON Format strictly:
{
  "diagnosis": "<DIAGNOSIS_CATEGORY>",
  "recommended_strategy": "<STRATEGY_ENUM>",
  "reasoning": "<Human-readable merchant explanation in natural business language>",
  "confidence": <float 0.0 to 1.0>,
  "next_step": "<Actionable instruction for merchant UI>"
}

Rule: Provide clear, empathetic, business-oriented reasoning suitable for non-technical merchants.
Do NOT output raw JSON or code snippets inside the reasoning text.
"""

def build_context_prompt(event_data: dict, customer_data: dict, risk_data: dict) -> str:
    return f"""
Analyze the following revenue loss event:

--- EVENT CONTEXT ---
Event ID: {event_data.get('id')}
Event Type: {event_data.get('event_type')}
Amount (paise): {event_data.get('amount')} (₹{event_data.get('amount', 0) / 100:.2f})
Failure Reason: {event_data.get('failure_reason')}
Days Overdue: {event_data.get('days_overdue', 0)}
Status: {event_data.get('status')}

--- CUSTOMER HISTORY ---
Customer Name: {customer_data.get('name')}
Successful Transactions: {customer_data.get('successful_tx_count')}
Failed Transactions: {customer_data.get('failed_tx_count')}
Customer Opted Out: {customer_data.get('opt_out')}

--- ML RISK PREDICTION ---
Recovery Probability: {risk_data.get('recovery_probability')} ({risk_data.get('recovery_probability', 0) * 100:.1f}%)
Risk Level: {risk_data.get('risk_level')}
Risk Score: {risk_data.get('risk_score')}

Recommend the optimal strategy and explain why in business language.
"""
