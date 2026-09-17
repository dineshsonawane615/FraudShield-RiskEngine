"""
Comprehensive test suite for FraudShield AI Backend.
Tests every endpoint with multiple edge cases.
"""
# Force UTF-8 stdout for Windows
import io, sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

import json
import os
import traceback


sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Ensure DB tables exist before test client starts
from app.database.database import engine, Base
from app.models.database_models import Customer, Transaction, Alert, Feedback  # noqa
Base.metadata.create_all(bind=engine)
from app.database.seed import seed_database
seed_database()

from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


PASS = 0
FAIL = 0
ERRORS = []

def test(name, fn):
    global PASS, FAIL, ERRORS
    try:
        fn()
        PASS += 1
        print(f"  [PASS] {name}")
    except AssertionError as e:
        FAIL += 1
        msg = f"  [FAIL] {name}: {e}"
        print(msg)
        ERRORS.append(msg)
    except Exception as e:
        FAIL += 1
        msg = f"  [ERROR] {name}: {type(e).__name__}: {e}\n{traceback.format_exc()}"
        print(msg)
        ERRORS.append(msg)


print("=" * 60)
print(" FraudShield AI — Comprehensive Endpoint Testing")
print("=" * 60)

# ============================================================
# 1. HEALTH ENDPOINT
# ============================================================
print("\n--- 1. GET /api/health ---")

def test_health_basic():
    r = client.get("/api/health")
    assert r.status_code == 200, f"Expected 200, got {r.status_code}"
    d = r.json()
    assert d["status"] == "healthy"
    assert "models" in d
    assert "xgboost" in d["models"]
    assert "isolation_forest" in d["models"]
test("Health basic", test_health_basic)

def test_root():
    r = client.get("/")
    assert r.status_code == 200
    d = r.json()
    assert "message" in d
test("Root endpoint", test_root)

# ============================================================
# 2. PREDICT ENDPOINT — Normal Transactions
# ============================================================
print("\n--- 2. POST /api/predict — Normal Transactions ---")

def test_predict_normal_low_amount():
    payload = {
        "customer_id": "C1001",
        "amount": 1500,
        "merchant": "Supermarket",
        "location": "Pune",
        "device_id": "DEV001",
        "is_new_device": False,
        "hour": 10,
        "transactions_last_10min": 0
    }
    r = client.post("/api/predict", json=payload)
    assert r.status_code == 200, f"Status {r.status_code}: {r.text}"
    d = r.json()
    assert d["risk_level"] == "LOW", f"Expected LOW, got {d['risk_level']} (score={d['risk_score']})"
    assert d["decision"] == "PROCEED", f"Expected PROCEED, got {d['decision']}"
    assert d["fraud_probability"] >= 0.0
    assert d["anomaly_score"] >= 0.0
    assert len(d["reasons"]) > 0
    assert "transaction_id" in d
test("Normal transaction ₹1500 Pune DEV001", test_predict_normal_low_amount)

def test_predict_normal_medium_amount():
    payload = {
        "customer_id": "C1001",
        "amount": 2500,
        "merchant": "Grocery",
        "location": "Pune",
        "device_id": "DEV001",
        "is_new_device": False,
        "hour": 14,
        "transactions_last_10min": 1
    }
    r = client.post("/api/predict", json=payload)
    assert r.status_code == 200
    d = r.json()
    assert d["risk_level"] == "LOW", f"Expected LOW, got {d['risk_level']} (score={d['risk_score']})"
test("Normal transaction ₹2500 Pune DEV001", test_predict_normal_medium_amount)

def test_predict_normal_slightly_high():
    payload = {
        "customer_id": "C1001",
        "amount": 3100,
        "merchant": "Electronics",
        "location": "Pune",
        "device_id": "DEV001",
        "is_new_device": False,
        "hour": 18,
        "transactions_last_10min": 0
    }
    r = client.post("/api/predict", json=payload)
    assert r.status_code == 200
    d = r.json()
    # Slightly above avg but same location + device, should still be LOW
    assert d["risk_level"] == "LOW", f"Expected LOW, got {d['risk_level']} (score={d['risk_score']})"
