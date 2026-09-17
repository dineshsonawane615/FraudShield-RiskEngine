<div align="center">

# 🛡️ FraudShield AI

### Real-Time, Explainable AI Fraud Detection System

[![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-009688?style=for-the-badge&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![Next.js](https://img.shields.io/badge/Next.js-16.3-black?style=for-the-badge&logo=next.js&logoColor=white)](https://nextjs.org)
[![Python](https://img.shields.io/badge/Python-3.11+-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://python.org)
[![XGBoost](https://img.shields.io/badge/XGBoost-ML-orange?style=for-the-badge)](https://xgboost.readthedocs.io)
[![SQLite](https://img.shields.io/badge/SQLite-Database-003B57?style=for-the-badge&logo=sqlite&logoColor=white)](https://sqlite.org)
[![TypeScript](https://img.shields.io/badge/TypeScript-5.7-3178C6?style=for-the-badge&logo=typescript&logoColor=white)](https://typescriptlang.org)

*An enterprise-grade fraud risk engine combining supervised XGBoost classification, unsupervised Isolation Forest anomaly detection, SHAP explainability, and a live analyst operations console.*

</div>

---

## 📋 Table of Contents

- [Overview](#-overview)
- [Live Demo Screenshots](#-live-demo-screenshots)
- [Tech Stack](#-tech-stack)
- [System Architecture](#-system-architecture)
- [ML Pipeline](#-ml-pipeline)
- [Project Structure](#-project-structure)
- [Quick Start](#-quick-start)
- [API Reference](#-api-reference)
- [Features](#-features)
- [Security](#-security)
- [Configuration](#-configuration)
- [Running Tests](#-running-tests)

---

## 🎯 Overview

**FraudShield AI** is a production-ready fraud detection platform that evaluates financial transactions in real time using a multi-layered machine learning pipeline. It flags suspicious activity, generates human-readable explanations for every decision, persists all results to a database, and provides fraud analysts with an interactive dashboard to review, approve, or block transactions.

### What makes it different

| Feature | Description |
|---|---|
| **Hybrid ML Engine** | Combines XGBoost (supervised, 60%) + Isolation Forest (unsupervised, 40%) for comprehensive coverage |
| **Explainable AI** | Every decision includes SHAP feature attributions and plain-English fraud reasons |
| **Deterministic Scoring** | Same transaction input always produces the same risk score — fully auditable |
| **Real-Time Pipeline** | Sub-second prediction: feature engineering → ML scoring → risk aggregation → DB persistence |
| **Analyst Feedback Loop** | Human labels stored for future model retraining without altering original risk scores |
| **Zero Mock Data** | Every number in the dashboard is the output of a real ML prediction pipeline |

---

## 🖥️ Live Demo Screenshots

> **Dashboard — Live Transaction Queue**
> Real-time risk scores from XGBoost + Isolation Forest. 61 transactions shown, 28 flagged HIGH risk.

> **Transaction Review Panel**
> Risk Score 100/100 · Fraud Probability 100% · Anomaly Score 86.3% · 5 ML fraud indicators

> **Analytics — Model Performance**
> Precision 100% · Recall 100% · F1 100% · False Positive Rate 0.0%

> **Backend Swagger API**
> Full OpenAPI documentation at `/api/docs`

---

## 🛠️ Tech Stack

### Backend
| Layer | Technology |
|---|---|
| API Framework | **FastAPI** 0.100+ with Uvicorn ASGI |
| ML — Supervised | **XGBoost** with class-imbalance weighting |
| ML — Unsupervised | **Isolation Forest** (scikit-learn) |
| Explainability | **SHAP** TreeExplainer + rule-based reasons |
| ORM | **SQLAlchemy** 2.0 |
| Database | **SQLite** (upgradeable to PostgreSQL) |
| Validation | **Pydantic** v2 with strict field constraints |
| Feature Scaling | **scikit-learn** StandardScaler |
| Config | **pydantic-settings** with `.env` support |

### Frontend
| Layer | Technology |
|---|---|
| Framework | **Next.js** 16.3 (Turbopack) |
| Language | **TypeScript** 5.7 |
| UI Library | **React** 19 |
| Icons | **Lucide React** |
| Styling | **Tailwind CSS** 4 |
| HTTP Client | Native **Fetch API** with typed client |

---

## 🏗️ System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     Next.js Frontend :3000                   │
│   ┌──────────┐  ┌──────────────────┐  ┌─────────────────┐  │
│   │ Live     │  │ Transaction      │  │ Analytics &     │  │
│   │ Queue    │  │ History          │  │ Model Metrics   │  │
│   └────┬─────┘  └────────┬─────────┘  └──────┬──────────┘  │
└────────┼─────────────────┼────────────────────┼─────────────┘
         │                 │  HTTP REST (JSON)   │
         ▼                 ▼                     ▼
┌─────────────────────────────────────────────────────────────┐
│                   FastAPI Backend :8000                      │
│                                                             │
│  POST /api/predict ──► Feature Engineering                  │
│                              │                              │
│                              ├──► XGBoost Classifier        │
│                              │    P(Fraud) → 0.0–1.0        │
│                              │                              │
│                              ├──► Isolation Forest          │
│                              │    Anomaly Score → 0.0–1.0   │
│                              │                              │
│                              └──► Hybrid Risk Engine        │
│                                   Score 0–100 + Decision    │
│                                   SHAP Explainability       │
│                                         │                   │
│                                         ▼                   │
│                              ┌──────────────────────┐       │
│                              │   SQLite Database    │       │
│                              │  Transactions        │       │
│                              │  Customers           │       │
│                              │  Alerts              │       │
│                              │  Feedbacks           │       │
│                              └──────────────────────┘       │
└─────────────────────────────────────────────────────────────┘
```

---

## 🤖 ML Pipeline

### 1. Feature Engineering (`services/feature_engineering.py`)

24 features are extracted per transaction:

| Feature Group | Features |
|---|---|
| **Amount** | `amount`, `customer_avg_amount`, `amount_ratio`, `amount_z_score` |
| **Device** | `is_new_device` |
| **Velocity** | `transactions_last_10min`, `transactions_last_1hour`, `transactions_last_24hours` |
| **Time** | `unusual_time` (00:00–05:59 or 23:00+), `hour`, `day_of_week` |
| **Location** | `location_anomaly`, `distance_from_usual_location` |
| **Customer** | `customer_transaction_count` |
| **PCA-style** | `V1–V10` (derived from anomaly factor — fully deterministic) |

### 2. XGBoost Classifier (`services/fraud_model.py`)

- Trained on synthetic credit card + behavioral transaction dataset
- Uses `scale_pos_weight` for severe class imbalance (fraud is rare)
- Returns P(Fraud) from 0.0 to 1.0
- Falls back to heuristic scoring if model file not present

### 3. Isolation Forest (`services/anomaly_model.py`)

- Unsupervised anomaly detection — no labels required
- Raw `decision_function` output transformed via sigmoid to [0, 1]
- Detects structural outliers independent of fraud labels

### 4. Hybrid Risk Engine (`services/risk_engine.py`)

```
Base Score = fraud_probability × 0.60 + anomaly_score × 0.40

Behavioral Boosts:
  + amount_z_score ≥ 5.0          → +15 points
  + amount_z_score ≥ 3.0          → +8  points
  + is_new_device + loc_anomaly    → +12 points
  + is_new_device only             → +5  points
  + transactions_last_10min ≥ 5   → +15 points
  + transactions_last_10min ≥ 3   → +8  points
  + unusual_time + z_score > 2.0  → +10 points

Final Risk Score = min(100, max(0, base_score × 100 + boosts))
```

| Score Range | Risk Level | Decision |
|:-----------:|:----------:|:--------:|
| 0 – 39 | 🟢 LOW | PROCEED |
| 40 – 69 | 🟡 MEDIUM | REVIEW |
| 70 – 100 | 🔴 HIGH | ALERT |

### 5. SHAP Explainability (`services/explanation.py`)

- Uses `shap.TreeExplainer` for XGBoost feature attributions
- Falls back to rule-based importance if SHAP unavailable
- Returns human-readable reason strings for every flagged signal

---

## 📁 Project Structure

```
FraudShield-AI/
│
├── backend/                          # FastAPI + ML Backend
│   ├── app/
│   │   ├── main.py                   # App entry point, middleware, routers
│   │   ├── config.py                 # Settings & environment variables
│   │   │
│   │   ├── api/                      # REST API Route Handlers
│   │   │   ├── routes_prediction.py  # POST /api/predict
│   │   │   ├── routes_transactions.py# GET  /api/transactions
│   │   │   ├── routes_alerts.py      # GET  /api/alerts
│   │   │   ├── routes_customers.py   # GET  /api/customers
│   │   │   ├── routes_feedback.py    # POST /api/feedback
│   │   │   ├── routes_metrics.py     # GET  /api/metrics
│   │   │   └── routes_health.py      # GET  /api/health
│   │   │
│   │   ├── services/                 # Business & ML Logic
│   │   │   ├── feature_engineering.py
│   │   │   ├── fraud_model.py        # XGBoost singleton
│   │   │   ├── anomaly_model.py      # Isolation Forest singleton
│   │   │   ├── risk_engine.py        # Hybrid scoring engine
│   │   │   ├── explanation.py        # SHAP + reason generator
│   │   │   └── feedback_service.py   # Analyst feedback handler
│   │   │
│   │   ├── models/
│   │   │   ├── database_models.py    # SQLAlchemy ORM (4 tables)
│   │   │   └── schemas.py            # Pydantic v2 schemas
│   │   │
│   │   └── database/
│   │       ├── database.py           # Engine, session, get_db()
│   │       └── seed.py               # Demo data seeder
│   │
│   ├── trained_models/               # Serialized ML artifacts
│   │   ├── xgboost_model.joblib
│   │   ├── isolation_forest.joblib
│   │   ├── scaler.joblib
│   │   └── metrics.json
│   │
│   ├── data/                         # Dataset preparation
│   ├── tests/                        # Pytest test suite
│   ├── train_models.py               # ML training script
│   ├── simulate_transactions.py      # Live streaming simulator
│   ├── requirements.txt
│   ├── .env.example
│   └── fraudshield.db                # SQLite database (auto-created)
│
└── frontend/                         # Next.js Analyst Dashboard
    ├── app/
    │   ├── layout.tsx                # Root layout
    │   ├── page.tsx                  # Main dashboard (Live Queue, History, Analytics)
    │   └── globals.css               # Design system & component styles
    ├── lib/
    │   ├── api.ts                    # Typed REST API client
    │   └── types.ts                  # TypeScript interfaces
    ├── .env.example
    ├── next.config.mjs
    └── package.json
```

---

## ⚡ Quick Start

### Prerequisites

- **Python** 3.11 or higher
- **Node.js** 18 or higher
- **npm** (or pnpm)

---

### 1. Clone the Repository

```bash
git clone https://github.com/your-username/fraudshield-ai.git
cd fraudshield-ai
```

---

### 2. Backend Setup

```bash
cd backend

# Create and activate virtual environment
python -m venv .venv

# Windows
.venv\Scripts\activate

# macOS / Linux
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

---

### 3. Train the ML Models

```bash
# From inside the backend/ directory
python train_models.py
```

This generates `trained_models/xgboost_model.joblib`, `isolation_forest.joblib`, `scaler.joblib`, and `metrics.json`.

---

### 4. Start the Backend Server

```bash
# From inside the backend/ directory
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

On first startup the server will:
- Create all database tables automatically
- Seed demo customers **C1001** (Rahul Sharma) and **C1002** (Anita Patel)
- Seed sample normal and HIGH-risk transactions
- Load the trained XGBoost and Isolation Forest models into memory

**API is now live at:** `http://localhost:8000`  
**Swagger UI:** `http://localhost:8000/api/docs`

---

### 5. Frontend Setup

```bash
# In a new terminal, from the project root
cd frontend

# Install dependencies
npm install

# Start the development server
npm run dev
```

**Dashboard is now live at:** `http://localhost:3000`

---

### 6. (Optional) Run the Transaction Simulator

```bash
# In a third terminal, from backend/
python simulate_transactions.py --count 20 --delay 1.5
```

This streams 20 realistic transactions to the API with 1.5-second delay between each, populating the live queue in real time.

---

## 📡 API Reference

### `POST /api/predict` — Predict Fraud Risk

Analyzes a transaction through the full ML pipeline and returns a risk score, decision, and explanation.

**Request:**
```json
{
  "customer_id": "C1001",
  "amount": 45000.0,
  "merchant": "Electronics",
  "location": "Mumbai",
  "device_id": "DEV999",
  "is_new_device": true,
  "hour": 3,
  "day_of_week": 2,
  "transactions_last_10min": 8,
  "transactions_last_1hour": 12,
  "transactions_last_24hours": 15
}
```

**Response:**
```json
{
  "transaction_id": "TX-A1B2C3D4E5",
  "customer_id": "C1001",
  "amount": 45000.0,
  "merchant": "Electronics",
  "location": "Mumbai",
  "fraud_probability": 0.91,
  "anomaly_score": 0.87,
  "risk_score": 94.0,
  "risk_level": "HIGH",
  "decision": "ALERT",
  "reasons": [
    "Transaction amount is significantly above customer baseline",
    "New device detected",
    "Unusual transaction time",
    "High transaction velocity",
    "Unusual location"
  ],
  "top_risk_factors": [
    {
      "feature": "amount_z_score",
      "importance": 0.4,
      "description": "Transaction amount (₹45,000) is significantly higher than customer average (₹2,500)."
    }
  ],
  "shap_values": { "amount_z_score": 0.2341, "is_new_device": 0.1823 },
  "timestamp": "2026-09-17T10:30:00"
}
```

---

### `GET /api/transactions` — List Transactions

```
GET /api/transactions?risk_level=HIGH&limit=50
GET /api/transactions/{transaction_id}
```

**Query Parameters:**

| Parameter | Type | Description |
|---|---|---|
| `risk_level` | string | Filter: `LOW`, `MEDIUM`, `HIGH` |
| `decision` | string | Filter: `PROCEED`, `REVIEW`, `ALERT` |
| `customer_id` | string | Filter by customer |
| `limit` | int | Max results (1–500, default 50) |

---

### `GET /api/alerts` — List Alerts

```
GET /api/alerts?status=OPEN&limit=50
```

| Status | Description |
|---|---|
| `OPEN` | Newly flagged — awaiting analyst review |
| `UNDER_REVIEW` | Assigned to analyst |
| `RESOLVED` | Closed by analyst action |

---

### `GET /api/customers/{id}` — Customer Profile

Returns customer profile including baseline spending patterns.

### `GET /api/customers/{id}/history` — Customer History

Returns full transaction history for a customer.

---

### `POST /api/feedback` — Submit Analyst Action

```json
{
  "transaction_id": "TX-A1B2C3D4E5",
  "action": "CONFIRM_FRAUD",
  "comment": "Cross-checked with customer — confirmed fraudulent"
}
```

| Action | Status Set | Label |
|---|---|---|
| `INVESTIGATE` | `UNDER_INVESTIGATION` | None |
| `MARK_LEGITIMATE` | `CLEARED` | 0 (not fraud) |
| `CONFIRM_FRAUD` | `CONFIRMED_FRAUD` | 1 (fraud) |
| `ESCALATE` | `ESCALATED` | 1 (fraud) |

> **Note:** Feedback actions update the investigation status only. Original ML risk scores are never modified, preserving the audit trail.

---

### `GET /api/metrics` — Model & Live Metrics

Returns trained model evaluation metrics plus live database statistics.

```json
{
  "precision": 1.0,
  "recall": 1.0,
  "f1": 1.0,
  "pr_auc": 1.0,
  "false_positive_rate": 0.0,
  "false_negative_rate": 0.0,
  "transaction_count": 61,
  "high_risk_count": 28,
  "medium_risk_count": 2,
  "low_risk_count": 31,
  "average_risk_score": 56.28
}
```

---

### `GET /api/health` — Health Check

```json
{
  "status": "healthy",
  "service": "FraudShield AI Backend",
  "version": "1.0.0",
  "database": "connected",
  "models": {
    "xgboost": "loaded",
    "isolation_forest": "loaded"
  }
}
```

---

## ✨ Features

### 🔴 Real-Time ML Prediction
- Sub-second transaction evaluation through the full ML pipeline
- Automatic Transaction ID generation (`TX-` prefix + UUID)
- Automatic alert creation for HIGH and MEDIUM risk transactions

### 📊 Explainable AI
- **SHAP TreeExplainer** feature attributions for every XGBoost prediction
- **Rule-based human-readable reasons** guaranteed even when SHAP is unavailable:
  - *"Transaction amount is significantly above customer baseline"*
  - *"New device detected"*
  - *"Unusual transaction time"*
  - *"High transaction velocity"*
  - *"Unusual location"*

### 👤 Customer Baseline Profiles
- Each customer has a stored `avg_amount`, `std_amount`, `usual_location`, `usual_device_id`
- Amount z-scores computed relative to individual customer history — not global averages
- Cold-start handling: unknown customers use sensible fallback defaults

### 🔁 Analyst Feedback Loop
- Four analyst actions: `INVESTIGATE`, `MARK_LEGITIMATE`, `CONFIRM_FRAUD`, `ESCALATE`
- Feedback labels (0 = legit, 1 = fraud) stored in dedicated `feedbacks` table
- Labels exportable for periodic model retraining

### 📡 Live Dashboard
- Real-time transaction queue sorted by ML risk score
- Search/filter across customer ID, transaction ID, merchant, location
- Transaction History view — full database log
- Analytics view — model performance metrics with trend sparklines
- "FastAPI Backend Online" status indicator in sidebar

### 🔄 Transaction Simulator
- `simulate_transactions.py` streams configurable bursts of realistic transactions
- Supports both normal (low-risk) and adversarial (high-risk) transaction profiles

---

## 🔒 Security

### Implemented Security Measures

| Measure | Implementation |
|---|---|
| **Security Headers** | `X-Content-Type-Options`, `X-Frame-Options`, `Referrer-Policy`, `Permissions-Policy` via custom middleware |
| **CORS Hardening** | Explicit origin whitelist — no wildcard `"*"` with `allow_credentials=True` |
| **Error Sanitization** | Internal exceptions logged server-side; only generic messages returned to clients |
| **Input Validation** | All fields have `max_length`, `gt`, `le` constraints in Pydantic schemas |
| **Environment-Gated Docs** | Swagger UI hidden when `ENVIRONMENT=production` |
| **Deterministic ML** | All features deterministic — same input always produces same output |
| **ORM Queries** | All database access via SQLAlchemy ORM — parameterized queries, no raw SQL |
| **Secrets Management** | `.env` excluded from version control via `.gitignore` |

### Recommended Before Production

- [ ] Add JWT or API-key authentication to all protected endpoints
- [ ] Add rate limiting (`slowapi`) — 30 req/min on `/api/predict`
- [ ] Migrate database from SQLite to PostgreSQL
- [ ] Enable HTTPS/TLS
- [ ] Add `created_at` DB indexes for query performance

---

## ⚙️ Configuration

Copy `.env.example` to `.env` and configure:

**`backend/.env.example`**
```env
# Database
DATABASE_URL=sqlite:///./fraudshield.db
# For PostgreSQL:
# DATABASE_URL=postgresql://user:password@localhost:5432/fraudshield

# CORS (comma-separated)
ALLOWED_ORIGINS=["http://localhost:3000","http://localhost:5173"]

# Risk Engine Weights (must sum to 1.0)
XGB_WEIGHT=0.60
IFOREST_WEIGHT=0.40

# Risk Thresholds
LOW_THRESHOLD=39.0
MEDIUM_THRESHOLD=69.0

# Environment (development | production)
ENVIRONMENT=development
```

**`frontend/.env.example`**
```env
# Backend API URL (no trailing slash)
NEXT_PUBLIC_API_URL=http://localhost:8000
```

---

## 🧪 Running Tests

```bash
cd backend

# Run full test suite
pytest tests/ -v

# Run specific test file
pytest tests/test_prediction.py -v

# Run with coverage report
pytest tests/ --cov=app --cov-report=term-missing
```

Test files:

| File | Coverage |
|---|---|
| `test_health.py` | Health endpoint, DB connection, model status |
| `test_prediction.py` | Normal tx, suspicious tx, edge cases, boundary values |
| `test_risk_engine.py` | Score calculation, threshold classification |
| `test_feedback.py` | All four analyst actions, status transitions |

---

## 🗄️ Database Schema

```
customers           transactions              alerts              feedbacks
──────────          ────────────              ──────              ─────────
id (PK)             id (PK)                   id (PK)             id (PK)
customer_id         transaction_id            transaction_id (FK) transaction_id (FK)
name                customer_id (FK)          customer_id         analyst_action
avg_amount          amount                    risk_score          label (0|1|null)
std_amount          merchant                  risk_level          comment
usual_location      location                  status              created_at
usual_device_id     device_id                 created_at
created_at          timestamp
                    is_new_device
                    transactions_last_10min
                    transactions_last_1hour
                    transactions_last_24hours
                    hour / day_of_week
                    fraud_probability
                    anomaly_score
                    risk_score
                    risk_level
                    decision
                    investigation_status
                    reasons_json
                    created_at
```

---

## 📦 Requirements

**Backend (`requirements.txt`)**
```
fastapi>=0.100.0
uvicorn>=0.22.0
pydantic>=2.0.0
pydantic-settings>=2.0.0
pandas>=2.0.0
numpy>=1.24.0
scikit-learn>=1.3.0
xgboost>=1.7.0
shap>=0.42.0
sqlalchemy>=2.0.0
joblib>=1.3.0
python-dotenv>=1.0.0
requests>=2.31.0
pytest>=7.4.0
httpx>=0.24.0
```

**Frontend (`package.json` key dependencies)**
```json
{
  "next": "16.3.3",
  "react": "^19",
  "typescript": "5.7.3",
  "lucide-react": "^1.16.0",
  "tailwindcss": "^4.3.3"
}
```

---

## 🚀 Deployment Notes

| Step | Action |
|---|---|
| Set `ENVIRONMENT=production` | Disables Swagger UI |
| Use PostgreSQL | Replace SQLite DATABASE_URL |
| Configure HTTPS | Add reverse proxy (nginx/Caddy) |
| Set `NEXT_PUBLIC_API_URL` | Point to production backend URL |
| Rotate any exposed secrets | Check git history with `git log` |
| Add authentication | Implement JWT or API key on all endpoints |

---

## 👨‍💻 Author

**Dinesh Sonawane**  
Full Stack AI/ML Developer  
GitHub: [@dineshsonawane615](https://github.com/dineshsonawane615)

---

<div align="center">

**Built with ❤️ using FastAPI · XGBoost · Isolation Forest · SHAP · Next.js · React · TypeScript**

*FraudShield AI — Because every fraudulent transaction tells a story. We just read it faster.*

</div>
