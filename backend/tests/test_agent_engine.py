import uuid
import pytest
from unittest.mock import patch
from app.models.merchant import Merchant
from app.models.customer import Customer
from app.models.revenue_event import RevenueEvent
from app.models.audit_log import AuditLog
from app.ai.strategy import RecoveryStrategy
from app.ai.diagnosis import DiagnosisCategory, diagnose_event
from app.ai.agent import agent_instance, DeterministicFallbackEngine
from app.services import agent_service


def test_1_payment_failure_diagnosis(db_session):
    m_id, c_id, e_id = str(uuid.uuid4()), str(uuid.uuid4()), str(uuid.uuid4())
    m = Merchant(id=m_id, name="M1", email="m1@test.com")
    c = Customer(id=c_id, merchant_id=m_id, name="C1", email="c1@test.com", successful_tx_count=3)
    e = RevenueEvent(id=e_id, merchant_id=m_id, customer_id=c_id, event_type="payment_failure", amount=100000)

    diag = diagnose_event(e, c, recovery_probability=0.80)
    assert diag == DiagnosisCategory.TEMPORARY_PAYMENT_FAILURE


def test_2_checkout_abandonment_diagnosis():
    c = Customer(id="c2", merchant_id="m2", name="C2", email="c2@test.com")
    e = RevenueEvent(id="e2", merchant_id="m2", customer_id="c2", event_type="checkout_abandonment", amount=200000)

    diag = diagnose_event(e, c, recovery_probability=0.70)
    assert diag == DiagnosisCategory.CHECKOUT_ABANDONMENT


def test_3_subscription_failure_diagnosis():
    c = Customer(id="c3", merchant_id="m3", name="C3", email="c3@test.com")
    e = RevenueEvent(id="e3", merchant_id="m3", customer_id="c3", event_type="subscription_failure", amount=99900)

    diag = diagnose_event(e, c, recovery_probability=0.60)
    assert diag == DiagnosisCategory.SUBSCRIPTION_RENEWAL_FAILURE


def test_4_overdue_invoice_diagnosis():
    c = Customer(id="c4", merchant_id="m4", name="C4", email="c4@test.com")
    e = RevenueEvent(id="e4", merchant_id="m4", customer_id="c4", event_type="overdue_invoice", amount=1500000, days_overdue=30)

    diag = diagnose_event(e, c, recovery_probability=0.50)
    assert diag == DiagnosisCategory.OVERDUE_RECEIVABLE


def test_5_opt_out_to_no_action():
    c = Customer(id="c5", merchant_id="m5", name="C5", email="c5@test.com", opt_out=True)
    e = RevenueEvent(id="e5", merchant_id="m5", customer_id="c5", event_type="payment_failure", amount=500000)

    diag = diagnose_event(e, c, recovery_probability=0.85)
    assert diag == DiagnosisCategory.CUSTOMER_OPTED_OUT

    strat, exp, conf, next_s = DeterministicFallbackEngine.select_strategy(diag, e, c, 0.85)
    assert strat == RecoveryStrategy.NO_ACTION


def test_6_already_recovered_to_no_action():
    c = Customer(id="c6", merchant_id="m6", name="C6", email="c6@test.com")
    e = RevenueEvent(id="e6", merchant_id="m6", customer_id="c6", event_type="payment_failure", amount=300000, status="recovered")

    diag = diagnose_event(e, c, recovery_probability=0.90)
    assert diag == DiagnosisCategory.ALREADY_RECOVERED

    strat, exp, conf, next_s = DeterministicFallbackEngine.select_strategy(diag, e, c, 0.90)
    assert strat == RecoveryStrategy.NO_ACTION


def test_7_low_recovery_probability_to_no_action():
    c = Customer(id="c7", merchant_id="m7", name="C7", email="c7@test.com")
    e = RevenueEvent(id="e7", merchant_id="m7", customer_id="c7", event_type="payment_failure", amount=200000)

    diag = diagnose_event(e, c, recovery_probability=0.15)
    assert diag == DiagnosisCategory.LOW_RECOVERY_PROBABILITY

    strat, exp, conf, next_s = DeterministicFallbackEngine.select_strategy(diag, e, c, 0.15)
    assert strat == RecoveryStrategy.NO_ACTION


def test_8_strategy_enum_validation():
    valid_strategies = set(RecoveryStrategy.__members__.values())
    assert RecoveryStrategy.SMART_RETRY in valid_strategies
    assert RecoveryStrategy.PAYMENT_REMINDER in valid_strategies
    assert RecoveryStrategy.PAYMENT_LINK in valid_strategies
    assert RecoveryStrategy.SUBSCRIPTION_RETRY in valid_strategies
    assert RecoveryStrategy.ESCALATE in valid_strategies
    assert RecoveryStrategy.NO_ACTION in valid_strategies