test("Normal transaction ₹3100 same device/location", test_predict_normal_slightly_high)

# ============================================================
# 3. PREDICT ENDPOINT — Suspicious Transactions
# ============================================================
print("\n--- 3. POST /api/predict — Suspicious Transactions ---")

def test_predict_suspicious_full():
    payload = {
        "customer_id": "C1001",
        "amount": 45000,
        "merchant": "Electronics",
        "location": "Mumbai",
        "device_id": "DEV999",
        "is_new_device": True,
        "hour": 3,
        "transactions_last_10min": 8
    }
    r = client.post("/api/predict", json=payload)
    assert r.status_code == 200
    d = r.json()
    assert d["risk_level"] == "HIGH", f"Expected HIGH, got {d['risk_level']} (score={d['risk_score']})"
    assert d["decision"] == "ALERT"
    assert "Transaction amount is significantly above customer baseline" in d["reasons"]
    assert "New device detected" in d["reasons"]
    assert "Unusual transaction time" in d["reasons"]
    assert "High transaction velocity" in d["reasons"]
    assert "Unusual location" in d["reasons"]
test("Suspicious ₹45000 Mumbai DEV999 3am velocity=8", test_predict_suspicious_full)

def test_predict_new_device_only():
    """New device but normal location/time/amount — should not be HIGH"""
    payload = {
        "customer_id": "C1001",
        "amount": 2000,
        "merchant": "Cafe",
        "location": "Pune",
        "device_id": "DEV_NEW_123",
        "is_new_device": True,
        "hour": 15,
        "transactions_last_10min": 0
    }
    r = client.post("/api/predict", json=payload)
    assert r.status_code == 200
    d = r.json()
    # New device alone shouldn't be HIGH
    assert d["risk_level"] in ["LOW", "MEDIUM"], f"Got {d['risk_level']} (score={d['risk_score']})"
test("New device only, normal everything else", test_predict_new_device_only)

def test_predict_unusual_time_only():
    """Late night but normal amount/location/device"""
    payload = {
        "customer_id": "C1001",
        "amount": 2000,
        "merchant": "Online Store",
        "location": "Pune",
        "device_id": "DEV001",
        "is_new_device": False,
        "hour": 2,
        "transactions_last_10min": 0
    }
    r = client.post("/api/predict", json=payload)
    assert r.status_code == 200
    d = r.json()
    assert d["risk_level"] in ["LOW", "MEDIUM"], f"Got {d['risk_level']} (score={d['risk_score']})"
test("Unusual time only, normal everything else", test_predict_unusual_time_only)

def test_predict_high_velocity_only():
    """High velocity but normal amount/location/device"""
    payload = {
        "customer_id": "C1001",
        "amount": 2000,
        "merchant": "ATM",
        "location": "Pune",
        "device_id": "DEV001",
        "is_new_device": False,
        "hour": 14,
        "transactions_last_10min": 10
    }
    r = client.post("/api/predict", json=payload)
    assert r.status_code == 200
    d = r.json()
    # High velocity alone should trigger some concern
    assert d["risk_score"] > 0
test("High velocity only, normal everything else", test_predict_high_velocity_only)

def test_predict_location_anomaly_only():
    """Different city but normal amount/device/time"""
    payload = {
        "customer_id": "C1001",
        "amount": 2500,
        "merchant": "Restaurant",
        "location": "Delhi",
        "device_id": "DEV001",
        "is_new_device": False,
        "hour": 12,
        "transactions_last_10min": 0
    }
    r = client.post("/api/predict", json=payload)
    assert r.status_code == 200
    d = r.json()
    assert d["risk_level"] in ["LOW", "MEDIUM"], f"Got {d['risk_level']} (score={d['risk_score']})"
test("Location anomaly only", test_predict_location_anomaly_only)

