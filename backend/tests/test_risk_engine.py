import uuid
import pytest
from app.models.merchant import Merchant
from app.models.customer import Customer
from app.models.revenue_event import RevenueEvent
from app.models.risk_assessment import RiskAssessment
from app.models.audit_log import AuditLog
from app.ml.features import extract_features, features_to_vector, FEATURE_NAMES
from app.ml.predictor import predictor, RecoveryPredictor
from app.ml.train import train_model


def test_1_feature_generation():
    m_id = str(uuid.uuid4())
    c_id = str(uuid.uuid4())
    e_id = str(uuid.uuid4())

    customer = Customer(
        id=c_id, merchant_id=m_id, name="Test Cust", email="cust@test.com",
        total_spent_paise=1000000, successful_tx_count=4, failed_tx_count=1, opt_out=False
    )
    event = RevenueEvent(
        id=e_id, merchant_id=m_id, customer_id=c_id, event_type="payment_failure",
        amount=250000, failure_reason="insufficient_funds", days_overdue=2
    )

    feat_dict = extract_features(event, customer, previous_attempts_count=1, previous_successful_count=0)

    assert "amount" in feat_dict
    assert feat_dict["amount"] == 250000.0
    assert feat_dict["days_overdue"] == 2.0
    assert feat_dict["customer_success_rate"] == 0.8  # 4 / (4+1)
    assert feat_dict["is_first_transaction"] == 0
    assert len(features_to_vector(feat_dict)) == len(FEATURE_NAMES)


def test_2_no_target_leakage():
    # Verify that target/outcome variables are NOT in feature names
    leakage_keys = ["recovered", "amount_recovered", "final_outcome", "post_status"]
    for lk in leakage_keys:
        assert lk not in FEATURE_NAMES


def test_3_model_training_and_artifact_creation(tmp_path):
    # Test model training routine
    artifact_dir = str(tmp_path / "artifacts")
    metrics = train_model(dataset_path="scripts/synthetic_dataset.json", artifact_dir=artifact_dir)

    assert "roc_auc" in metrics
    assert 0.0 <= metrics["roc_auc"] <= 1.0
    assert metrics["train_samples"] > 0
    assert metrics["test_samples"] > 0


def test_4_probability_output_between_0_and_1(db_session):
    m_id = str(uuid.uuid4())
    c_id = str(uuid.uuid4())
    e_id = str(uuid.uuid4())

    m = Merchant(id=m_id, name="M", email="m@test.com")
    c = Customer(id=c_id, merchant_id=m_id, name="C", email="c@test.com", successful_tx_count=2, failed_tx_count=1)
    e = RevenueEvent(id=e_id, merchant_id=m_id, customer_id=c_id, event_type="subscription_failure", amount=199900)
    db_session.add_all([m, c, e])
    db_session.commit()

    res = predictor.predict_event(e, c)
    prob = res["recovery_probability"]

    assert 0.0 <= prob <= 1.0
    assert 0.0 <= res["risk_score"] <= 1.0
    assert res["risk_score"] == round(1.0 - prob, 4)


def test_5_expected_recovery_calculation(db_session):
    m_id = str(uuid.uuid4())
    c_id = str(uuid.uuid4())
    e_id = str(uuid.uuid4())

    m = Merchant(id=m_id, name="M5", email="m5@test.com")
    c = Customer(id=c_id, merchant_id=m_id, name="C5", email="c5@test.com")
    e = RevenueEvent(id=e_id, merchant_id=m_id, customer_id=c_id, event_type="overdue_invoice", amount=1000000)  # ₹10,000
    db_session.add_all([m, c, e])
    db_session.commit()

    res = predictor.predict_event(e, c)
    expected_paise = res["expected_recovery_amount"]

    assert isinstance(expected_paise, int)
    assert 0 <= expected_paise <= 1000000
    assert expected_paise == int(round(1000000 * res["recovery_probability"]))


def test_6_risk_level_thresholds():
    assert RecoveryPredictor.determine_risk_level(0.10) == "CRITICAL"
    assert RecoveryPredictor.determine_risk_level(0.24) == "CRITICAL"
    assert RecoveryPredictor.determine_risk_level(0.25) == "HIGH"
    assert RecoveryPredictor.determine_risk_level(0.49) == "HIGH"
    assert RecoveryPredictor.determine_risk_level(0.50) == "MEDIUM"
    assert RecoveryPredictor.determine_risk_level(0.74) == "MEDIUM"
    assert RecoveryPredictor.determine_risk_level(0.75) == "LOW"
    assert RecoveryPredictor.determine_risk_level(0.95) == "LOW"