def test_9_expected_recovery_calculation_integer_paise():
    c = Customer(id="c9", merchant_id="m9", name="C9", email="c9@test.com", successful_tx_count=2)
    e = RevenueEvent(id="e9", merchant_id="m9", customer_id="c9", event_type="payment_failure", amount=1234567)  # ₹12,345.67

    rec = agent_instance.recommend(e, c, {"recovery_probability": 0.75, "risk_level": "MEDIUM"})
    exp_paise = rec["expected_recovery_amount_paise"]

    assert isinstance(exp_paise, int)
    assert exp_paise == int(round(1234567 * 0.75))


def test_10_agent_recommendation_generation(db_session):
    m_id, c_id, e_id = str(uuid.uuid4()), str(uuid.uuid4()), str(uuid.uuid4())
    m = Merchant(id=m_id, name="M10", email="m10@test.com")
    c = Customer(id=c_id, merchant_id=m_id, name="C10", email="c10@test.com", successful_tx_count=4)
    e = RevenueEvent(id=e_id, merchant_id=m_id, customer_id=c_id, event_type="payment_failure", amount=400000)
    db_session.add_all([m, c, e])
    db_session.commit()

    rec = agent_service.analyze_and_recommend(db_session, e_id)

    assert rec["revenue_event_id"] == e_id
    assert isinstance(rec["recommended_strategy"], RecoveryStrategy)
    assert len(rec["reasoning"]) > 10
    assert 0.0 <= rec["confidence"] <= 1.0


def test_11_deterministic_fallback_without_llm():
    c = Customer(id="c11", merchant_id="m11", name="C11", email="c11@test.com", successful_tx_count=5)
    e = RevenueEvent(id="e11", merchant_id="m11", customer_id="c11", event_type="payment_failure", amount=500000)

    # Ensure OPENAI_API_KEY is not set or placeholder
    with patch("app.ai.agent.settings.OPENAI_API_KEY", "placeholder_key"):
        rec = agent_instance.recommend(e, c, {"recovery_probability": 0.80, "risk_level": "LOW"})
        assert rec["recommended_strategy"] == RecoveryStrategy.SMART_RETRY
        assert "Smart Retry" in rec["reasoning"] or "reliable payment history" in rec["reasoning"]


def test_12_missing_llm_credentials_fallback(client, db_session):
    m_id, c_id, e_id = str(uuid.uuid4()), str(uuid.uuid4()), str(uuid.uuid4())
    m = Merchant(id=m_id, name="M12", email="m12@test.com")
    c = Customer(id=c_id, merchant_id=m_id, name="C12", email="c12@test.com")
    e = RevenueEvent(id=e_id, merchant_id=m_id, customer_id=c_id, event_type="checkout_abandonment", amount=150000)
    db_session.add_all([m, c, e])
    db_session.commit()

    res = client.post(f"/api/v1/agent/analyze/{e_id}")
    assert res.status_code == 200
    data = res.json()

    assert data["recommended_strategy"] == "PAYMENT_REMINDER"
    assert "reasoning" in data


def test_13_invalid_llm_output_recovery(db_session):
    c = Customer(id="c13", merchant_id="m13", name="C13", email="c13@test.com")
    e = RevenueEvent(id="e13", merchant_id="m13", customer_id="c13", event_type="subscription_failure", amount=299900)

    # Mock _call_llm_reasoning returning invalid JSON or invalid strategy
    with patch.object(agent_instance, "_call_llm_reasoning", return_value={"recommended_strategy": "INVALID_ACTION"}):
        with patch("app.ai.agent.settings.OPENAI_API_KEY", "valid_fake_key"):
            rec = agent_instance.recommend(e, c, {"recovery_probability": 0.70, "risk_level": "LOW"})
            # Should recover cleanly via fallback engine to SUBSCRIPTION_RETRY
            assert rec["recommended_strategy"] == RecoveryStrategy.SUBSCRIPTION_RETRY


def test_14_audit_log_creation_not_executed(db_session):
    m_id, c_id, e_id = str(uuid.uuid4()), str(uuid.uuid4()), str(uuid.uuid4())
    m = Merchant(id=m_id, name="M14", email="m14@test.com")
    c = Customer(id=c_id, merchant_id=m_id, name="C14", email="c14@test.com")
    e = RevenueEvent(id=e_id, merchant_id=m_id, customer_id=c_id, event_type="overdue_invoice", amount=1000000)
    db_session.add_all([m, c, e])
    db_session.commit()

    agent_service.analyze_and_recommend(db_session, e_id)

    audit = db_session.query(AuditLog).filter_by(revenue_event_id=e_id, action="AGENT_RECOMMENDATION_GENERATED").first()
    assert audit is not None
    assert audit.actor == "AI_RECOVERY_AGENT"
    assert audit.policy_result == "RECOMMENDATION — NOT EXECUTED"


def test_15_invalid_event_id(client):
    res = client.post("/api/v1/agent/analyze/non_existent_event_id")
    assert res.status_code == 404
    assert "not found" in res.json()["detail"].lower()