def test_predict_very_high_amount():
    """Extremely high amount with all other flags"""
    payload = {
        "customer_id": "C1001",
        "amount": 500000,
        "merchant": "Jewelry",
        "location": "Unknown City",
        "device_id": "DEV_STOLEN",
        "is_new_device": True,
        "hour": 1,
        "transactions_last_10min": 15
    }
    r = client.post("/api/predict", json=payload)
    assert r.status_code == 200
    d = r.json()
    assert d["risk_level"] == "HIGH", f"Expected HIGH for massive fraud, got {d['risk_level']}"
    assert d["risk_score"] >= 70
test("Extreme fraud ₹500000 all flags", test_predict_very_high_amount)

# ============================================================
# 4. PREDICT ENDPOINT — Edge Cases & Validation
# ============================================================
print("\n--- 4. POST /api/predict — Edge Cases ---")

def test_predict_unknown_customer():
    """Customer that doesn't exist in DB — cold-start fallback"""
    payload = {
        "customer_id": "C9999",
        "amount": 5000,
        "merchant": "Store",
        "location": "Bangalore",
        "device_id": "DEV_X",
        "is_new_device": False,
        "hour": 10,
        "transactions_last_10min": 0
    }
    r = client.post("/api/predict", json=payload)
    assert r.status_code == 200, f"Cold-start should work, got {r.status_code}: {r.text}"
    d = r.json()
    assert d["customer_id"] == "C9999"
test("Unknown customer cold-start", test_predict_unknown_customer)

def test_predict_missing_optional_fields():
    """Only required fields, everything else null/default"""
    payload = {
        "customer_id": "C1001",
        "amount": 2000
    }
    r = client.post("/api/predict", json=payload)
    assert r.status_code == 200, f"Should accept minimal payload, got {r.status_code}: {r.text}"
test("Minimal payload (only customer_id + amount)", test_predict_missing_optional_fields)

def test_predict_zero_amount():
    """Zero amount should fail validation (amount > 0)"""
    payload = {
        "customer_id": "C1001",
        "amount": 0
    }
    r = client.post("/api/predict", json=payload)
    assert r.status_code == 422, f"Expected 422 for zero amount, got {r.status_code}"
test("Zero amount (should return 422)", test_predict_zero_amount)

def test_predict_negative_amount():
    """Negative amount should fail validation"""
    payload = {
        "customer_id": "C1001",
        "amount": -100
    }
    r = client.post("/api/predict", json=payload)
    assert r.status_code == 422, f"Expected 422, got {r.status_code}"
test("Negative amount (should return 422)", test_predict_negative_amount)

def test_predict_missing_customer_id():
    """Missing customer_id should fail validation"""
    payload = {
        "amount": 2000
    }
    r = client.post("/api/predict", json=payload)
    assert r.status_code == 422, f"Expected 422, got {r.status_code}"
test("Missing customer_id (should return 422)", test_predict_missing_customer_id)

def test_predict_invalid_hour():
    """Hour > 23 should fail validation"""
    payload = {
        "customer_id": "C1001",
        "amount": 2000,
        "hour": 25
    }
    r = client.post("/api/predict", json=payload)
    assert r.status_code == 422, f"Expected 422 for invalid hour, got {r.status_code}"
test("Invalid hour=25 (should return 422)", test_predict_invalid_hour)

def test_predict_empty_body():
    """Empty body should fail"""
    r = client.post("/api/predict", json={})
    assert r.status_code == 422
test("Empty body (should return 422)", test_predict_empty_body)

def test_predict_string_amount():
    """String amount should fail"""
    payload = {
        "customer_id": "C1001",
        "amount": "abc"
    }
    r = client.post("/api/predict", json=payload)
    assert r.status_code == 422
test("String amount (should return 422)", test_predict_string_amount)

def test_predict_very_small_amount():
    """Very small but valid amount"""
    payload = {
        "customer_id": "C1001",
        "amount": 0.01,
        "location": "Pune",
        "device_id": "DEV001",
        "is_new_device": False,
        "hour": 10,
        "transactions_last_10min": 0
    }
    r = client.post("/api/predict", json=payload)
    assert r.status_code == 200
    d = r.json()
    assert d["risk_level"] == "LOW", f"₹0.01 should be LOW, got {d['risk_level']}"
