# RecoverAI — AI Revenue Recovery Agent

> **Tagline**: Detect. Decide. Recover.

RecoverAI is an autonomous, policy-guarded revenue recovery agent built for the Razorpay AI Revenue Recovery Buildathon. It detects revenue slipping away from payment failures, checkout abandonments, failed subscriptions, and overdue B2B receivables, applies machine learning and AI reasoning to diagnose causes and recommend intervention strategies, and executes bounded recovery workflows with a strict deterministic policy engine and full audit trail.

---

## Key Features

- **Full End-to-End Recovery Loop**: Ingests events, diagnoses root cause, assesses risk score & recovery probability, selects optimal strategy, enforces safety policies, executes recovery actions, and measures money recovered.
- **4 Revenue Scenarios**: Payment Failure, Checkout Abandonment, Subscription Failure, Overdue B2B Receivable.
- **Deterministic Policy Engine**: Enforces authoritative safety guardrails (max retry attempts, cutoff windows, min probability thresholds, high-value transaction escalation, customer opt-outs). LLMs and clients can NEVER override policy decisions.
- **Bounded Recovery Execution Engine (Phase 8)**: Provider-abstracted execution engine supporting Seeded Simulation & Razorpay Test Mode with strict idempotency and policy authorization.
- **Analytics & Merchant Intelligence Layer (Phase 9)**: SQL-aggregated KPI metrics, 7-stage pipeline funnel, strategy/scenario breakdowns, daily time-series, top opportunity ranking, and merchant-isolated audit summaries — all dynamically calculated, never hard-coded.
- **Integer Paise Money Architecture**: All monetary figures are stored as integer paise (e.g. ₹1,000 = `100000` paise) preventing floating-point rounding errors.
- **ML Revenue Risk Engine (Phase 5)**: XGBoost-based predictor estimating recovery probability and expected recovery amount without target leakage.
- **AI Recovery Agent (Phase 6)**: Reasoning & diagnosis layer producing structured strategy recommendations and human-readable merchant explanations.
- **Dynamic Batch Metrics**: Calculates real-time recovery metrics (Total Revenue, Revenue at Risk, Recoverable Revenue, Recovered Revenue, Recovery Rate %) directly from DB transactions.

---

## Closed Strategy Catalog

- `SMART_RETRY` — Automated retry scheduled at optimal customer authorization window.
- `PAYMENT_REMINDER` — Multi-channel notification sent to customer.
- `PAYMENT_LINK` — Custom Razorpay Payment Link generated and delivered.
- `SUBSCRIPTION_RETRY` — Subscription payment re-attempt workflow.
- `ESCALATE` — Flagged for manual merchant intervention (high-value or complex).
- `NO_ACTION` — Suppressed due to low probability, opt-out, or policy cutoff.

---

## Bounded Recovery Execution Engine Architecture (Phase 8)

> [!IMPORTANT]
> **Simulation Disclaimer**: The current demo uses synthetic data and a deterministic simulation provider. It does not execute real-money transactions.

### Core Operational Principles
1. **Server-Side Policy Recheck**: Execution is permitted ONLY when the server-side Policy Engine returns `ALLOW`.
2. **Strict Idempotency**: Pre-checks DB state to prevent duplicate recoveries on resolved transactions.
3. **Provider Abstraction**:
   - `SimulationRecoveryProvider`: Reproducible pseudo-random seed draw compared against ML `recovery_probability`.
   - `RazorpayTestProvider`: Simulates Razorpay Test Mode Payment Link generation & e-mandate retry calls.
4. **Controlled Attempt Statuses**: `PENDING`, `IN_PROGRESS`, `SUCCESS`, `FAILED`, `BLOCKED`, `STOPPED`, `ESCALATED`.
5. **Expected vs. Actual Recovery**:
   - **Expected Recovery**: Sum of ML-predicted expected recovery amounts.
   - **Actual Recovery**: Sum of successfully recovered transaction amounts in integer paise.
   - $\text{Recovery Rate \%} = \frac{\text{Total Successfully Recovered Revenue}}{\text{Total Revenue Attempted}} \times 100$

---

## Setup & Execution Guide

### 1. Requirements
- Python 3.10+
- virtualenv
- PostgreSQL (or SQLite for local development)

