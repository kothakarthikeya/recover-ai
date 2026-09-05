import os
import json
from datetime import datetime
from sqlalchemy.orm import Session
from app.models.merchant import Merchant
from app.models.customer import Customer
from app.models.revenue_event import RevenueEvent


def ensure_demo_data_seeded(db: Session):
    """
    Safely seeds synthetic demo dataset if DB is empty.
    Ensures deployed demo environment has active opportunities and metrics ready out-of-the-box.
    """
    try:
        print("Demo data check started")
        event_count = db.query(RevenueEvent).count()
        if event_count > 0:
            print(f"Existing demo data found: {event_count} events")
            return

        possible_paths = [
            os.path.abspath("scripts/synthetic_dataset.json"),
            os.path.abspath("../scripts/synthetic_dataset.json"),
            os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))), "scripts", "synthetic_dataset.json"),
            "/app/scripts/synthetic_dataset.json",
        ]

        json_path = None
        for p in possible_paths:
            if os.path.exists(p):
                json_path = p
                break

        if not json_path:
            print("Demo data check error: scripts/synthetic_dataset.json not found.")
            return

        print(f"Auto-seeding synthetic demo data from {json_path}...")
        with open(json_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        merchant_data = data["merchant"]
        customers_data = data["customers"]
        events_data = data["revenue_events"]

        # Insert Merchant
        if not db.query(Merchant).filter_by(id=merchant_data["id"]).first():
            db.add(Merchant(
                id=merchant_data["id"],
                name=merchant_data["name"],
                email=merchant_data["email"],
                business_type=merchant_data.get("business_type", "SaaS"),
                currency=merchant_data.get("currency", "INR")
            ))
            db.commit()

        # Insert Customers
        existing_cust_ids = set(c.id for c in db.query(Customer.id).filter_by(merchant_id=merchant_data["id"]).all())
        new_customers = [
            Customer(
                id=c["id"],
                merchant_id=c["merchant_id"],
                name=c["name"],
                email=c["email"],
                phone=c.get("phone"),
                total_spent_paise=c["total_spent_paise"],
                successful_tx_count=c["successful_tx_count"],
                failed_tx_count=c["failed_tx_count"],
                opt_out=c.get("opt_out", False)
            ) for c in customers_data if c["id"] not in existing_cust_ids
        ]
        if new_customers:
            db.bulk_save_objects(new_customers)
            db.commit()

        # Insert Events
        existing_event_ids = set(e.id for e in db.query(RevenueEvent.id).filter_by(merchant_id=merchant_data["id"]).all())
        new_events = [
            RevenueEvent(
                id=e["id"],
                merchant_id=e["merchant_id"],
                customer_id=e["customer_id"],
                event_type=e["event_type"],
                amount=e["amount"],
                currency=e.get("currency", "INR"),
                status=e.get("status", "pending"),
                failure_reason=e.get("failure_reason"),
                days_overdue=e.get("days_overdue", 0),
                transaction_count=e.get("transaction_count", 1),
                successful_transaction_count=e.get("successful_transaction_count", 0),
                event_time=datetime.fromisoformat(e["event_time"]) if "event_time" in e else datetime.utcnow()
            ) for e in events_data if e["id"] not in existing_event_ids
        ]
        if new_events:
            chunk_size = 2000
            for i in range(0, len(new_events), chunk_size):
                db.bulk_save_objects(new_events[i:i + chunk_size])
                db.commit()

        print(f"Seeded {len(new_events)} synthetic revenue events")
    except Exception as err:
        db.rollback()
        print(f"Demo data check error: {err}")