test("Very small amount ₹0.01", test_predict_very_small_amount)

# ============================================================
# 5. TRANSACTIONS ENDPOINT
# ============================================================
print("\n--- 5. GET /api/transactions ---")

def test_get_all_transactions():
    r = client.get("/api/transactions")
    assert r.status_code == 200
    d = r.json()
    assert isinstance(d, list)
    assert len(d) > 0
    tx = d[0]
    # Check all expected fields exist
    required_fields = ["transaction_id", "customer_id", "amount", "risk_score", 
                       "risk_level", "decision", "investigation_status", "reasons"]
    for f in required_fields:
        assert f in tx, f"Missing field '{f}' in transaction response"
test("Get all transactions", test_get_all_transactions)

def test_get_transactions_filter_risk_level():
    r = client.get("/api/transactions?risk_level=HIGH")
    assert r.status_code == 200
    d = r.json()
    for tx in d:
        assert tx["risk_level"] == "HIGH", f"Expected HIGH, got {tx['risk_level']}"
test("Filter by risk_level=HIGH", test_get_transactions_filter_risk_level)

def test_get_transactions_filter_low():
    r = client.get("/api/transactions?risk_level=LOW")
    assert r.status_code == 200
    d = r.json()
    for tx in d:
        assert tx["risk_level"] == "LOW"
test("Filter by risk_level=LOW", test_get_transactions_filter_low)

def test_get_transactions_filter_decision():
    r = client.get("/api/transactions?decision=ALERT")
    assert r.status_code == 200
    d = r.json()
    for tx in d:
        assert tx["decision"] == "ALERT"
test("Filter by decision=ALERT", test_get_transactions_filter_decision)

def test_get_transactions_filter_customer():
    r = client.get("/api/transactions?customer_id=C1001")
    assert r.status_code == 200
    d = r.json()
    for tx in d:
        assert tx["customer_id"] == "C1001"
test("Filter by customer_id=C1001", test_get_transactions_filter_customer)

def test_get_transactions_limit():
    r = client.get("/api/transactions?limit=2")
    assert r.status_code == 200
    d = r.json()
    assert len(d) <= 2
test("Limit=2", test_get_transactions_limit)

def test_get_transactions_invalid_limit():
    r = client.get("/api/transactions?limit=0")
    assert r.status_code == 422
test("Invalid limit=0 (should return 422)", test_get_transactions_invalid_limit)

def test_get_transactions_nonexistent_filter():
    r = client.get("/api/transactions?customer_id=DOESNOTEXIST")
    assert r.status_code == 200
    d = r.json()
    assert len(d) == 0
test("Filter nonexistent customer", test_get_transactions_nonexistent_filter)

# ============================================================
# 6. TRANSACTION BY ID
# ============================================================
print("\n--- 6. GET /api/transactions/{id} ---")

def test_get_transaction_by_valid_id():
    # First get a transaction to use its ID
    r = client.get("/api/transactions?limit=1")
    d = r.json()
    assert len(d) > 0
    tx_id = d[0]["transaction_id"]
    
    r2 = client.get(f"/api/transactions/{tx_id}")
    assert r2.status_code == 200
    d2 = r2.json()
    assert d2["transaction_id"] == tx_id
test("Get transaction by valid ID", test_get_transaction_by_valid_id)

def test_get_transaction_not_found():
    r = client.get("/api/transactions/TX_DOES_NOT_EXIST")
    assert r.status_code == 404, f"Expected 404, got {r.status_code}"
test("Transaction not found (should return 404)", test_get_transaction_not_found)

def test_get_seeded_suspicious_tx():
    r = client.get("/api/transactions/TX_DEMO_SUSPICIOUS_999")
    assert r.status_code == 200
    d = r.json()
    assert d["risk_level"] == "HIGH"
    assert d["amount"] == 45000.0
