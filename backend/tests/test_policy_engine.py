import uuid
from datetime import datetime, timedelta, timezone
import pytest
from app.models.merchant import Merchant
from app.models.customer import Customer
from app.models.revenue_event import RevenueEvent
from app.models.recovery_attempt import RecoveryAttempt
from app.models.audit_log import AuditLog
from app.ai.strategy import RecoveryStrategy
from app.schemas.policy import PolicyDecisionEnum, RuleIdEnum
from app.policies.guardrails import PolicyConfig
from app.policies.stopping_rules import evaluate_stopping_rules
from app.services import policy_service


def test_1_normal_eligible_event_allow(db_session):
    m_id, c_id, e_id = str(uuid.uuid4()), str(uuid.uuid4()), str(uuid.uuid4())
    m = Merchant(id=m_id, name="M1", email="m1@test.com")
    c = Customer(id=c_id, merchant_id=m_id, name="C1", email="c1@test.com", successful_tx_count=3)
    e = RevenueEvent(id=e_id, merchant_id=m_id, customer_id=c_id, event_type="payment_failure", amount=250000)
    db_session.add_all([m, c, e])
    db_session.commit()

    dec, rule, reason, req = evaluate_stopping_rules(e, c, recovery_probability=0.75, recommended_strategy=RecoveryStrategy.SMART_RETRY)
    assert dec == PolicyDecisionEnum.ALLOW
    assert rule == RuleIdEnum.STANDARD_ELIGIBILITY


def test_2_customer_opt_out_no_action(db_session):
    c = Customer(id="c2", merchant_id="m2", name="C2", email="c2@test.com", opt_out=True)
    e = RevenueEvent(id="e2", merchant_id="m2", customer_id="c2", event_type="payment_failure", amount=100000)

    dec, rule, reason, req = evaluate_stopping_rules(e, c, recovery_probability=0.80, recommended_strategy=RecoveryStrategy.SMART_RETRY)
    assert dec == PolicyDecisionEnum.NO_ACTION
    assert rule == RuleIdEnum.CUSTOMER_OPT_OUT


def test_3_already_recovered_no_action():
    c = Customer(id="c3", merchant_id="m3", name="C3", email="c3@test.com")
    e = RevenueEvent(id="e3", merchant_id="m3", customer_id="c3", event_type="payment_failure", amount=100000, status="recovered")

    dec, rule, reason, req = evaluate_stopping_rules(e, c, recovery_probability=0.90, recommended_strategy=RecoveryStrategy.SMART_RETRY)
    assert dec == PolicyDecisionEnum.NO_ACTION
    assert rule == RuleIdEnum.ALREADY_RECOVERED


def test_4_low_recovery_probability_no_action():
    c = Customer(id="c4", merchant_id="m4", name="C4", email="c4@test.com")
    e = RevenueEvent(id="e4", merchant_id="m4", customer_id="c4", event_type="payment_failure", amount=100000)

    dec, rule, reason, req = evaluate_stopping_rules(e, c, recovery_probability=0.15, recommended_strategy=RecoveryStrategy.SMART_RETRY)
    assert dec == PolicyDecisionEnum.NO_ACTION
    assert rule == RuleIdEnum.LOW_RECOVERY_PROBABILITY


def test_5_maximum_attempts_block():
    c = Customer(id="c5", merchant_id="m5", name="C5", email="c5@test.com")
    e = RevenueEvent(id="e5", merchant_id="m5", customer_id="c5", event_type="payment_failure", amount=100000)

    dec, rule, reason, req = evaluate_stopping_rules(e, c, recovery_probability=0.80, recommended_strategy=RecoveryStrategy.SMART_RETRY, previous_attempts_count=2)
    assert dec == PolicyDecisionEnum.BLOCK
    assert rule == RuleIdEnum.MAX_ATTEMPTS_EXCEEDED


def test_6_high_value_transaction_escalate():
    c = Customer(id="c6", merchant_id="m6", name="C6", email="c6@test.com")
    e = RevenueEvent(id="e6", merchant_id="m6", customer_id="c6", event_type="payment_failure", amount=10000000)  # ₹1,00,000

    dec, rule, reason, req = evaluate_stopping_rules(e, c, recovery_probability=0.80, recommended_strategy=RecoveryStrategy.SMART_RETRY)
    assert dec == PolicyDecisionEnum.ESCALATE
    assert rule == RuleIdEnum.HIGH_VALUE_TRANSACTION
    assert req is True


