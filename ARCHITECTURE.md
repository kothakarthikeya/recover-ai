# RecoverAI Architecture Specification

## 1. System Overview

**RecoverAI** is an AI-powered revenue recovery agent built for the Razorpay AI Revenue Recovery Buildathon. It monitors financial events, detects revenue at risk across multiple payment failure scenarios, calculates recovery probability using Machine Learning, recommends optimal intervention strategies via an AI Reasoning Layer, validates actions through a deterministic Policy Guardrail Engine, executes bounded recovery workflows, and maintains an auditable timeline with batch metric tracking.

```
       +-------------------------------------------------------+
       |                  Revenue Event Source                 |
       |  (Payment Failure, Checkout Abandonment, Subscriptions, |
       |                   Overdue Invoices)                   |
       +---------------------------+---------------------------+
                                   |
                                   v
       +-------------------------------------------------------+
       |                  1. DETECT & DIAGNOSE                 |
       |  Risk Engine (ML Risk Scoring & Probability Model)    |
       +---------------------------+---------------------------+
                                   |
                                   v
       +-------------------------------------------------------+
       |                   2. AI DECISION                      |
       |  AI Agent Layer (Reasoning, Diagnosis, Recommendation)|
       +---------------------------+---------------------------+
                                   |
                                   v
       +-------------------------------------------------------+
       |                 3. POLICY GUARDRAIL                   |
       |  Deterministic Engine (Stopping Rules, Limits, Opt-out)|
       +---------------------------+---------------------------+
                                   |
                     +-------------+-------------+
                     |                           |
             ALLOW   v                           v   DENY / STOP / ESCALATE
       +------------------------+      +------------------------+
       |        4. ACT          |      |  No Action / Escalated  |
       | Recovery Engine (Razorpay|      |        Handling        |
       |  Test Mode Workflow)   |      +------------------------+
       +-----------+------------+
                   |
                   v
       +-------------------------------------------------------+
       |                 5. MEASURE & AUDIT                    |
       | Analytics Engine + Batch Measurement + Audit Trail    |
       +-------------------------------------------------------+
```

---

## 2. Core Operational Loop

1. **DETECT**: Ingest & identify revenue at risk across 4 key scenarios:
   - Payment Failure
   - Checkout Abandonment
   - Failed Subscription
   - Overdue B2B Receivable
2. **DIAGNOSE**: Extract customer & transaction features; compute recovery probability score via trained ML model (`backend/app/ml`).
3. **DECIDE**: AI Reasoning Engine (`backend/app/ai`) synthesizes context, failure cause, and probability to recommend a Strategy (`SMART_RETRY`, `PAYMENT_REMINDER`, `PAYMENT_LINK`, `SUBSCRIPTION_RETRY`, `ESCALATE`, `NO_ACTION`).
4. **GUARDRAIL**: Policy Engine (`backend/app/policies`) independently enforces deterministic rules (max retries, cutoff windows, min probability thresholds, high-value transaction escalation, opt-out checks).
5. **ACT**: Bounded Recovery Engine (`backend/app/services/recovery_service.py`) triggers automated workflow (e.g. Razorpay Test Mode API link generation or retry schedule).
6. **MEASURE**: Calculate dynamic batch recovery metrics (Revenue at Risk, Recoverable Revenue, Recovered Revenue, Recovery Rate %).
7. **AUDIT**: Append every state transition and policy decision to an immutable Audit Trail.

---

## 3. Data Architecture & Precision Rules

- **Currency Unit**: All monetary fields MUST be stored as **integer paise** (e.g., ₹1,000.00 = `100000` paise). Floating-point values for monetary amounts are strictly prohibited.
- **Storage Engine**: PostgreSQL (SQLAlchemy ORM + Alembic migrations). SQLite supported for lightweight local testing.

---

## 4. Recovery Execution Engine Architecture (Phase 8)

- **Provider Abstraction Interface**:
  - `BaseRecoveryProvider` abstract base class.
  - `SimulationRecoveryProvider`: Seeded pseudo-random draw hash comparison against ML `recovery_probability`.
  - `RazorpayTestProvider`: Test Mode Razorpay Payment Link and subscription retry implementation.
- **Strict Idempotency Guard**:
  - Prevents re-executing resolved or active recovery attempts.
  - Returns `Revenue has already been recovered` if already successful.
- **Attempt & Event Audit Records**:
  - `RecoveryAttempt`: Statuses (`PENDING`, `IN_PROGRESS`, `SUCCESS`, `FAILED`, `BLOCKED`, `STOPPED`, `ESCALATED`).
  - `RecoveryEvent`: Detailed state transitions (`recovery_success`, `recovery_failed`).
  - `AuditLog`: Action logs (`RECOVERY_STARTED`, `RECOVERY_SUCCEEDED`, `RECOVERY_FAILED`, `RECOVERY_BLOCKED`, `RECOVERY_ESCALATED`, `RECOVERY_STOPPED`).
- **Batch Recovery Metrics**:
  - Dynamically computes total revenue attempted, total revenue recovered, expected recovery, and recovery rate percentage.

---

## 5. Technology Stack

- **Frontend**: React + TypeScript + Vite + Tailwind CSS + shadcn/ui + Recharts
- **Backend**: Python + FastAPI + SQLAlchemy + Pydantic + Alembic
- **ML / AI**: XGBoost / scikit-learn + LLM Reasoning Layer
- **Payments**: Razorpay Test Mode APIs & Webhooks