test("Get seeded suspicious demo transaction", test_get_seeded_suspicious_tx)

# ============================================================
# 7. ALERTS ENDPOINT
# ============================================================
print("\n--- 7. GET /api/alerts ---")

def test_get_all_alerts():
    r = client.get("/api/alerts")
    assert r.status_code == 200
    d = r.json()
    assert isinstance(d, list)
    if len(d) > 0:
        alert = d[0]
        required = ["id", "transaction_id", "customer_id", "risk_score", "risk_level", "status"]
        for f in required:
            assert f in alert, f"Missing field '{f}' in alert"
test("Get all alerts", test_get_all_alerts)

def test_get_alerts_filter_open():
    r = client.get("/api/alerts?status=OPEN")
    assert r.status_code == 200
    d = r.json()
    for a in d:
        assert a["status"] == "OPEN"
test("Filter alerts status=OPEN", test_get_alerts_filter_open)

def test_get_alerts_filter_resolved():
    r = client.get("/api/alerts?status=RESOLVED")
    assert r.status_code == 200
test("Filter alerts status=RESOLVED", test_get_alerts_filter_resolved)

def test_alert_created_for_high_risk():
    """Verify that a HIGH-risk prediction creates an alert"""
    payload = {
        "customer_id": "C1001",
        "amount": 60000,
        "merchant": "Unknown Vendor",
        "location": "Kolkata",
        "device_id": "DEV_ALERT_TEST",
        "is_new_device": True,
        "hour": 2,
        "transactions_last_10min": 6
    }
    r = client.post("/api/predict", json=payload)
    assert r.status_code == 200
    d = r.json()
    tx_id = d["transaction_id"]
    
    # Check alert was created
    r2 = client.get("/api/alerts")
    alerts = r2.json()
    matched = [a for a in alerts if a["transaction_id"] == tx_id]
    if d["risk_level"] in ["HIGH", "MEDIUM"]:
        assert len(matched) > 0, f"Alert should exist for tx {tx_id} with risk_level={d['risk_level']}"
test("Alert auto-created for HIGH risk prediction", test_alert_created_for_high_risk)

def test_no_alert_for_low_risk():
    """LOW risk prediction should NOT create an alert"""
    payload = {
        "customer_id": "C1001",
        "amount": 1200,
        "merchant": "Grocery",
        "location": "Pune",
        "device_id": "DEV001",
        "is_new_device": False,
        "hour": 11,
        "transactions_last_10min": 0
    }
    r = client.post("/api/predict", json=payload)
    d = r.json()
    tx_id = d["transaction_id"]
    assert d["risk_level"] == "LOW"
    
    r2 = client.get("/api/alerts")
    alerts = r2.json()
    matched = [a for a in alerts if a["transaction_id"] == tx_id]
    assert len(matched) == 0, f"LOW risk tx {tx_id} should NOT have an alert"
test("No alert for LOW risk prediction", test_no_alert_for_low_risk)

# ============================================================
# 8. CUSTOMERS ENDPOINT
# ============================================================
print("\n--- 8. GET /api/customers ---")

def test_get_customer_c1001():
    r = client.get("/api/customers/C1001")
    assert r.status_code == 200
    d = r.json()
    assert d["customer_id"] == "C1001"
    assert d["name"] == "Rahul Sharma"
    assert d["avg_amount"] == 2500.0
    assert d["usual_location"] == "Pune"
    assert d["usual_device_id"] == "DEV001"
test("Get customer C1001", test_get_customer_c1001)

def test_get_customer_c1002():
    r = client.get("/api/customers/C1002")
    assert r.status_code == 200
    d = r.json()
    assert d["customer_id"] == "C1002"
test("Get customer C1002", test_get_customer_c1002)

def test_get_customer_not_found():
    r = client.get("/api/customers/C9999")
    assert r.status_code == 404, f"Expected 404, got {r.status_code}: {r.text}"
