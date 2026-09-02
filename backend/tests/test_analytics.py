import uuid
from datetime import datetime, timedelta, timezone
import pytest
from unittest.mock import patch, MagicMock

from app.models.merchant import Merchant
from app.models.customer import Customer
from app.models.revenue_event import RevenueEvent
from app.models.risk_assessment import RiskAssessment
from app.models.recovery_attempt import RecoveryAttempt
from app.models.audit_log import AuditLog
from app.ai.strategy import RecoveryStrategy
from app.services import analytics_service, recovery_service


def test_1_overview_metrics(client, db_session):
    m_id, c_id = str(uuid.uuid4()), str(uuid.uuid4())
    m = Merchant(id=m_id, name="M1", email="m1@test.com")
    c = Customer(id=c_id, merchant_id=m_id, name="C1", email="c1@test.com")
    e1 = RevenueEvent(id=str(uuid.uuid4()), merchant_id=m_id, customer_id=c_id, event_type="payment_failure", amount=100000, status="recovered")
    e2 = RevenueEvent(id=str(uuid.uuid4()), merchant_id=m_id, customer_id=c_id, event_type="checkout_abandonment", amount=200000, status="pending")
    db_session.add_all([m, c, e1, e2])
    db_session.commit()

    res = client.get(f"/api/v1/analytics/overview?merchant_id={m_id}")
    assert res.status_code == 200
    data = res.json()

    assert data["total_revenue_paise"] == 300000
    assert data["actual_recovered_paise"] == 100000
    assert data["total_events_count"] == 2
    assert "₹3,000.00" in data["total_revenue_formatted"]


def test_2_revenue_at_risk(client, db_session):
    m_id, c_id = str(uuid.uuid4()), str(uuid.uuid4())
    m = Merchant(id=m_id, name="M2", email="m2@test.com")
    c = Customer(id=c_id, merchant_id=m_id, name="C2", email="c2@test.com")
    e1 = RevenueEvent(id=str(uuid.uuid4()), merchant_id=m_id, customer_id=c_id, event_type="payment_failure", amount=500000, status="pending")
    e2 = RevenueEvent(id=str(uuid.uuid4()), merchant_id=m_id, customer_id=c_id, event_type="subscription_failure", amount=300000, status="recovered")
    db_session.add_all([m, c, e1, e2])
    db_session.commit()

    res = client.get(f"/api/v1/analytics/overview?merchant_id={m_id}")
    assert res.json()["revenue_at_risk_paise"] == 500000


def test_3_expected_recovery(db_session):
    m_id, c_id, e_id = str(uuid.uuid4()), str(uuid.uuid4()), str(uuid.uuid4())
    m = Merchant(id=m_id, name="M3", email="m3@test.com")
    c = Customer(id=c_id, merchant_id=m_id, name="C3", email="c3@test.com")
    e = RevenueEvent(id=e_id, merchant_id=m_id, customer_id=c_id, event_type="payment_failure", amount=1000000)  # ₹10,000
    r = RiskAssessment(id=str(uuid.uuid4()), revenue_event_id=e_id, risk_score=0.25, recovery_probability=0.75, risk_level="MEDIUM", revenue_at_risk_paise=1000000)
    db_session.add_all([m, c, e, r])
    db_session.commit()

    overview = analytics_service.get_overview_analytics(db_session, merchant_id=m_id)
    assert overview.expected_recovery_paise == 750000


def test_4_actual_recovery(client, db_session):
    m_id, c_id, e_id = str(uuid.uuid4()), str(uuid.uuid4()), str(uuid.uuid4())
    m = Merchant(id=m_id, name="M4", email="m4@test.com")
    c = Customer(id=c_id, merchant_id=m_id, name="C4", email="c4@test.com")
    e = RevenueEvent(id=e_id, merchant_id=m_id, customer_id=c_id, event_type="payment_failure", amount=400000, status="recovered")
    db_session.add_all([m, c, e])
    db_session.commit()

    res = client.get(f"/api/v1/analytics/overview?merchant_id={m_id}")
    assert res.json()["actual_recovered_paise"] == 400000