def test_7_expired_recovery_window_block():
    c = Customer(id="c7", merchant_id="m7", name="C7", email="c7@test.com")
    old_time = datetime.now(timezone.utc) - timedelta(hours=80)
    e = RevenueEvent(id="e7", merchant_id="m7", customer_id="c7", event_type="payment_failure", amount=100000, event_time=old_time)

    dec, rule, reason, req = evaluate_stopping_rules(e, c, recovery_probability=0.80, recommended_strategy=RecoveryStrategy.SMART_RETRY)
    assert dec == PolicyDecisionEnum.BLOCK
    assert rule == RuleIdEnum.RECOVERY_WINDOW_EXPIRED


def test_8_strategy_event_mismatch_block():
    c = Customer(id="c8", merchant_id="m8", name="C8", email="c8@test.com")
    # Payment failure does not allow PAYMENT_REMINDER (only checkout_abandonment/overdue_invoice allow reminder)
    e = RevenueEvent(id="e8", merchant_id="m8", customer_id="c8", event_type="payment_failure", amount=100000)

    dec, rule, reason, req = evaluate_stopping_rules(e, c, recovery_probability=0.80, recommended_strategy=RecoveryStrategy.PAYMENT_REMINDER)
    assert dec == PolicyDecisionEnum.BLOCK
    assert rule == RuleIdEnum.STRATEGY_INCOMPATIBLE


def test_9_incompatible_strategy_checkout_abandonment():
    c = Customer(id="c9", merchant_id="m9", name="C9", email="c9@test.com")
    # checkout_abandonment does not allow SMART_RETRY
    e = RevenueEvent(id="e9", merchant_id="m9", customer_id="c9", event_type="checkout_abandonment", amount=100000)

    dec, rule, reason, req = evaluate_stopping_rules(e, c, recovery_probability=0.80, recommended_strategy=RecoveryStrategy.SMART_RETRY)
    assert dec == PolicyDecisionEnum.BLOCK
    assert rule == RuleIdEnum.STRATEGY_INCOMPATIBLE


def test_10_high_value_plus_invalid_strategy_escalate():
    c = Customer(id="c10", merchant_id="m10", name="C10", email="c10@test.com")
    e = RevenueEvent(id="e10", merchant_id="m10", customer_id="c10", event_type="payment_failure", amount=15000000)

    # Rule 6 (High value escalation) takes priority over Rule 7 (Strategy compatibility)
    dec, rule, reason, req = evaluate_stopping_rules(e, c, recovery_probability=0.80, recommended_strategy=RecoveryStrategy.PAYMENT_REMINDER)
    assert dec == PolicyDecisionEnum.ESCALATE
    assert rule == RuleIdEnum.HIGH_VALUE_TRANSACTION


def test_11_opt_out_plus_high_value_no_action():
    c = Customer(id="c11", merchant_id="m11", name="C11", email="c11@test.com", opt_out=True)
    e = RevenueEvent(id="e11", merchant_id="m11", customer_id="c11", event_type="payment_failure", amount=20000000)

    # Rule 2 (Opt-out) takes priority over Rule 6 (High-value)
    dec, rule, reason, req = evaluate_stopping_rules(e, c, recovery_probability=0.80, recommended_strategy=RecoveryStrategy.SMART_RETRY)
    assert dec == PolicyDecisionEnum.NO_ACTION
    assert rule == RuleIdEnum.CUSTOMER_OPT_OUT


def test_12_already_recovered_plus_high_value_no_action():
    c = Customer(id="c12", merchant_id="m12", name="C12", email="c12@test.com")
    e = RevenueEvent(id="e12", merchant_id="m12", customer_id="c12", event_type="payment_failure", amount=20000000, status="recovered")

    # Rule 1 (Already recovered) takes priority over Rule 6 (High-value)
    dec, rule, reason, req = evaluate_stopping_rules(e, c, recovery_probability=0.90, recommended_strategy=RecoveryStrategy.SMART_RETRY)
    assert dec == PolicyDecisionEnum.NO_ACTION
    assert rule == RuleIdEnum.ALREADY_RECOVERED


