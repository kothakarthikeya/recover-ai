#!/usr/bin/env python3
"""
Database Seeder for RecoverAI.
Imports generated synthetic revenue events into the database safely and idempotently.
"""

import argparse
import json
import os
import sys
from datetime import datetime

# Add backend directory to sys.path
sys.path.insert(0, os.path.realpath(os.path.join(os.path.dirname(__file__), "..", "backend")))

from app.db.session import SessionLocal
from app.models.merchant import Merchant
from app.models.customer import Customer
from app.models.revenue_event import RevenueEvent
from app.models.risk_assessment import RiskAssessment
from app.models.recovery_attempt import RecoveryAttempt
from app.models.recovery_event import RecoveryEvent
from app.models.audit_log import AuditLog


def seed_database(json_filepath: str, reset: bool = False):
    if not os.path.exists(json_filepath):
        print(f"Error: Synthetic dataset file not found at {json_filepath}")
        print("Please run `python scripts/generate_synthetic_data.py` first.")
        sys.exit(1)

    print(f"Reading dataset from {json_filepath}...")
    with open(json_filepath, "r", encoding="utf-8") as f:
        data = json.load(f)

    db = SessionLocal()
    try:
        if reset:
            print("Reset flag active: Clearing existing demo database tables...")
            db.query(RecoveryEvent).delete()
            db.query(RecoveryAttempt).delete()
            db.query(AuditLog).delete()
            db.query(RiskAssessment).delete()
            db.query(RevenueEvent).delete()
            db.query(Customer).delete()
            db.query(Merchant).delete()
            db.commit()
            print("Existing tables cleared.")

        merchant_data = data["merchant"]
        customers_data = data["customers"]
        events_data = data["revenue_events"]

        # 1. Upsert Merchant
        existing_merchant = db.query(Merchant).filter_by(id=merchant_data["id"]).first()
        if not existing_merchant:
            merchant = Merchant(
                id=merchant_data["id"],
                name=merchant_data["name"],
                email=merchant_data["email"],
                business_type=merchant_data.get("business_type", "SaaS"),
                currency=merchant_data.get("currency", "INR")
            )
            db.add(merchant)
            db.commit()
            print(f"Inserted merchant: {merchant.name} ({merchant.id})")
        else:
            print(f"Merchant already exists: {existing_merchant.name} ({existing_merchant.id})")

        # 2. Insert Customers (in batches)
        existing_cust_ids = set(c.id for c in db.query(Customer.id).filter_by(merchant_id=merchant_data["id"]).all())
        new_customers = []
        for c in customers_data:
            if c["id"] not in existing_cust_ids:
                new_customers.append(Customer(
                    id=c["id"],
                    merchant_id=c["merchant_id"],
                    name=c["name"],
                    email=c["email"],
                    phone=c.get("phone"),
                    total_spent_paise=c["total_spent_paise"],
                    successful_tx_count=c["successful_tx_count"],
                    failed_tx_count=c["failed_tx_count"],
                    opt_out=c.get("opt_out", False)
                ))

        if new_customers:
            db.bulk_save_objects(new_customers)
            db.commit()
            print(f"Inserted {len(new_customers)} synthetic customers.")
        else:
            print(f"All {len(customers_data)} synthetic customers already exist.")

        # 3. Insert Revenue Events (in batches)
        existing_event_ids = set(e.id for e in db.query(RevenueEvent.id).filter_by(merchant_id=merchant_data["id"]).all())
        new_events = []
        for e in events_data:
            if e["id"] not in existing_event_ids:
                event_time_dt = datetime.fromisoformat(e["event_time"]) if "event_time" in e else datetime.utcnow()
                new_events.append(RevenueEvent(
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
                    event_time=event_time_dt
                ))

        if new_events:
            chunk_size = 2000
            for i in range(0, len(new_events), chunk_size):
                chunk = new_events[i:i + chunk_size]
                db.bulk_save_objects(chunk)
                db.commit()
            print(f"Inserted {len(new_events)} synthetic revenue events.")
        else:
            print(f"All {len(events_data)} synthetic revenue events already exist.")

        print("\n--- Seeding Completed Successfully ---")
        print(f"Total Merchants: {db.query(Merchant).count()}")
        print(f"Total Customers: {db.query(Customer).count()}")
        print(f"Total Revenue Events: {db.query(RevenueEvent).count()}")

    except Exception as err:
        db.rollback()
        print(f"Seeding failed: {err}")
        sys.exit(1)
    finally:
        db.close()


def main():
    parser = argparse.ArgumentParser(description="Seed database with synthetic revenue data")
    parser.add_argument("--file", type=str, default="scripts/synthetic_dataset.json", help="Path to synthetic dataset JSON file")
    parser.add_argument("--reset", action="store_true", help="Clear existing DB records before seeding fresh dataset")
    args = parser.parse_args()
    seed_database(args.file, reset=args.reset)


if __name__ == "__main__":
    main()