def test_5_recovery_rate_formula(db_session):
    m_id, c_id = str(uuid.uuid4()), str(uuid.uuid4())
    m = Merchant(id=m_id, name="M5", email="m5@test.com")
    c = Customer(id=c_id, merchant_id=m_id, name="C5", email="c5@test.com", successful_tx_count=5)
    e1 = RevenueEvent(id="rev_rate_1", merchant_id=m_id, customer_id=c_id, event_type="payment_failure", amount=100000)
    e2 = RevenueEvent(id="rev_rate_2", merchant_id=m_id, customer_id=c_id, event_type="payment_failure", amount=100000)
    db_session.add_all([m, c, e1, e2])
    db_session.commit()

    # Directly insert recovery attempt records for deterministic accounting
    # e1: SUCCESS (100k recovered), e2: FAILED (0 recovered)
    att1 = RecoveryAttempt(id=str(uuid.uuid4()), revenue_event_id="rev_rate_1", strategy="SMART_RETRY", status="SUCCESS", attempt_number=1)
    att2 = RecoveryAttempt(id=str(uuid.uuid4()), revenue_event_id="rev_rate_2", strategy="SMART_RETRY", status="FAILED", attempt_number=1)
    db_session.add_all([att1, att2])
    e1.status = "recovered"
    db_session.commit()

    ov = analytics_service.get_overview_analytics(db_session, merchant_id=m_id)
    # 100k recovered, 200k attempted -> 50.0%
    assert ov.recovery_rate_percent == 50.0


def test_6_strategy_analytics(client, db_session):
    m_id, c_id, e_id = str(uuid.uuid4()), str(uuid.uuid4()), str(uuid.uuid4())
    m = Merchant(id=m_id, name="M6", email="m6@test.com")
    c = Customer(id=c_id, merchant_id=m_id, name="C6", email="c6@test.com")
    e = RevenueEvent(id=e_id, merchant_id=m_id, customer_id=c_id, event_type="payment_failure", amount=150000)
    att = RecoveryAttempt(id=str(uuid.uuid4()), revenue_event_id=e_id, strategy="SMART_RETRY", status="SUCCESS", attempt_number=1)
    db_session.add_all([m, c, e, att])
    db_session.commit()

    res = client.get(f"/api/v1/analytics/strategies?merchant_id={m_id}")
    assert res.status_code == 200
    strats = res.json()["strategies"]
    smart = next(s for s in strats if s["strategy"] == "SMART_RETRY")
    assert smart["attempts_count"] == 1
    assert smart["successes_count"] == 1
    assert smart["amount_recovered_paise"] == 150000


def test_7_scenario_analytics(client, db_session):
    m_id, c_id = str(uuid.uuid4()), str(uuid.uuid4())
    m = Merchant(id=m_id, name="M7", email="m7@test.com")
    c = Customer(id=c_id, merchant_id=m_id, name="C7", email="c7@test.com")
    e1 = RevenueEvent(id=str(uuid.uuid4()), merchant_id=m_id, customer_id=c_id, event_type="payment_failure", amount=100000)
    e2 = RevenueEvent(id=str(uuid.uuid4()), merchant_id=m_id, customer_id=c_id, event_type="checkout_abandonment", amount=200000)
    db_session.add_all([m, c, e1, e2])
    db_session.commit()

    res = client.get(f"/api/v1/analytics/scenarios?merchant_id={m_id}")
    assert res.status_code == 200
    scenarios = res.json()["scenarios"]

    pf = next(s for s in scenarios if s["event_type"] == "payment_failure")
    ca = next(s for s in scenarios if s["event_type"] == "checkout_abandonment")
    assert pf["event_count"] == 1
    assert ca["event_count"] == 1


def test_8_policy_analytics_and_counts(db_session):
    m_id, c_id, e_id = str(uuid.uuid4()), str(uuid.uuid4()), str(uuid.uuid4())
    m = Merchant(id=m_id, name="M8", email="m8@test.com")
    c = Customer(id=c_id, merchant_id=m_id, name="C8", email="c8@test.com")
    e = RevenueEvent(id=e_id, merchant_id=m_id, customer_id=c_id, event_type="payment_failure", amount=100000)
    aud = AuditLog(id=str(uuid.uuid4()), revenue_event_id=e_id, action="POLICY_EVALUATED", actor="POLICY", policy_result="BLOCK")
    db_session.add_all([m, c, e, aud])
    db_session.commit()

    summary = analytics_service.get_audit_summary(db_session, merchant_id=m_id)
    assert summary.total_policy_evaluations == 1
    assert summary.total_blocks == 1


