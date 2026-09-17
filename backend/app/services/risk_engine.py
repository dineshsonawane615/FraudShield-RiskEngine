import math
import pandas as pd
from typing import Dict, Any, Tuple
from app.config import settings

def calculate_risk(
    fraud_probability: float,
    anomaly_score: float,
    features_df: pd.DataFrame
) -> Tuple[float, str, str]:
    """
    Aggregates XGBoost fraud probability, Isolation Forest anomaly score, 
    and behavioral signals into a 0-100 risk score, risk level, and decision.
    """
    xgb_w = settings.XGB_WEIGHT
    iforest_w = settings.IFOREST_WEIGHT

    # Combined base score (0.0 to 1.0)
    base_score = (fraud_probability * xgb_w) + (anomaly_score * iforest_w)
    risk_score_raw = base_score * 100.0

    # Behavioral signal boosts
    z_score = float(features_df.get("amount_z_score", [0]).iloc[0])
    is_new_device = int(features_df.get("is_new_device", [0]).iloc[0])
    unusual_time = int(features_df.get("unusual_time", [0]).iloc[0])
    tx_10m = int(features_df.get("transactions_last_10min", [0]).iloc[0])
    loc_anomaly = int(features_df.get("location_anomaly", [0]).iloc[0])

    boost = 0.0
    if z_score >= 5.0:
        boost += 15.0
    elif z_score >= 3.0:
        boost += 8.0

    if is_new_device and loc_anomaly:
        boost += 12.0
    elif is_new_device:
        boost += 5.0

    if tx_10m >= 5:
        boost += 15.0
    elif tx_10m >= 3:
        boost += 8.0

    if unusual_time and z_score > 2.0:
        boost += 10.0

    total_risk_score = round(min(100.0, max(0.0, risk_score_raw + boost)), 1)

    # Risk level classification
    if total_risk_score <= settings.LOW_THRESHOLD:
        risk_level = "LOW"
        decision = "PROCEED"
    elif total_risk_score <= settings.MEDIUM_THRESHOLD:
        risk_level = "MEDIUM"
        decision = "REVIEW"
    else:
        risk_level = "HIGH"
        decision = "ALERT"

    return total_risk_score, risk_level, decision
