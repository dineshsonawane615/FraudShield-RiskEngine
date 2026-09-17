import numpy as np
import pandas as pd
from typing import Dict, Any, Tuple
from sqlalchemy.orm import Session
from app.models.database_models import Customer, Transaction
from app.models.schemas import PredictionInput

FEATURE_COLUMNS = [
    "amount", "customer_avg_amount", "amount_ratio", "amount_z_score",
    "is_new_device", "transactions_last_10min", "transactions_last_1hour",
    "transactions_last_24hours", "unusual_time", "location_anomaly",
    "distance_from_usual_location", "customer_transaction_count", "hour", "day_of_week",
    "V1", "V2", "V3", "V4", "V5", "V6", "V7", "V8", "V9", "V10"
]

def extract_features(payload: PredictionInput, db: Session) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    """
    Extracts engineered features from payload + customer history in DB.
    Handles cold-start fallback gracefully if customer record does not exist.
    """
    # 1. Fetch customer from DB or apply cold-start defaults
    customer = db.query(Customer).filter(Customer.customer_id == payload.customer_id).first()
    
    if customer:
        cust_avg = customer.avg_amount
        cust_std = customer.std_amount if customer.std_amount > 0 else 500.0
        usual_loc = customer.usual_location
        usual_dev = customer.usual_device_id
        tx_count = db.query(Transaction).filter(Transaction.customer_id == payload.customer_id).count()
    else:
        # Cold start fallback for unknown customer
        cust_avg = 2500.0
        cust_std = 500.0
        usual_loc = payload.location or "Unknown"
        usual_dev = payload.device_id or "UNKNOWN"
        tx_count = 0

    # 2. Extract input values & fallbacks
    amount = float(payload.amount)
    hour = payload.hour if payload.hour is not None else 12
    day_of_week = payload.day_of_week if payload.day_of_week is not None else 0
    
    # Ratios and Z-Scores
    amount_ratio = amount / (cust_avg + 1e-5)
    amount_z_score = (amount - cust_avg) / (cust_std + 1e-5)
    
    # Device checks
    is_new_device = 1 if payload.is_new_device or (payload.device_id and payload.device_id != usual_dev) else 0
    
    # Velocities
    tx_10m = payload.transactions_last_10min if payload.transactions_last_10min is not None else 0
    tx_1h = payload.transactions_last_1hour if payload.transactions_last_1hour is not None else max(tx_10m, 0)
    tx_24h = payload.transactions_last_24hours if payload.transactions_last_24hours is not None else max(tx_1h, 0)
    
    # Time & Location checks
    unusual_time = 1 if (hour < 6 or hour >= 23) else 0
    loc_anomaly = 1 if (payload.location and payload.location.lower() != usual_loc.lower()) else 0
    dist_loc = 500.0 if loc_anomaly else 0.0

    # Synthetic PCA features (V1-V10) aligned with behavioral anomaly level
    anomaly_factor = 0.0
    if amount_z_score > 3.0:
        anomaly_factor += 1.5
    if is_new_device:
        anomaly_factor += 1.0
    if loc_anomaly:
        anomaly_factor += 1.0
    if tx_10m > 3:
        anomaly_factor += 1.0
        
    # Deterministic V-features derived from anomaly_factor — same input always yields same output.
    # Previously used np.random.normal() which made risk scores non-reproducible (FIXED: VUL-006).
    v_features = {f"V{i}": float(anomaly_factor * (0.5 + 0.1 * i)) for i in range(1, 11)}

    feature_dict = {
        "amount": amount,
        "customer_avg_amount": cust_avg,
        "amount_ratio": amount_ratio,
        "amount_z_score": amount_z_score,
        "is_new_device": is_new_device,
        "transactions_last_10min": tx_10m,
        "transactions_last_1hour": tx_1h,
        "transactions_last_24hours": tx_24h,
        "unusual_time": unusual_time,
        "location_anomaly": loc_anomaly,
        "distance_from_usual_location": dist_loc,
        "customer_transaction_count": tx_count,
        "hour": hour,
        "day_of_week": day_of_week,
        **v_features
    }

    df_features = pd.DataFrame([feature_dict])[FEATURE_COLUMNS]
    
    meta_info = {
        "cust_avg": cust_avg,
        "cust_std": cust_std,
        "usual_loc": usual_loc,
        "usual_dev": usual_dev,
        "tx_count": tx_count
    }

    return df_features, meta_info