test("Customer not found (should return 404)", test_get_customer_not_found)

# ============================================================
# 9. CUSTOMER HISTORY ENDPOINT
# ============================================================
print("\n--- 9. GET /api/customers/{id}/history ---")

def test_get_customer_history_c1001():
    r = client.get("/api/customers/C1001/history")
    assert r.status_code == 200, f"Got {r.status_code}: {r.text}"
    d = r.json()
    assert "customer" in d, f"Missing 'customer' field: {d.keys()}"
    assert "transactions" in d
    assert "total_transactions" in d
    assert d["total_transactions"] == len(d["transactions"])
    assert d["customer"]["customer_id"] == "C1001"
test("Customer C1001 history", test_get_customer_history_c1001)

def test_get_customer_history_nonexistent():
    """History for non-existent customer"""
    r = client.get("/api/customers/C_NONEXISTENT/history")
    # Should either return 404 or return empty history gracefully
    assert r.status_code in [200, 404], f"Got {r.status_code}: {r.text}"
test("Customer history for nonexistent customer", test_get_customer_history_nonexistent)

# ============================================================
# 10. FEEDBACK ENDPOINT
# ============================================================
print("\n--- 10. POST /api/feedback ---")

def _create_test_transaction():
    """Helper to create a fresh transaction for feedback tests"""
    payload = {
        "customer_id": "C1001",
        "amount": 30000,
        "merchant": "Test Merchant",
        "location": "Mumbai",
        "device_id": "DEV_FB_TEST",
        "is_new_device": True,
        "hour": 4,
        "transactions_last_10min": 5
    }
    r = client.post("/api/predict", json=payload)
    return r.json()["transaction_id"]

def test_feedback_mark_legitimate():
    tx_id = _create_test_transaction()
    payload = {
        "transaction_id": tx_id,
        "action": "MARK_LEGITIMATE",
        "comment": "Customer confirmed via OTP"
    }
    r = client.post("/api/feedback", json=payload)
    assert r.status_code == 200, f"Got {r.status_code}: {r.text}"
    d = r.json()
    assert d["analyst_action"] == "MARK_LEGITIMATE"
    assert d["investigation_status"] == "CLEARED"
    assert d["label"] == 0  # 0 = legitimate
    
    # Verify original risk score is preserved
    r2 = client.get(f"/api/transactions/{tx_id}")
    tx = r2.json()
    assert tx["investigation_status"] == "CLEARED"
    assert tx["risk_score"] > 0  # Original score preserved
test("Feedback: MARK_LEGITIMATE", test_feedback_mark_legitimate)

def test_feedback_confirm_fraud():
    tx_id = _create_test_transaction()
    payload = {
        "transaction_id": tx_id,
        "action": "CONFIRM_FRAUD",
        "comment": "Confirmed stolen card"
    }
    r = client.post("/api/feedback", json=payload)
    assert r.status_code == 200
    d = r.json()
    assert d["analyst_action"] == "CONFIRM_FRAUD"
    assert d["investigation_status"] == "CONFIRMED_FRAUD"
    assert d["label"] == 1  # 1 = fraud
test("Feedback: CONFIRM_FRAUD", test_feedback_confirm_fraud)

def test_feedback_investigate():
    tx_id = _create_test_transaction()
    payload = {
        "transaction_id": tx_id,
        "action": "INVESTIGATE",
        "comment": "Need more info"
    }
    r = client.post("/api/feedback", json=payload)
    assert r.status_code == 200
    d = r.json()
    assert d["analyst_action"] == "INVESTIGATE"
    assert d["investigation_status"] == "UNDER_INVESTIGATION"
test("Feedback: INVESTIGATE", test_feedback_investigate)

def test_feedback_escalate():
    tx_id = _create_test_transaction()
    payload = {
        "transaction_id": tx_id,
        "action": "ESCALATE",
        "comment": "Suspicious pattern across accounts"
    }
    r = client.post("/api/feedback", json=payload)
    assert r.status_code == 200
    d = r.json()
    assert d["analyst_action"] == "ESCALATE"
    assert d["investigation_status"] == "ESCALATED"
