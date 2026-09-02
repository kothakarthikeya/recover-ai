"""
AI Recovery Agent module for RecoverAI.
Combines ML predictions, deterministic diagnosis, and LLM reasoning with a 100% reliable fallback engine.
Never executes payment actions directly.
"""

import os
import json
import httpx
from typing import Dict, Any, Optional, Tuple

from app.core.config import settings
from app.ai.strategy import RecoveryStrategy
from app.ai.diagnosis import DiagnosisCategory, diagnose_event
from app.ai.explanation import generate_business_explanation
from app.ai.prompts import SYSTEM_PROMPT, build_context_prompt
from app.models.revenue_event import RevenueEvent
from app.models.customer import Customer


class DeterministicFallbackEngine:
    """
    100% reliable rule-based fallback strategy engine.
    Ensures system never crashes if LLM credentials are missing or API fails.
    """
    @staticmethod
    def select_strategy(
        diagnosis: DiagnosisCategory,
        event: RevenueEvent,
        customer: Customer,
        recovery_prob: float
    ) -> Tuple[RecoveryStrategy, str, float, str]:
        # Rule 1: Customer Opted Out or Low Probability
        if diagnosis in [DiagnosisCategory.CUSTOMER_OPTED_OUT, DiagnosisCategory.ALREADY_RECOVERED, DiagnosisCategory.LOW_RECOVERY_PROBABILITY]:
            strategy = RecoveryStrategy.NO_ACTION
            confidence = 0.95
            next_step = "No action required. Event logged and suppressed per policy."

        # Rule 2: High Value Risk Threshold
        elif diagnosis == DiagnosisCategory.HIGH_VALUE_RISK:
            strategy = RecoveryStrategy.ESCALATE
            confidence = 0.90
            next_step = "Flagged for priority review by merchant manager."

        # Rule 3: Payment Failure
        elif event.event_type == "payment_failure":
            if recovery_prob >= 0.65 and customer.successful_tx_count >= 1:
                strategy = RecoveryStrategy.SMART_RETRY
                confidence = 0.85
                next_step = "Schedule automated Smart Retry at peak authorization window."
            elif recovery_prob >= 0.40:
                strategy = RecoveryStrategy.PAYMENT_LINK
                confidence = 0.80
                next_step = "Generate Razorpay Payment Link and send via SMS/Email."
            else:
                strategy = RecoveryStrategy.NO_ACTION
                confidence = 0.75
                next_step = "Suppress automatic retry due to moderate recovery probability."

        # Rule 4: Checkout Abandonment
        elif event.event_type == "checkout_abandonment":
            if event.amount >= 2000000:  # ≥ ₹20,000
                strategy = RecoveryStrategy.PAYMENT_LINK
                confidence = 0.85
                next_step = "Deliver personalized Razorpay Payment Link for high-value cart."
            else:
                strategy = RecoveryStrategy.PAYMENT_REMINDER
                confidence = 0.80
                next_step = "Send automated checkout recovery reminder notification."

        # Rule 5: Subscription Failure
        elif event.event_type == "subscription_failure":
            if recovery_prob >= 0.50:
                strategy = RecoveryStrategy.SUBSCRIPTION_RETRY
                confidence = 0.85
                next_step = "Re-trigger subscription e-mandate auto-debit attempt."
            else:
                strategy = RecoveryStrategy.PAYMENT_LINK
                confidence = 0.75
                next_step = "Send payment link to update recurring payment card details."

        # Rule 6: Overdue Invoice
        elif event.event_type == "overdue_invoice":
            if event.days_overdue > 60 or event.amount >= 5000000:
                strategy = RecoveryStrategy.ESCALATE
                confidence = 0.90
                next_step = "Escalate severely overdue/high-value invoice to accounts management."
            else:
                strategy = RecoveryStrategy.PAYMENT_REMINDER
                confidence = 0.85
                next_step = "Send formal B2B invoice payment reminder."

        else:
            strategy = RecoveryStrategy.NO_ACTION
            confidence = 0.70
            next_step = "No immediate automated intervention recommended."

        explanation = generate_business_explanation(
            diagnosis=diagnosis,
            strategy=strategy,
            event_type=event.event_type,
            amount_paise=event.amount,
            recovery_prob=recovery_prob,
            customer_name=customer.name,
            success_count=customer.successful_tx_count
        )

        return strategy, explanation, confidence, next_step


