import uuid
import pytest
from app.models.merchant import Merchant
from app.models.customer import Customer
from app.models.revenue_event import RevenueEvent
from app.models.risk_assessment import RiskAssessment
from app.models.recovery_attempt import RecoveryAttempt
from app.models.recovery_event import RecoveryEvent
from app.models.audit_log import AuditLog


def test_create_merchant_and_customer(db_session):
    merchant = Merchant(
        id=str(uuid.uuid4()),
        name="Test Merchant Pvt Ltd",
        email="merchant@example.com",
        business_type="SaaS"
    )
    db_session.add(merchant)
    db_session.commit()

    customer = Customer(
        id=str(uuid.uuid4()),
        merchant_id=merchant.id,
        name="John Doe",
        email="john@example.com",
        total_spent_paise=5000000,  # ₹50,000 in paise
        successful_tx_count=5
    )
    db_session.add(customer)
    db_session.commit()

    saved_customer = db_session.query(Customer).filter_by(id=customer.id).first()
    assert saved_customer is not None
    assert saved_customer.merchant_id == merchant.id
    assert saved_customer.total_spent_paise == 5000000
    assert saved_customer.merchant.name == "Test Merchant Pvt Ltd"


def test_revenue_event_and_paise_precision(db_session):
    merchant_id = str(uuid.uuid4())
    customer_id = str(uuid.uuid4())

    merchant = Merchant(id=merchant_id, name="Test Merchant", email="testm@example.com")
    customer = Customer(id=customer_id, merchant_id=merchant_id, name="Jane Smith", email="jane@example.com")
    db_session.add_all([merchant, customer])
    db_session.commit()

    # Create revenue event with integer paise
    amount_in_paise = 1500000  # ₹15,000.00
    revenue_event = RevenueEvent(
        id=str(uuid.uuid4()),
        merchant_id=merchant_id,
        customer_id=customer_id,
        event_type="payment_failure",
        amount=amount_in_paise,
        failure_reason="insufficient_funds",
        status="pending"
    )
    db_session.add(revenue_event)
    db_session.commit()

    saved_event = db_session.query(RevenueEvent).filter_by(id=revenue_event.id).first()
    assert saved_event is not None
    assert saved_event.amount == 1500000
    assert isinstance(saved_event.amount, int)
    assert saved_event.event_type == "payment_failure"


def test_risk_assessment_and_audit_log(db_session):
    merchant_id = str(uuid.uuid4())
    customer_id = str(uuid.uuid4())
    event_id = str(uuid.uuid4())

    merchant = Merchant(id=merchant_id, name="Merchant M", email="m@example.com")
    customer = Customer(id=customer_id, merchant_id=merchant_id, name="Cust C", email="c@example.com")
    event = RevenueEvent(
        id=event_id,
        merchant_id=merchant_id,
        customer_id=customer_id,
        event_type="subscription_failure",
        amount=299900  # ₹2,999
    )
    db_session.add_all([merchant, customer, event])
    db_session.commit()

    risk = RiskAssessment(
        id=str(uuid.uuid4()),
        revenue_event_id=event_id,
        risk_score=0.25,
        recovery_probability=0.75,
        risk_level="MEDIUM",
        revenue_at_risk_paise=299900
    )
    db_session.add(risk)

    audit = AuditLog(
        id=str(uuid.uuid4()),
        revenue_event_id=event_id,
        action="RISK_EVALUATED",
        actor="SYSTEM_AGENT",
        policy_result="ALLOWED",
        details="Risk score evaluated successfully"
    )
    db_session.add(audit)
    db_session.commit()

    saved_risk = db_session.query(RiskAssessment).filter_by(revenue_event_id=event_id).first()
    saved_audit = db_session.query(AuditLog).filter_by(revenue_event_id=event_id).first()

    assert saved_risk.recovery_probability == 0.75
    assert saved_audit.policy_result == "ALLOWED"


def test_cascade_delete_merchant(db_session):
    merchant_id = str(uuid.uuid4())
    merchant = Merchant(id=merchant_id, name="Cascade Merchant", email="cascade@example.com")
    customer = Customer(id=str(uuid.uuid4()), merchant_id=merchant_id, name="Cust", email="cust@example.com")
    db_session.add_all([merchant, customer])
    db_session.commit()

    event = RevenueEvent(
        id=str(uuid.uuid4()),
        merchant_id=merchant_id,
        customer_id=customer.id,
        event_type="checkout_abandonment",
        amount=50000
    )
    db_session.add(event)
    db_session.commit()

    db_session.delete(merchant)
    db_session.commit()

    assert db_session.query(Customer).filter_by(merchant_id=merchant_id).count() == 0
    assert db_session.query(RevenueEvent).filter_by(merchant_id=merchant_id).count() == 0