test("Feedback: ESCALATE", test_feedback_escalate)

def test_feedback_nonexistent_transaction():
    payload = {
        "transaction_id": "TX_DOES_NOT_EXIST_999",
        "action": "MARK_LEGITIMATE",
        "comment": "test"
    }
    r = client.post("/api/feedback", json=payload)
    assert r.status_code == 404, f"Expected 404, got {r.status_code}: {r.text}"
test("Feedback on nonexistent transaction (should return 404)", test_feedback_nonexistent_transaction)

def test_feedback_invalid_action():
    tx_id = _create_test_transaction()
    payload = {
        "transaction_id": tx_id,
        "action": "INVALID_ACTION",
        "comment": "test"
    }
    r = client.post("/api/feedback", json=payload)
    # Should either return 422 or handle gracefully
    # If server accepts it, it should fall back to a default status
    assert r.status_code in [200, 422], f"Got {r.status_code}: {r.text}"
test("Feedback: Invalid action", test_feedback_invalid_action)

def test_feedback_missing_action():
    payload = {
        "transaction_id": "TX123"
    }
    r = client.post("/api/feedback", json=payload)
    assert r.status_code == 422
test("Feedback: Missing action (should return 422)", test_feedback_missing_action)

def test_feedback_missing_transaction_id():
    payload = {
        "action": "MARK_LEGITIMATE"
    }
    r = client.post("/api/feedback", json=payload)
    assert r.status_code == 422
test("Feedback: Missing transaction_id (should return 422)", test_feedback_missing_transaction_id)

def test_feedback_no_comment():
    """Comment is optional"""
    tx_id = _create_test_transaction()
    payload = {
        "transaction_id": tx_id,
        "action": "MARK_LEGITIMATE"
    }
    r = client.post("/api/feedback", json=payload)
    assert r.status_code == 200, f"Comment is optional, got {r.status_code}: {r.text}"
test("Feedback: No comment (optional)", test_feedback_no_comment)

def test_feedback_alert_status_update():
    """After MARK_LEGITIMATE, the related alert should be RESOLVED"""
    tx_id = _create_test_transaction()
    
    # Submit feedback
    payload = {
        "transaction_id": tx_id,
        "action": "MARK_LEGITIMATE",
        "comment": "Cleared"
    }
    r = client.post("/api/feedback", json=payload)
    assert r.status_code == 200
    
    # Check alerts for this transaction
    r2 = client.get("/api/alerts")
    alerts = r2.json()
    matched = [a for a in alerts if a["transaction_id"] == tx_id]
    for a in matched:
        assert a["status"] == "RESOLVED", f"Alert status should be RESOLVED, got {a['status']}"
test("Feedback updates alert status to RESOLVED", test_feedback_alert_status_update)

# ============================================================
# 11. METRICS ENDPOINT
# ============================================================
print("\n--- 11. GET /api/metrics ---")

def test_metrics_basic():
    r = client.get("/api/metrics")
    assert r.status_code == 200
    d = r.json()
    required = ["precision", "recall", "f1", "pr_auc", "false_positive_rate",
                 "false_negative_rate", "transaction_count", "high_risk_count",
                 "medium_risk_count", "low_risk_count", "average_risk_score"]
    for f in required:
        assert f in d, f"Missing field '{f}' in metrics response"
test("Metrics basic response", test_metrics_basic)

def test_metrics_values_range():
    r = client.get("/api/metrics")
    d = r.json()
    assert 0.0 <= d["precision"] <= 1.0, f"precision={d['precision']}"
    assert 0.0 <= d["recall"] <= 1.0
    assert 0.0 <= d["f1"] <= 1.0
    assert 0.0 <= d["pr_auc"] <= 1.0
    assert d["transaction_count"] > 0
    assert d["average_risk_score"] >= 0
test("Metrics values in valid ranges", test_metrics_values_range)

