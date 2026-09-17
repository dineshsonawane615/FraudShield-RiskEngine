import pandas as pd
from app.services.risk_engine import calculate_risk

def test_risk_calculation_low():
    features_dict = {
        "amount_z_score": [0.2],
        "is_new_device": [0],
        "unusual_time": [0],
        "transactions_last_10min": [0],
        "location_anomaly": [0]
    }
    df = pd.DataFrame(features_dict)
    risk_score, risk_level, decision = calculate_risk(0.05, 0.10, df)

    assert risk_score < 40.0
    assert risk_level == "LOW"
    assert decision == "PROCEED"

def test_risk_calculation_high():
    features_dict = {
        "amount_z_score": [6.0],
        "is_new_device": [1],
        "unusual_time": [1],
        "transactions_last_10min": [8],
        "location_anomaly": [1]
    }
    df = pd.DataFrame(features_dict)
    risk_score, risk_level, decision = calculate_risk(0.90, 0.85, df)

    assert risk_score >= 70.0
    assert risk_level == "HIGH"
    assert decision == "ALERT"