class AIRecoveryAgent:
    def __init__(self):
        self.agent_version = "v1.0.0"

    def recommend(
        self,
        event: RevenueEvent,
        customer: Customer,
        risk_data: Dict[str, Any],
        previous_attempts_count: int = 0
    ) -> Dict[str, Any]:
        """
        Main recommendation entry point.
        Combines deterministic diagnosis, optional LLM reasoning, and fallback engine.
        """
        recovery_prob = float(risk_data.get("recovery_probability", 0.5))
        risk_level = risk_data.get("risk_level", "MEDIUM")

        # 1. Deterministic Diagnosis
        diagnosis = diagnose_event(
            event=event,
            customer=customer,
            recovery_probability=recovery_prob,
            previous_attempts_count=previous_attempts_count
        )

        # 2. Check if LLM API key is available
        api_key = getattr(settings, "OPENAI_API_KEY", None) or os.getenv("OPENAI_API_KEY")
        use_llm = bool(api_key and api_key != "placeholder_key" and not api_key.startswith("placeholder"))

        strategy = None
        reasoning = None
        confidence = 0.85
        next_step = ""

        if use_llm:
            try:
                llm_res = self._call_llm_reasoning(event, customer, risk_data, api_key)
                if llm_res:
                    strategy_str = llm_res.get("recommended_strategy")
                    if strategy_str in RecoveryStrategy.__members__:
                        strategy = RecoveryStrategy(strategy_str)
                        reasoning = llm_res.get("reasoning")
                        confidence = float(llm_res.get("confidence", 0.85))
                        next_step = llm_res.get("next_step", "")
            except Exception as e:
                print(f"LLM Reasoning call failed: {e}. Falling back to deterministic engine.")
                strategy = None

        # 3. Fallback Engine if LLM not used or failed
        if strategy is None:
            strategy, reasoning, confidence, next_step = DeterministicFallbackEngine.select_strategy(
                diagnosis=diagnosis,
                event=event,
                customer=customer,
                recovery_prob=recovery_prob
            )

        # Calculate expected recovery in integer paise in Python (never in LLM)
        expected_recovery_paise = int(round(float(event.amount) * recovery_prob))

        return {
            "revenue_event_id": event.id,
            "diagnosis": diagnosis.value,
            "recommended_strategy": strategy,
            "reasoning": reasoning,
            "confidence": round(confidence, 2),
            "expected_recovery_amount_paise": expected_recovery_paise,
            "recovery_probability": recovery_prob,
            "risk_level": risk_level,
            "next_step": next_step,
            "agent_version": self.agent_version
        }

    def _call_llm_reasoning(
        self,
        event: RevenueEvent,
        customer: Customer,
        risk_data: Dict[str, Any],
        api_key: str
    ) -> Optional[Dict[str, Any]]:
        """Call OpenAI-compatible LLM endpoint using httpx with strict timeout."""
        event_dict = {
            "id": event.id,
            "event_type": event.event_type,
            "amount": event.amount,
            "failure_reason": event.failure_reason,
            "days_overdue": event.days_overdue,
            "status": event.status
        }
        cust_dict = {
            "name": customer.name,
            "successful_tx_count": customer.successful_tx_count,
            "failed_tx_count": customer.failed_tx_count,
            "opt_out": customer.opt_out
        }

        user_prompt = build_context_prompt(event_dict, cust_dict, risk_data)

        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        payload = {
            "model": settings.AI_MODEL_NAME,
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt}
            ],
            "response_format": {"type": "json_object"},
            "temperature": 0.2
        }

        with httpx.Client(timeout=10.0) as client:
            resp = client.post("https://api.openai.com/v1/chat/completions", headers=headers, json=payload)
            if resp.status_code == 200:
                content = resp.json()["choices"][0]["message"]["content"]
                return json.loads(content)
        return None


agent_instance = AIRecoveryAgent()