def test_metrics_counts_consistent():
    r = client.get("/api/metrics")
    d = r.json()
    total = d["high_risk_count"] + d["medium_risk_count"] + d["low_risk_count"]
    assert total == d["transaction_count"], f"Counts don't add up: {total} != {d['transaction_count']}"
test("Metrics: high+medium+low = total", test_metrics_counts_consistent)

# ============================================================
# 12. CUSTOMER C1002 CROSS-FLOW
# ============================================================
print("\n--- 12. Cross-customer C1002 tests ---")

def test_predict_c1002_normal():
    payload = {
        "customer_id": "C1002",
        "amount": 4000,
        "merchant": "Restaurant",
        "location": "Mumbai",
        "device_id": "DEV002",
        "is_new_device": False,
        "hour": 19,
        "transactions_last_10min": 0
    }
    r = client.post("/api/predict", json=payload)
    assert r.status_code == 200
    d = r.json()
    assert d["risk_level"] == "LOW", f"Expected LOW for C1002 normal, got {d['risk_level']} (score={d['risk_score']})"
test("C1002 normal transaction", test_predict_c1002_normal)

def test_predict_c1002_suspicious():
    payload = {
        "customer_id": "C1002",
        "amount": 90000,
        "merchant": "Wire Transfer",
        "location": "Chennai",
        "device_id": "DEV_HACK",
        "is_new_device": True,
        "hour": 1,
        "transactions_last_10min": 7
    }
    r = client.post("/api/predict", json=payload)
    assert r.status_code == 200
    d = r.json()
    assert d["risk_level"] in ["MEDIUM", "HIGH"], f"Expected MEDIUM/HIGH, got {d['risk_level']}"
test("C1002 suspicious transaction", test_predict_c1002_suspicious)

# ============================================================
# 13. RESPONSE SCHEMA COMPLETENESS
# ============================================================
print("\n--- 13. Response schema verification ---")

def test_predict_response_schema():
    payload = {
        "customer_id": "C1001",
        "amount": 5000,
        "merchant": "Test",
        "location": "Pune",
        "device_id": "DEV001",
        "is_new_device": False,
        "hour": 10,
        "transactions_last_10min": 0
    }
    r = client.post("/api/predict", json=payload)
    d = r.json()
    required = ["transaction_id", "customer_id", "amount", "merchant", "location",
                "device_id", "is_new_device", "fraud_probability", "anomaly_score",
                "risk_score", "risk_level", "decision", "reasons", "top_risk_factors",
                "timestamp"]
    for f in required:
        assert f in d, f"Missing field '{f}' in prediction response"
    
    # Verify types
    assert isinstance(d["fraud_probability"], float)
    assert isinstance(d["anomaly_score"], float)
    assert isinstance(d["risk_score"], (int, float))
    assert isinstance(d["reasons"], list)
    assert isinstance(d["top_risk_factors"], list)
    assert isinstance(d["is_new_device"], bool)
test("Predict response schema completeness", test_predict_response_schema)

def test_predict_top_risk_factors_schema():
    payload = {
        "customer_id": "C1001",
        "amount": 45000,
        "merchant": "Electronics",
        "location": "Mumbai",
        "device_id": "DEV999",
        "is_new_device": True,
        "hour": 3,
        "transactions_last_10min": 8
    }
    r = client.post("/api/predict", json=payload)
    d = r.json()
    assert len(d["top_risk_factors"]) > 0
    for factor in d["top_risk_factors"]:
        assert "feature" in factor
        assert "importance" in factor
        assert "description" in factor
        assert isinstance(factor["importance"], float)
test("top_risk_factors schema", test_predict_top_risk_factors_schema)


# ============================================================
# FINAL SUMMARY
# ============================================================
print("\n" + "=" * 60)
print(f" RESULTS: {PASS} passed, {FAIL} failed")
print("=" * 60)

if ERRORS:
    print("\n FAILURES/ERRORS:")
    for e in ERRORS:
        print(e)
    print()

sys.exit(1 if FAIL > 0 else 0)