def test_7_single_event_risk_api(client, db_session):
    m_id = str(uuid.uuid4())
    c_id = str(uuid.uuid4())
    e_id = str(uuid.uuid4())

    m = Merchant(id=m_id, name="M7", email="m7@test.com")
    c = Customer(id=c_id, merchant_id=m_id, name="C7", email="c7@test.com")
    e = RevenueEvent(id=e_id, merchant_id=m_id, customer_id=c_id, event_type="payment_failure", amount=500000)
    db_session.add_all([m, c, e])
    db_session.commit()

    res = client.post(f"/api/v1/risk/analyze/{e_id}")
    assert res.status_code == 200
    data = res.json()

    assert data["revenue_event_id"] == e_id
    assert "recovery_probability" in data
    assert "risk_score" in data
    assert data["risk_level"] in ["LOW", "MEDIUM", "HIGH", "CRITICAL"]
    assert data["revenue_at_risk_paise"] == 500000
    assert data["model_version"] == "v1.0.0"


def test_8_batch_risk_api(client, db_session):
    m_id = str(uuid.uuid4())
    c_id = str(uuid.uuid4())
    e1_id = str(uuid.uuid4())
    e2_id = str(uuid.uuid4())

    m = Merchant(id=m_id, name="M8", email="m8@test.com")
    c = Customer(id=c_id, merchant_id=m_id, name="C8", email="c8@test.com")
    e1 = RevenueEvent(id=e1_id, merchant_id=m_id, customer_id=c_id, event_type="payment_failure", amount=100000)
    e2 = RevenueEvent(id=e2_id, merchant_id=m_id, customer_id=c_id, event_type="checkout_abandonment", amount=200000)
    db_session.add_all([m, c, e1, e2])
    db_session.commit()

    res = client.post("/api/v1/risk/analyze-batch", json={"event_ids": [e1_id, e2_id]})
    assert res.status_code == 200
    data = res.json()

    assert data["events_analyzed"] == 2
    assert data["total_revenue_at_risk_paise"] == 300000
    assert len(data["assessments"]) == 2
    assert "LOW" in data["risk_level_counts"]


def test_9_persistence_of_risk_assessment(client, db_session):
    m_id = str(uuid.uuid4())
    c_id = str(uuid.uuid4())
    e_id = str(uuid.uuid4())

    m = Merchant(id=m_id, name="M9", email="m9@test.com")
    c = Customer(id=c_id, merchant_id=m_id, name="C9", email="c9@test.com")
    e = RevenueEvent(id=e_id, merchant_id=m_id, customer_id=c_id, event_type="subscription_failure", amount=150000)
    db_session.add_all([m, c, e])
    db_session.commit()

    client.post(f"/api/v1/risk/analyze/{e_id}")

    saved = db_session.query(RiskAssessment).filter_by(revenue_event_id=e_id).first()
    assert saved is not None
    assert saved.revenue_at_risk_paise == 150000
    assert saved.model_version == "v1.0.0"


def test_10_audit_log_creation(client, db_session):
    m_id = str(uuid.uuid4())
    c_id = str(uuid.uuid4())
    e_id = str(uuid.uuid4())

    m = Merchant(id=m_id, name="M10", email="m10@test.com")
    c = Customer(id=c_id, merchant_id=m_id, name="C10", email="c10@test.com")
    e = RevenueEvent(id=e_id, merchant_id=m_id, customer_id=c_id, event_type="overdue_invoice", amount=800000)
    db_session.add_all([m, c, e])
    db_session.commit()

    client.post(f"/api/v1/risk/analyze/{e_id}")

    audit = db_session.query(AuditLog).filter_by(revenue_event_id=e_id, action="RISK_ANALYZED").first()
    assert audit is not None
    assert audit.actor == "ML_PREDICTION_ENGINE"
    assert audit.policy_result == "COMPLETED"


def test_11_invalid_event_id(client):
    res = client.post("/api/v1/risk/analyze/non_existent_event_id")
    assert res.status_code == 404
    assert "not found" in res.json()["detail"].lower()


def test_12_empty_batch(client):
    res = client.post("/api/v1/risk/analyze-batch", json={"event_ids": []})
    assert res.status_code == 200
    data = res.json()

    assert data["events_analyzed"] == 0
    assert data["total_revenue_at_risk_paise"] == 0
    assert data["estimated_recoverable_revenue_paise"] == 0
    assert data["assessments"] == []


def test_13_deterministic_prediction_with_fixed_inputs(db_session):
    m_id = str(uuid.uuid4())
    c_id = str(uuid.uuid4())
    e_id = str(uuid.uuid4())

    m = Merchant(id=m_id, name="M13", email="m13@test.com")
    c = Customer(id=c_id, merchant_id=m_id, name="C13", email="c13@test.com", successful_tx_count=5, failed_tx_count=1)
    e = RevenueEvent(id=e_id, merchant_id=m_id, customer_id=c_id, event_type="payment_failure", amount=300000, days_overdue=1)
    db_session.add_all([m, c, e])
    db_session.commit()

    res1 = predictor.predict_event(e, c)
    res2 = predictor.predict_event(e, c)

    assert res1["recovery_probability"] == res2["recovery_probability"]
    assert res1["risk_score"] == res2["risk_score"]
    assert res1["expected_recovery_amount"] == res2["expected_recovery_amount"]