def test_13_policy_audit_creation(client, db_session):
    m_id, c_id, e_id = str(uuid.uuid4()), str(uuid.uuid4()), str(uuid.uuid4())
    m = Merchant(id=m_id, name="M13", email="m13@test.com")
    c = Customer(id=c_id, merchant_id=m_id, name="C13", email="c13@test.com")
    e = RevenueEvent(id=e_id, merchant_id=m_id, customer_id=c_id, event_type="payment_failure", amount=300000)
    db_session.add_all([m, c, e])
    db_session.commit()

    res = client.post(f"/api/v1/policy/evaluate/{e_id}")
    assert res.status_code == 200
    data = res.json()

    assert data["decision"] == "ALLOW"
    assert data["rule_id"] == "STANDARD_ELIGIBILITY"

    audit = db_session.query(AuditLog).filter_by(revenue_event_id=e_id, action="POLICY_EVALUATED").first()
    assert audit is not None
    assert audit.policy_result == "ALLOW"


def test_14_deterministic_evaluation():
    c = Customer(id="c14", merchant_id="m14", name="C14", email="c14@test.com")
    e = RevenueEvent(id="e14", merchant_id="m14", customer_id="c14", event_type="payment_failure", amount=500000)

    res1 = evaluate_stopping_rules(e, c, 0.70, RecoveryStrategy.SMART_RETRY)
    res2 = evaluate_stopping_rules(e, c, 0.70, RecoveryStrategy.SMART_RETRY)

    assert res1 == res2


def test_15_custom_policy_configuration():
    c = Customer(id="c15", merchant_id="m15", name="C15", email="c15@test.com")
    e = RevenueEvent(id="e15", merchant_id="m15", customer_id="c15", event_type="payment_failure", amount=500000)  # ₹5,000

    # Custom strict policy config with ₹4,000 threshold
    custom_cfg = PolicyConfig(high_value_threshold_paise=400000)

    dec, rule, reason, req = evaluate_stopping_rules(e, c, 0.80, RecoveryStrategy.SMART_RETRY, config=custom_cfg)
    assert dec == PolicyDecisionEnum.ESCALATE
    assert rule == RuleIdEnum.HIGH_VALUE_TRANSACTION


def test_16_missing_risk_assessment_handling(client, db_session):
    m_id, c_id, e_id = str(uuid.uuid4()), str(uuid.uuid4()), str(uuid.uuid4())
    m = Merchant(id=m_id, name="M16", email="m16@test.com")
    c = Customer(id=c_id, merchant_id=m_id, name="C16", email="c16@test.com")
    e = RevenueEvent(id=e_id, merchant_id=m_id, customer_id=c_id, event_type="checkout_abandonment", amount=150000)
    db_session.add_all([m, c, e])
    db_session.commit()

    # Evaluating policy automatically generates risk assessment if not present
    res = client.post(f"/api/v1/policy/evaluate/{e_id}")
    assert res.status_code == 200
    assert res.json()["decision"] == "ALLOW"


def test_17_missing_agent_recommendation_handling(client, db_session):
    m_id, c_id, e_id = str(uuid.uuid4()), str(uuid.uuid4()), str(uuid.uuid4())
    m = Merchant(id=m_id, name="M17", email="m17@test.com")
    c = Customer(id=c_id, merchant_id=m_id, name="C17", email="c17@test.com")
    e = RevenueEvent(id=e_id, merchant_id=m_id, customer_id=c_id, event_type="subscription_failure", amount=299900)
    db_session.add_all([m, c, e])
    db_session.commit()

    # Evaluating policy automatically generates agent recommendation if not present
    res = client.post(f"/api/v1/policy/evaluate/{e_id}")
    assert res.status_code == 200
    assert res.json()["decision"] == "ALLOW"


def test_18_invalid_event_id(client):
    res = client.post("/api/v1/policy/evaluate/non_existent_event_id")
    assert res.status_code == 404
    assert "not found" in res.json()["detail"].lower()
