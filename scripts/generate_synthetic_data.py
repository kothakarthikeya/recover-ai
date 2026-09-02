#!/usr/bin/env python3
"""
Synthetic Revenue Event Generator for RecoverAI.
Generates realistic, reproducible synthetic revenue events and customer histories.
All data is explicitly marked as synthetic/demo data.
"""

import argparse
import json
import random
import uuid
from datetime import datetime, timedelta, timezone

EVENT_TYPES = [
    "payment_failure",
    "checkout_abandonment",
    "subscription_failure",
    "overdue_invoice"
]

EVENT_TYPE_DISTRIBUTION = [0.35, 0.30, 0.20, 0.15]

FAILURE_REASONS = {
    "payment_failure": [
        "insufficient_funds",
        "card_declined_by_issuer",
        "authentication_failed_3ds",
        "expired_card",
        "network_timeout"
    ],
    "checkout_abandonment": [
        "cart_abandoned_at_payment_step",
        "session_expired",
        "payment_window_closed_by_user",
        "bank_otp_not_received"
    ],
    "subscription_failure": [
        "recurring_mandate_failed",
        "card_expired_before_renewal",
        "auto_debit_limit_exceeded",
        "bank_account_frozen"
    ],
    "overdue_invoice": [
        "invoice_past_due_15_days",
        "invoice_past_due_30_days",
        "invoice_past_due_60_days",
        "payment_terms_exceeded"
    ]
}

FIRST_NAMES = ["Aarav", "Ananya", "Rohan", "Priya", "Vikram", "Sneha", "Kabir", "Neha", "Aditya", "Pooja", "Rahul", "Divya", "Karan", "Meera", "Siddharth", "Ishita"]
LAST_NAMES = ["Sharma", "Verma", "Patel", "Gupta", "Rao", "Nair", "Mehta", "Singh", "Joshi", "Kumar", "Chawla", "Deshmukh", "Reddy", "Iyer", "Banerjee", "Kapoor"]
DOMAINS = ["example.com", "demo-corp.in", "testmail.com", "sample-corp.co.in"]

# Monetary ranges in paise for each event type (₹500 to ₹2,50,000)
PAISE_RANGES = {
    "payment_failure": (50000, 5000000),         # ₹500 - ₹50,000
    "checkout_abandonment": (100000, 3000000),      # ₹1,000 - ₹30,000
    "subscription_failure": (99900, 999900),        # ₹999 - ₹9,999
    "overdue_invoice": (5000000, 25000000)          # ₹50,000 - ₹2,50,000
}


def generate_synthetic_dataset(count: int = 10000, seed: int = 42, customer_count: int = 1200):
    random.seed(seed)
    now = datetime.now(timezone.utc)

    # Demo Merchant
    merchant_id = f"mer_demo_{uuid.UUID(int=random.getrandbits(128)).hex[:12]}"
    merchant = {
        "id": merchant_id,
        "name": "Acme Retail & SaaS (Synthetic Demo)",
        "email": "demo-merchant@recoverai.test",
        "business_type": "SaaS & E-Commerce",
        "currency": "INR",
        "is_synthetic": True
    }

    # Generate synthetic customers with history
    customers = []
    for i in range(customer_count):
        cust_id = f"cust_syn_{uuid.UUID(int=random.getrandbits(128)).hex[:12]}"
        fname = random.choice(FIRST_NAMES)
        lname = random.choice(LAST_NAMES)
        domain = random.choice(DOMAINS)
        email = f"{fname.lower()}.{lname.lower()}{random.randint(10, 99)}@{domain}"
        phone = f"+9198{random.randint(10000000, 99999999)}"

        total_tx = random.randint(2, 25)
        success_tx = random.randint(1, total_tx)
        failed_tx = total_tx - success_tx
        avg_spend = random.randint(50000, 2000000)  # paise
        total_spent_paise = success_tx * avg_spend

        # 5% opt out rate
        opt_out = random.random() < 0.05

        customers.append({
            "id": cust_id,
            "merchant_id": merchant_id,
            "name": f"{fname} {lname}",
            "email": email,
            "phone": phone,
            "total_spent_paise": total_spent_paise,
            "successful_tx_count": success_tx,
            "failed_tx_count": failed_tx,
            "opt_out": opt_out,
            "is_synthetic": True
        })

    # Generate synthetic revenue events linked to customers
    revenue_events = []
    statuses = ["pending", "risk_assessed", "in_recovery", "recovered", "failed", "escalated", "stopped"]
    status_weights = [0.45, 0.15, 0.10, 0.15, 0.08, 0.04, 0.03]

    for i in range(count):
        event_id = f"rev_syn_{uuid.UUID(int=random.getrandbits(128)).hex[:12]}"
        customer = random.choice(customers)
        event_type = random.choices(EVENT_TYPES, weights=EVENT_TYPE_DISTRIBUTION)[0]
        
        min_p, max_p = PAISE_RANGES[event_type]
        amount = random.randint(min_p, max_p)
        failure_reason = random.choice(FAILURE_REASONS[event_type])
        status = random.choices(statuses, weights=status_weights)[0]

        days_overdue = 0
        if event_type == "overdue_invoice":
            days_overdue = random.randint(7, 90)
        elif event_type == "subscription_failure":
            days_overdue = random.randint(1, 14)
        elif event_type == "payment_failure":
            days_overdue = random.randint(0, 5)

        # 60% of events in recent 0-2 days (within 72h recovery window), 40% older events
        if random.random() < 0.60:
            event_days_ago = random.randint(0, 2)
        else:
            event_days_ago = random.randint(3, 60)

        event_time = (now - timedelta(days=event_days_ago, minutes=random.randint(0, 1440))).isoformat()

        revenue_events.append({
            "id": event_id,
            "merchant_id": merchant_id,
            "customer_id": customer["id"],
            "event_type": event_type,
            "amount": amount,
            "currency": "INR",
            "status": status,
            "failure_reason": failure_reason,
            "days_overdue": days_overdue,
            "transaction_count": customer["successful_tx_count"] + customer["failed_tx_count"],
            "successful_transaction_count": customer["successful_tx_count"],
            "event_time": event_time,
            "is_synthetic": True
        })

    return {
        "metadata": {
            "dataset_name": "RecoverAI Synthetic Revenue Dataset",
            "seed": seed,
            "generated_at": now.isoformat(),
            "total_events": len(revenue_events),
            "total_customers": len(customers),
            "notice": "DEMO / SYNTHETIC DATA ONLY. DOES NOT CONTAIN REAL RAZORPAY CUSTOMER DATA."
        },
        "merchant": merchant,
        "customers": customers,
        "revenue_events": revenue_events
    }


def main():
    parser = argparse.ArgumentParser(description="Generate synthetic revenue events for RecoverAI")
    parser.add_argument("--count", type=int, default=10000, help="Number of revenue events to generate")
    parser.add_argument("--customers", type=int, default=1200, help="Number of synthetic customers")
    parser.add_argument("--seed", type=int, default=42, help="Random seed for reproducibility")
    parser.add_argument("--output", type=str, default="scripts/synthetic_dataset.json", help="Output JSON path")
    args = parser.parse_args()

    print(f"Generating synthetic revenue dataset: {args.count} events, {args.customers} customers (Seed={args.seed})...")
    data = generate_synthetic_dataset(count=args.count, seed=args.seed, customer_count=args.customers)

    with open(args.output, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)

    print(f"Successfully generated dataset and saved to {args.output}")
    print(f"Summary: {data['metadata']['total_events']} events, {data['metadata']['total_customers']} customers.")


if __name__ == "__main__":
    main()
