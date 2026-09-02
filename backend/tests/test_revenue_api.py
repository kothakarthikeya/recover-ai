import uuid
import pytest
from app.models.merchant import Merchant
from app.models.customer import Customer
from app.models.revenue_event import RevenueEvent


def test_empty_database_behavior(client):
    # Test overview on empty database
    res = client.get("/api/v1/revenue/overview")
    assert res.status_code == 200
    data = res.json()
    assert data["total_revenue_paise"] == 0
    assert data["revenue_at_risk_paise"] == 0
    assert data["total_events_count"] == 0
    assert data["total_customers_count"] == 0
    assert data["by_event_type"] == {}
    assert data["by_status"] == {}

    # Test list events on empty database
    res_events = client.get("/api/v1/revenue/events")
    assert res_events.status_code == 200
    list_data = res_events.json()
    assert list_data["items"] == []
    assert list_data["total"] == 0
    assert list_data["page"] == 1


def test_overview_calculation_and_paise_precision(client, db_session):
    merchant_id = str(uuid.uuid4())
    customer_id = str(uuid.uuid4())

    m = Merchant(id=merchant_id, name="Test M", email="tm@test.com")
    c = Customer(id=customer_id, merchant_id=merchant_id, name="Test C", email="tc@test.com")
    db_session.add_all([m, c])

    # Event 1: pending payment_failure ₹1,000 (100000 paise)
    e1 = RevenueEvent(
        id=str(uuid.uuid4()), merchant_id=merchant_id, customer_id=customer_id,
        event_type="payment_failure", amount=100000, status="pending"
    )
    # Event 2: recovered checkout_abandonment ₹2,500 (250000 paise)
    e2 = RevenueEvent(
        id=str(uuid.uuid4()), merchant_id=merchant_id, customer_id=customer_id,
        event_type="checkout_abandonment", amount=250000, status="recovered"
    )
    # Event 3: in_recovery subscription_failure ₹500 (50000 paise)
    e3 = RevenueEvent(
        id=str(uuid.uuid4()), merchant_id=merchant_id, customer_id=customer_id,
        event_type="subscription_failure", amount=50000, status="in_recovery"
    )
    db_session.add_all([e1, e2, e3])
    db_session.commit()

    res = client.get(f"/api/v1/revenue/overview?merchant_id={merchant_id}")
    assert res.status_code == 200
    data = res.json()
    
    assert data["total_revenue_paise"] == 400000  # 100000 + 250000 + 50000
    assert data["revenue_at_risk_paise"] == 150000  # pending (100000) + in_recovery (50000)
    assert data["total_events_count"] == 3
    assert data["total_customers_count"] == 1
    assert data["by_event_type"]["payment_failure"] == 1
    assert data["by_event_type"]["checkout_abandonment"] == 1
    assert data["by_event_type"]["subscription_failure"] == 1


def test_event_pagination_and_filtering(client, db_session):
    merchant_id = str(uuid.uuid4())
    customer_id = str(uuid.uuid4())

    m = Merchant(id=merchant_id, name="Test M2", email="tm2@test.com")
    c = Customer(id=customer_id, merchant_id=merchant_id, name="Test C2", email="tc2@test.com")
    db_session.add_all([m, c])

    for i in range(15):
        e = RevenueEvent(
            id=str(uuid.uuid4()),
            merchant_id=merchant_id,
            customer_id=customer_id,
            event_type="payment_failure" if i % 2 == 0 else "overdue_invoice",
            amount=(i + 1) * 100000,  # ₹1,000 to ₹15,000
            status="pending" if i < 10 else "recovered"
        )
        db_session.add(e)
    db_session.commit()

    # Pagination test
    res = client.get(f"/api/v1/revenue/events?merchant_id={merchant_id}&page=1&page_size=5")
    assert res.status_code == 200
    data = res.json()
    assert len(data["items"]) == 5
    assert data["total"] == 15
    assert data["total_pages"] == 3

    # Filtering by event_type
    res_type = client.get(f"/api/v1/revenue/events?merchant_id={merchant_id}&event_type=overdue_invoice")
    assert res_type.status_code == 200
    assert res_type.json()["total"] == 7

    # Filtering by status
    res_status = client.get(f"/api/v1/revenue/events?merchant_id={merchant_id}&status=recovered")
    assert res_status.status_code == 200
    assert res_status.json()["total"] == 5

    # Filtering by amount range (min=500000 paise, max=1000000 paise)
    res_amount = client.get(f"/api/v1/revenue/events?merchant_id={merchant_id}&min_amount=500000&max_amount=1000000")
    assert res_amount.status_code == 200
    assert res_amount.json()["total"] == 6


def test_event_detail_and_invalid_id(client, db_session):
    merchant_id = str(uuid.uuid4())
    customer_id = str(uuid.uuid4())
    event_id = str(uuid.uuid4())

    m = Merchant(id=merchant_id, name="Test M3", email="tm3@test.com")
    c = Customer(id=customer_id, merchant_id=merchant_id, name="Detail Customer", email="detail@test.com", total_spent_paise=900000)
    e = RevenueEvent(id=event_id, merchant_id=merchant_id, customer_id=customer_id, event_type="subscription_failure", amount=300000)
    db_session.add_all([m, c, e])
    db_session.commit()

    # Valid event detail
    res = client.get(f"/api/v1/revenue/events/{event_id}")
    assert res.status_code == 200
    data = res.json()
    assert data["id"] == event_id
    assert data["amount"] == 300000
    assert data["customer"]["name"] == "Detail Customer"

    # Invalid event ID
    res_404 = client.get(f"/api/v1/revenue/events/non_existent_id")
    assert res_404.status_code == 404
    assert "not found" in res_404.json()["detail"].lower()


def test_import_revenue_events_validation(client, db_session):
    merchant_id = str(uuid.uuid4())
    customer_id = str(uuid.uuid4())

    m = Merchant(id=merchant_id, name="Test M4", email="tm4@test.com")
    c = Customer(id=customer_id, merchant_id=merchant_id, name="Import Customer", email="import@test.com")
    db_session.add_all([m, c])
    db_session.commit()

    # Successful import payload
    valid_payload = {
        "merchant_id": merchant_id,
        "events": [
            {
                "customer_id": customer_id,
                "event_type": "payment_failure",
                "amount": 150000,
                "currency": "INR",
                "failure_reason": "card_declined"
            }
        ]
    }
    res_import = client.post("/api/v1/revenue/import", json=valid_payload)
    assert res_import.status_code == 201
    assert res_import.json()["imported_count"] == 1

    # Invalid event type validation (422)
    invalid_type_payload = {
        "merchant_id": merchant_id,
        "events": [
            {
                "customer_id": customer_id,
                "event_type": "invalid_event_type",
                "amount": 150000
            }
        ]
    }
    res_inv_type = client.post("/api/v1/revenue/import", json=invalid_type_payload)
    assert res_inv_type.status_code == 422

    # Invalid amount validation (negative or zero amount, 422)
    invalid_amount_payload = {
        "merchant_id": merchant_id,
        "events": [
            {
                "customer_id": customer_id,
                "event_type": "payment_failure",
                "amount": -500
            }
        ]
    }
    res_inv_amount = client.post("/api/v1/revenue/import", json=invalid_amount_payload)
    assert res_inv_amount.status_code == 422
