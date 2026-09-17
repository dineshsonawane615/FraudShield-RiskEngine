import pandas as pd
from typing import List, Dict, Any, Tuple, Optional
from app.services.fraud_model import fraud_model_service

def generate_explanations(
    features_df: pd.DataFrame,
    meta_info: Dict[str, Any]
) -> Tuple[List[str], List[Dict[str, Any]], Optional[Dict[str, float]]]:
    """
    Computes SHAP values (if model available) and constructs 
    human-readable risk reasons and top contributing factors.
    """
    reasons: List[str] = []
    top_factors: List[Dict[str, Any]] = []
    shap_dict: Optional[Dict[str, float]] = None

    amount = float(features_df.get("amount", [0]).iloc[0])
    cust_avg = float(features_df.get("customer_avg_amount", [2500]).iloc[0])
    z_score = float(features_df.get("amount_z_score", [0]).iloc[0])
    is_new_device = int(features_df.get("is_new_device", [0]).iloc[0])
    unusual_time = int(features_df.get("unusual_time", [0]).iloc[0])
    tx_10m = int(features_df.get("transactions_last_10min", [0]).iloc[0])
    loc_anomaly = int(features_df.get("location_anomaly", [0]).iloc[0])

    # Rule-based human-readable reasons (Guaranteed understandable output)
    if z_score >= 3.0 or (cust_avg > 0 and amount >= 3.0 * cust_avg):
        reasons.append("Transaction amount is significantly above customer baseline")
        top_factors.append({
            "feature": "amount_z_score",
            "importance": round(min(0.40, 0.15 + 0.05 * z_score), 2),
            "description": f"Transaction amount (₹{amount:,.2f}) is significantly higher than customer average baseline (₹{cust_avg:,.2f})."
        })

    if is_new_device == 1:
        reasons.append("New device detected")
        top_factors.append({
            "feature": "is_new_device",
            "importance": 0.25,
            "description": "Transaction initiated from an unrecognized device ID."
        })

    if unusual_time == 1:
        reasons.append("Unusual transaction time")
        top_factors.append({
            "feature": "unusual_time",
            "importance": 0.15,
            "description": "Transaction occurred during unusual late-night hours."
        })

    if tx_10m >= 3:
        reasons.append("High transaction velocity")
        top_factors.append({
            "feature": "transactions_last_10min",
            "importance": 0.20,
            "description": f"High burst velocity detected ({tx_10m} transactions in last 10 minutes)."
        })

    if loc_anomaly == 1:
        reasons.append("Unusual location")
        top_factors.append({
            "feature": "location_anomaly",
            "importance": 0.20,
            "description": "Transaction location differs from customer's home baseline location."
        })

    # Default fallback reason for normal transactions
    if not reasons:
        reasons.append("Transaction matches normal customer behavior profile")
        top_factors.append({
            "feature": "amount_z_score",
            "importance": 0.05,
            "description": "Transaction amount is within normal variance range."
        })

    # Try computing actual SHAP feature attributions from XGBoost model
    try:
        import shap
        xgb = fraud_model_service._model
        if xgb is not None:
            explainer = shap.TreeExplainer(xgb)
            shap_values = explainer.shap_values(features_df)
            
            # Handle binary classification 1D or 2D SHAP array
            if len(shap_values.shape) == 2:
                vals = shap_values[0]
            else:
                vals = shap_values
                
            cols = features_df.columns
            shap_dict = {str(col): round(float(val), 4) for col, val in zip(cols, vals)}
    except Exception as e:
        # SHAP calculation fallback
        shap_dict = {factor["feature"]: factor["importance"] for factor in top_factors}

    # Sort top factors by importance descending
    top_factors = sorted(top_factors, key=lambda x: x["importance"], reverse=True)

    return reasons, top_factors, shap_dict
