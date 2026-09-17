import json
import uuid
import datetime
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database.database import get_db
from app.models.database_models import Transaction, Alert
from app.models.schemas import PredictionInput, PredictionOutput
from app.services.feature_engineering import extract_features
from app.services.fraud_model import fraud_model_service
from app.services.anomaly_model import anomaly_model_service
from app.services.risk_engine import calculate_risk
from app.services.explanation import generate_explanations

router = APIRouter(prefix="/predict", tags=["Prediction"])

@router.post("", response_model=PredictionOutput)
def predict_fraud_risk(payload: PredictionInput, db: Session = Depends(get_db)):
    """
    Analyzes a transaction payload in real-time using feature engineering, 
    XGBoost fraud detection, Isolation Forest anomaly scoring, risk aggregation, 
    and SHAP explainability.
    """
    try:
        # 1. Feature Engineering & History Fetch
        features_df, meta_info = extract_features(payload, db)

        # 2. Model Scoring
        fraud_prob = fraud_model_service.predict_proba(features_df)
        anomaly_score = anomaly_model_service.predict_anomaly_score(features_df)

        # 3. Risk Engine Aggregation
        risk_score, risk_level, decision = calculate_risk(fraud_prob, anomaly_score, features_df)

        # 4. Explainability & Reason Generation
        reasons, top_risk_factors, shap_dict = generate_explanations(features_df, meta_info)

        # 5. Generate Transaction ID
        tx_id = f"TX-{uuid.uuid4().hex[:10].upper()}"
        now = datetime.datetime.utcnow()

        # 6. Save Transaction Record to Database
        tx_record = Transaction(
            transaction_id=tx_id,
            customer_id=payload.customer_id,
            amount=float(payload.amount),
            merchant=payload.merchant or "General Merchant",
            location=payload.location or "Unknown",
            device_id=payload.device_id or "UNKNOWN",
            timestamp=now,
            is_new_device=bool(payload.is_new_device),
            transactions_last_10min=payload.transactions_last_10min or 0,
            transactions_last_1hour=payload.transactions_last_1hour or 0,
            transactions_last_24hours=payload.transactions_last_24hours or 0,
            hour=payload.hour if payload.hour is not None else 12,
            day_of_week=payload.day_of_week if payload.day_of_week is not None else 0,
            fraud_probability=round(fraud_prob, 4),
            anomaly_score=round(anomaly_score, 4),
            risk_score=risk_score,
            risk_level=risk_level,
            decision=decision,
            investigation_status="UNASSIGNED",
            reasons_json=json.dumps(reasons),
            created_at=now
        )
        db.add(tx_record)
        db.commit()

        # 7. Auto-Create Alert if HIGH or MEDIUM risk
        if risk_level in ["HIGH", "MEDIUM"]:
            alert_status = "OPEN" if risk_level == "HIGH" else "UNDER_REVIEW"
            alert = Alert(
                transaction_id=tx_id,
                customer_id=payload.customer_id,
                risk_score=risk_score,
                risk_level=risk_level,
                status=alert_status,
                created_at=now
            )
            db.add(alert)
            db.commit()

        return PredictionOutput(
            transaction_id=tx_id,
            customer_id=payload.customer_id,
            amount=payload.amount,
            merchant=payload.merchant or "General Merchant",
            location=payload.location or "Unknown",
            device_id=payload.device_id or "UNKNOWN",
            is_new_device=bool(payload.is_new_device),
            fraud_probability=round(fraud_prob, 4),
            anomaly_score=round(anomaly_score, 4),
            risk_score=risk_score,
            risk_level=risk_level,
            decision=decision,
            reasons=reasons,
            top_risk_factors=top_risk_factors,
            shap_values=shap_dict,
            timestamp=now
        )
    except Exception as e:
        import logging
        logging.getLogger(__name__).exception("Prediction pipeline error")
        db.rollback()
        raise HTTPException(status_code=500, detail="An internal error occurred during prediction. Please try again later.")
