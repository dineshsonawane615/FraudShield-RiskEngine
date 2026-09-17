# FraudShield AI — Real-Time Explainable AI Fraud Detection Backend

FraudShield AI is an enterprise-ready, explainable AI fraud-risk detection engine designed for real-time transaction monitoring, anomaly detection, risk scoring, alert management, and analyst feedback loops.

---

## Architecture Overview

FraudShield AI uses a multi-layered detection pipeline:
1. **Behavioral Feature Engineering**: Computes real-time velocity metrics (10m, 1h, 24h), z-score amount deviations against customer baseline profiles, location anomaly flags, time-of-day checks, and device change detection. Cold-start customers are handled with sensible fallback defaults.
2. **XGBoost Classifier**: Supervised fraud detection trained on transaction behavior with class weighting (`scale_pos_weight`) for severe imbalanced classification.
3. **Isolation Forest**: Unsupervised anomaly detection identifying transactions with unusual structural patterns.
4. **Hybrid Risk Engine**: Combines supervised $P(\text{Fraud})$ (60%) and unsupervised anomaly scores (40%) plus behavioral boosts into a $0–100$ risk score.
   - **0–39**: LOW risk $\rightarrow$ `PROCEED`
   - **40–69**: MEDIUM risk $\rightarrow$ `REVIEW`
   - **70–100**: HIGH risk $\rightarrow$ `ALERT`
5. **SHAP & Human-Readable Explainability**: Generates tree feature attributions and actionable plain-English reason strings (e.g., *"Transaction amount is significantly above customer baseline"*).
6. **Analyst Feedback Loop**: Enables fraud analysts to mark transactions as legitimate or confirmed fraud without modifying historical risk scores.

---

## Folder Structure

```
backend/
├── app/
│   ├── main.py                    # FastAPI Entrypoint & Middleware
│   ├── config.py                  # App Settings & Environment Vars
│   ├── api/                       # REST API Endpoints
│   │   ├── routes_prediction.py    # POST /api/predict
│   │   ├── routes_transactions.py  # GET /api/transactions & GET /api/transactions/{id}
│   │   ├── routes_alerts.py        # GET /api/alerts
│   │   ├── routes_customers.py     # GET /api/customers & GET /api/customers/{id}/history
│   │   ├── routes_feedback.py      # POST /api/feedback
│   │   ├── routes_metrics.py       # GET /api/metrics
│   │   └── routes_health.py        # GET /api/health
│   ├── models/
│   │   ├── database_models.py     # SQLAlchemy ORM Models
│   │   └── schemas.py             # Pydantic Request/Response Schemas
│   ├── services/                  # Business & ML Logic
│   │   ├── feature_engineering.py # Real-time feature calculation
│   │   ├── fraud_model.py         # XGBoost Model Loading Singleton
│   │   ├── anomaly_model.py       # Isolation Forest Singleton
│   │   ├── risk_engine.py         # Risk aggregation & threshold logic
│   │   ├── explanation.py         # SHAP & reason text generator
│   │   └── feedback_service.py    # Analyst feedback handler
│   └── database/
│       ├── database.py            # SQLAlchemy Engine & Session
│       └── seed.py                # Database Seeder (Customer C1001 & demo txs)
├── data/
│   └── prepare_dataset.py         # Synthetic Credit Card & Behavioral Dataset Script
├── trained_models/
│   ├── xgboost_model.joblib       # Serialized XGBoost Model
│   ├── isolation_forest.joblib    # Serialized Isolation Forest
│   ├── scaler.joblib              # Feature Scaler
│   └── metrics.json               # Precision, Recall, PR-AUC Metrics
├── train_models.py                # ML Training Script
├── simulate_transactions.py       # Real-Time Transaction Streaming Simulator
├── tests/                         # Pytest Suite
│   ├── conftest.py
│   ├── test_health.py
│   ├── test_prediction.py
│   ├── test_risk_engine.py
│   └── test_feedback.py
├── requirements.txt
├── .env.example
└── README.md
```

---

## Getting Started

### 1. Installation
Ensure Python 3.11+ is installed.

```bash
# Navigate to backend directory
cd backend

# Install dependencies
pip install -r requirements.txt
```

### 2. Model Training & Data Preparation
Train the XGBoost and Isolation Forest models and export artifacts to `trained_models/`:

```bash
python train_models.py
```

### 3. Database Seeding & Launch Server
Start the FastAPI server (it automatically runs database tables initialization and seeder on startup):

```bash
uvicorn app.main:app --reload --port 8000
```

- **Swagger Documentation**: [http://127.0.0.1:8000/api/docs](http://127.0.0.1:8000/api/docs)
- **ReDoc API Spec**: [http://127.0.0.1:8000/api/redoc](http://127.0.0.1:8000/api/redoc)

---

## Real-Time Transaction Streaming Simulator

To demonstrate live streaming transactions to the dashboard, run the simulator script in a separate terminal:

```bash
python simulate_transactions.py --count 20 --delay 1.5
```

---

## Running Automated Tests

Run the full pytest suite:

```bash
pytest tests
```

---

## API Documentation

### 1. Predict Fraud Risk
- **POST** `/api/predict`

**Request Body:**
```json
{
  "customer_id": "C1001",
  "amount": 45000,
  "merchant": "Electronics",
  "location": "Mumbai",
  "device_id": "DEV999",
  "is_new_device": true,
  "hour": 3,
  "transactions_last_10min": 8
}
```

**Response Body:**
```json
{
  "transaction_id": "TX-A1B2C3D4E5",
  "customer_id": "C1001",
  "amount": 45000.0,
  "merchant": "Electronics",
  "location": "Mumbai",
  "device_id": "DEV999",
  "is_new_device": true,
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
      "importance": 0.35,
      "description": "Transaction amount (₹45,000.00) is significantly higher than customer average baseline (₹2,500.00)."
    }
  ],
  "timestamp": "2026-09-17T15:30:00"
}
```

### 2. Transaction Management
- **GET** `/api/transactions` (Query parameters: `risk_level`, `decision`, `customer_id`, `limit`)
- **GET** `/api/transactions/{transaction_id}`

### 3. Alerts Management
- **GET** `/api/alerts` (Query parameter: `status` = `OPEN`, `UNDER_REVIEW`, `RESOLVED`)

### 4. Customer Profiles & History
- **GET** `/api/customers/{customer_id}`
- **GET** `/api/customers/{customer_id}/history`

### 5. Analyst Feedback
- **POST** `/api/feedback`

**Request Body:**
```json
{
  "transaction_id": "TX-A1B2C3D4E5",
  "action": "MARK_LEGITIMATE",
  "comment": "Confirmed with cardholder via phone OTP"
}
```

### 6. System Metrics & Health
- **GET** `/api/metrics`
- **GET** `/api/health`

---

## Connecting a React Frontend

To integrate a React/Next.js dashboard:
1. Set the API Base URL to `http://localhost:8000/api`.
2. Ensure CORS is enabled (default allows `http://localhost:3000` and `http://localhost:5173`).
3. Call `POST /api/predict` when submitting transaction forms.
4. Call `GET /api/transactions` and `GET /api/alerts` to render transaction tables and alert notifications in real-time.
5. Call `POST /api/feedback` from analyst action modal dialogues.