def test_9_recovery_analytics(db_session):
    m_id, c_id, e_id = str(uuid.uuid4()), str(uuid.uuid4()), str(uuid.uuid4())
    m = Merchant(id=m_id, name="M9", email="m9@test.com")
    c = Customer(id=c_id, merchant_id=m_id, name="C9", email="c9@test.com")
    e = RevenueEvent(id=e_id, merchant_id=m_id, customer_id=c_id, event_type="payment_failure", amount=100000)
    aud = AuditLog(id=str(uuid.uuid4()), revenue_event_id=e_id, action="RECOVERY_SUCCEEDED", actor="ENGINE", policy_result="SUCCESS", amount_recovered_paise=100000)
    db_session.add_all([m, c, e, aud])
    db_session.commit()

    summary = analytics_service.get_audit_summary(db_session, merchant_id=m_id)
    assert summary.total_successes == 1


def test_10_pipeline_counts(client, db_session):
    m_id, c_id, e_id = str(uuid.uuid4()), str(uuid.uuid4()), str(uuid.uuid4())
    m = Merchant(id=m_id, name="M10", email="m10@test.com")
    c = Customer(id=c_id, merchant_id=m_id, name="C10", email="c10@test.com")
    e = RevenueEvent(id=e_id, merchant_id=m_id, customer_id=c_id, event_type="payment_failure", amount=500000)
    db_session.add_all([m, c, e])
    db_session.commit()

    res = client.get(f"/api/v1/analytics/pipeline?merchant_id={m_id}")
    assert res.status_code == 200
    pipe = res.json()["pipeline"]
    det = next(p for p in pipe if p["stage"] == "DETECTED")
    assert det["count"] == 1
    assert det["amount_paise"] == 500000


def test_11_pipeline_monetary_values(client, db_session):
    m_id, c_id, e_id = str(uuid.uuid4()), str(uuid.uuid4()), str(uuid.uuid4())
    m = Merchant(id=m_id, name="M11", email="m11@test.com")
    c = Customer(id=c_id, merchant_id=m_id, name="C11", email="c11@test.com")
    e = RevenueEvent(id=e_id, merchant_id=m_id, customer_id=c_id, event_type="overdue_invoice", amount=1250000)
    db_session.add_all([m, c, e])
    db_session.commit()

    res = client.get(f"/api/v1/analytics/pipeline?merchant_id={m_id}")
    pipe = res.json()["pipeline"]
    det = next(p for p in pipe if p["stage"] == "DETECTED")
    assert "₹12,500.00" in det["amount_formatted"]


def test_12_timeseries_daily_aggregation(client, db_session):
    m_id, c_id = str(uuid.uuid4()), str(uuid.uuid4())
    m = Merchant(id=m_id, name="M12", email="m12@test.com")
    c = Customer(id=c_id, merchant_id=m_id, name="C12", email="c12@test.com")
    t1 = datetime(2026, 8, 28, 10, 0, tzinfo=timezone.utc)
    t2 = datetime(2026, 8, 29, 14, 0, tzinfo=timezone.utc)
    e1 = RevenueEvent(id=str(uuid.uuid4()), merchant_id=m_id, customer_id=c_id, event_type="payment_failure", amount=100000, event_time=t1)
    e2 = RevenueEvent(id=str(uuid.uuid4()), merchant_id=m_id, customer_id=c_id, event_type="payment_failure", amount=200000, event_time=t2)
    db_session.add_all([m, c, e1, e2])
    db_session.commit()

    res = client.get(f"/api/v1/analytics/timeseries?merchant_id={m_id}")
    assert res.status_code == 200
    ts = res.json()["timeseries"]
    assert len(ts) == 2
    assert ts[0]["date"] == "2026-08-28"
    assert ts[1]["date"] == "2026-08-29"


def test_13_opportunity_ranking(client, db_session):
    m_id, c_id = str(uuid.uuid4()), str(uuid.uuid4())
    m = Merchant(id=m_id, name="M13", email="m13@test.com")
    c = Customer(id=c_id, merchant_id=m_id, name="High Opp Cust", email="opp@test.com")
    e1 = RevenueEvent(id="rev_opp_small", merchant_id=m_id, customer_id=c_id, event_type="payment_failure", amount=50000)
    e2 = RevenueEvent(id="rev_opp_large", merchant_id=m_id, customer_id=c_id, event_type="payment_failure", amount=5000000)
    db_session.add_all([m, c, e1, e2])
    db_session.commit()

    res = client.get(f"/api/v1/analytics/opportunities?merchant_id={m_id}&limit=5")
    assert res.status_code == 200
    opps = res.json()
    assert len(opps) == 2
    # Highest expected recovery should come first
    assert opps[0]["revenue_event_id"] == "rev_opp_large"


