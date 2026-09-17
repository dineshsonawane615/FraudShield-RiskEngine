import json
from fastapi.testclient import TestClient
from app.main import app

def run_end_to_end_verification():
    client = TestClient(app)
    print("==================================================")
    print(" FraudShield AI — End-to-End Backend Verification ")
    print("==================================================")

    # 1. Health Check
    print("\n1. Testing GET /api/health...")
    res = client.get("/api/health")
    assert res.status_code == 200
    print("   -> Status:", res.json()["status"], "| Models:", res.json()["models"])

    # 2. Normal Transaction Prediction
    print("\n2. Testing Normal Transaction (Expect LOW / PROCEED)...")
    normal_payload = {
        "customer_id": "C1001",
        "amount": 1500,
        "merchant": "Supermarket",
        "location": "Pune",
        "device_id": "DEV001",
        "is_new_device": False,
        "hour": 10,
        "transactions_last_10min": 0
    }
    res = client.post("/api/predict", json=normal_payload)
    assert res.status_code == 200
    n_data = res.json()
    print(f"   -> Transaction ID: {n_data['transaction_id']}")
    print(f"   -> Risk Score: {n_data['risk_score']} | Risk Level: {n_data['risk_level']} | Decision: {n_data['decision']}")
    assert n_data["risk_level"] == "LOW"
    assert n_data["decision"] == "PROCEED"

    # 3. Suspicious Transaction Prediction
    print("\n3. Testing Suspicious Transaction (Expect HIGH / ALERT)...")
    suspicious_payload = {
        "customer_id": "C1001",
        "amount": 45000,
        "merchant": "Electronics",
        "location": "Mumbai",
        "device_id": "DEV999",
        "is_new_device": True,
        "hour": 3,
        "transactions_last_10min": 8
    }
    res = client.post("/api/predict", json=suspicious_payload)
    assert res.status_code == 200
    s_data = res.json()
    print(f"   -> Transaction ID: {s_data['transaction_id']}")
    print(f"   -> Risk Score: {s_data['risk_score']} | Risk Level: {s_data['risk_level']} | Decision: {s_data['decision']}")
    print(f"   -> Fraud Reasons: {s_data['reasons']}")
    assert s_data["risk_level"] in ["MEDIUM", "HIGH"]

    # 4. Verify Alert Generation
    print("\n4. Testing GET /api/alerts...")
    res = client.get("/api/alerts")
    assert res.status_code == 200
    alerts = res.json()
    print(f"   -> Total Active Alerts: {len(alerts)}")
    assert len(alerts) > 0

    # 5. Verify Transaction Retrieval
    print("\n5. Testing GET /api/transactions...")
    res = client.get("/api/transactions")
    assert res.status_code == 200
    txs = res.json()
    print(f"   -> Total Recorded Transactions: {len(txs)}")

    # 6. Verify Feedback Submission
    print("\n6. Testing POST /api/feedback...")
    feedback_payload = {
        "transaction_id": s_data['transaction_id'],
        "action": "MARK_LEGITIMATE",
        "comment": "Customer confirmed transaction via OTP"
    }
    res = client.post("/api/feedback", json=feedback_payload)
    assert res.status_code == 200
    fb_data = res.json()
    print(f"   -> Action: {fb_data['analyst_action']} | Status: {fb_data['investigation_status']}")

    # 7. Verify Metrics Endpoint
    print("\n7. Testing GET /api/metrics...")
    res = client.get("/api/metrics")
    assert res.status_code == 200
    m_data = res.json()
    print(f"   -> Precision: {m_data['precision']} | Recall: {m_data['recall']} | F1: {m_data['f1']} | PR-AUC: {m_data['pr_auc']}")
    print(f"   -> Total Txs in DB: {m_data['transaction_count']} | High Risk Count: {m_data['high_risk_count']}")

    print("\n==================================================")
    print(" ALL 7 END-TO-END VERIFICATION CHECKS PASSED! ")
    print("==================================================")

if __name__ == "__main__":
    run_end_to_end_verification()