### 2. Python Environment Setup
```bash
cd backend
python -m venv venv

# Windows (PowerShell / CMD):
.\venv\Scripts\activate

# macOS / Linux:
source venv/bin/activate

pip install -r requirements.txt
cp .env.example .env
```

### 3. Database Migration & Setup
```bash
cd backend
python -m alembic upgrade head
```

### 4. Generate Synthetic Revenue Dataset (Phase 3)
```bash
python scripts/generate_synthetic_data.py --count 10000 --seed 42 --output scripts/synthetic_dataset.json
```

### 5. Seed Database
```bash
python scripts/seed_database.py --file scripts/synthetic_dataset.json
```

### 6. Train Machine Learning Model (Phase 5)
```bash
cd backend
python -m app.ml.train
```

### 7. Run FastAPI Server
```bash
cd backend
uvicorn app.main:app --reload --port 8000
```
- **Swagger Documentation**: [http://localhost:8000/docs](http://localhost:8000/docs)
- **ReDoc Documentation**: [http://localhost:8000/redoc](http://localhost:8000/redoc)

### 8. Run Full Test Suite (81 Test Cases)
```bash
python -m pytest backend/tests
```

---

## Implemented API Endpoints (Phases 1–8)

### Health
- `GET /health` — Service & database health status.

### Revenue APIs
- `GET /api/v1/revenue/overview` — Calculated aggregate revenue, revenue at risk, event type and status breakdowns.
- `GET /api/v1/revenue/events` — Paginated and filtered revenue events list.
- `GET /api/v1/revenue/events/{id}` — Event detail with customer transaction history.
- `POST /api/v1/revenue/import` — Safe validation import endpoint for synthetic revenue events.

### Risk & ML Prediction APIs (Phase 5)
- `POST /api/v1/risk/analyze/{event_id}` — Analyze single event risk and persist `RiskAssessment`.
- `POST /api/v1/risk/analyze-batch` — Analyze batch of events and summarize risk metrics.
- `GET /api/v1/risk/{event_id}` — Retrieve risk assessment.

### AI Recovery Agent APIs (Phase 6)
- `POST /api/v1/agent/analyze/{event_id}` — Diagnosis & strategy recommendation workflow.
- `POST /api/v1/agent/recommend/{event_id}` — Recommend optimal recovery strategy.
- `GET /api/v1/agent/{event_id}` — Get agent recommendation.

### Deterministic Policy & Guardrail APIs (Phase 7)
- `POST /api/v1/policy/evaluate/{event_id}` — Authoritative server-side policy decision evaluation and audit log.
- `GET /api/v1/policy/{event_id}` — Get calculated policy decision.

### Analytics & Merchant Intelligence APIs (Phase 9)
- `GET /api/v1/analytics/overview` — Core revenue KPIs: total revenue, revenue at risk, expected recovery, actual recovered, recovery rate %, and merchant-friendly formatted representations.
- `GET /api/v1/analytics/pipeline` — 7-stage recovery funnel (DETECTED → RISK_ANALYZED → AI_RECOMMENDED → POLICY_EVALUATED → ELIGIBLE → ATTEMPTED → RECOVERED) with count and amount at each stage.
- `GET /api/v1/analytics/strategies` — Performance breakdown by recovery strategy (attempts, successes, failures, amounts, success rate %).
- `GET /api/v1/analytics/scenarios` — Metrics by revenue loss scenario (payment_failure, checkout_abandonment, subscription_failure, overdue_invoice).
- `GET /api/v1/analytics/timeseries` — Daily time-series aggregation for dashboard charts.
- `GET /api/v1/analytics/opportunities` — Top recovery opportunities sorted by expected recovery, probability, and risk amount.
- `GET /api/v1/analytics/audit-summary` — Aggregate recommendation, policy decision, and execution counters + recent audit logs.
- `GET /api/v1/recovery/opportunities` — Retrieve prioritized recovery opportunities.
- `GET /api/v1/recovery/{event_id}` — Get recovery execution status.
- `POST /api/v1/recovery/{event_id}/execute` — Execute bounded recovery workflow (policy authorized).
- `POST /api/v1/recovery/{event_id}/approve` — Merchant approval for escalated events (policy re-checked).
- `POST /api/v1/recovery/{event_id}/stop` — Manually stop/suppress recovery workflow.
- `POST /api/v1/recovery/execute-batch` — Execute batch recovery and compute aggregate recovery metrics.