def test_14_audit_summary(client, db_session):
    m_id, c_id, e_id = str(uuid.uuid4()), str(uuid.uuid4()), str(uuid.uuid4())
    m = Merchant(id=m_id, name="M14", email="m14@test.com")
    c = Customer(id=c_id, merchant_id=m_id, name="C14", email="c14@test.com")
    e = RevenueEvent(id=e_id, merchant_id=m_id, customer_id=c_id, event_type="payment_failure", amount=100000)
    aud = AuditLog(id=str(uuid.uuid4()), revenue_event_id=e_id, action="AGENT_RECOMMENDATION_GENERATED", actor="AGENT", policy_result="RECOMMENDATION — NOT EXECUTED")
    db_session.add_all([m, c, e, aud])
    db_session.commit()

    res = client.get(f"/api/v1/analytics/audit-summary?merchant_id={m_id}")
    assert res.status_code == 200
    data = res.json()
    assert data["total_recommendations"] == 1
    assert len(data["recent_logs"]) == 1


def test_15_date_filtering(client, db_session):
    m_id, c_id = str(uuid.uuid4()), str(uuid.uuid4())
    m = Merchant(id=m_id, name="M15", email="m15@test.com")
    c = Customer(id=c_id, merchant_id=m_id, name="C15", email="c15@test.com")
    t1 = datetime(2026, 8, 1, 12, 0, tzinfo=timezone.utc)
    t2 = datetime(2026, 8, 20, 12, 0, tzinfo=timezone.utc)
    e1 = RevenueEvent(id=str(uuid.uuid4()), merchant_id=m_id, customer_id=c_id, event_type="payment_failure", amount=100000, event_time=t1)
    e2 = RevenueEvent(id=str(uuid.uuid4()), merchant_id=m_id, customer_id=c_id, event_type="payment_failure", amount=200000, event_time=t2)
    db_session.add_all([m, c, e1, e2])
    db_session.commit()

    # Filter for mid-August date range
    res = client.get(f"/api/v1/analytics/overview?merchant_id={m_id}&start_date=2026-08-15T00:00:00Z&end_date=2026-08-25T23:59:59Z")
    assert res.status_code == 200
    data = res.json()
    assert data["total_events_count"] == 1
    assert data["total_revenue_paise"] == 200000


def test_16_merchant_isolation(client, db_session):
    m1_id, m2_id = str(uuid.uuid4()), str(uuid.uuid4())
    c1_id, c2_id = str(uuid.uuid4()), str(uuid.uuid4())

    m1 = Merchant(id=m1_id, name="Merchant 1", email="m1_iso@test.com")
    m2 = Merchant(id=m2_id, name="Merchant 2", email="m2_iso@test.com")
    c1 = Customer(id=c1_id, merchant_id=m1_id, name="C1", email="c1_iso@test.com")
    c2 = Customer(id=c2_id, merchant_id=m2_id, name="C2", email="c2_iso@test.com")

    e1 = RevenueEvent(id=str(uuid.uuid4()), merchant_id=m1_id, customer_id=c1_id, event_type="payment_failure", amount=100000)
    e2 = RevenueEvent(id=str(uuid.uuid4()), merchant_id=m2_id, customer_id=c2_id, event_type="payment_failure", amount=900000)
    db_session.add_all([m1, m2, c1, c2, e1, e2])
    db_session.commit()

    res1 = client.get(f"/api/v1/analytics/overview?merchant_id={m1_id}")
    res2 = client.get(f"/api/v1/analytics/overview?merchant_id={m2_id}")

    assert res1.json()["total_revenue_paise"] == 100000
    assert res2.json()["total_revenue_paise"] == 900000


def test_17_empty_dataset_handling(client):
    non_existent_merchant = str(uuid.uuid4())
    res = client.get(f"/api/v1/analytics/overview?merchant_id={non_existent_merchant}")
    assert res.status_code == 200
    data = res.json()
    assert data["total_revenue_paise"] == 0
    assert data["revenue_at_risk_paise"] == 0
    assert data["actual_recovered_paise"] == 0
    assert data["recovery_rate_percent"] == 0.0


def test_18_zero_attempt_strategy_handling(client):
    res = client.get("/api/v1/analytics/strategies")
    assert res.status_code == 200
    strats = res.json()["strategies"]
    assert len(strats) == len(RecoveryStrategy)
    for s in strats:
        assert s["success_rate_percent"] >= 0.0
