def test_predict_endpoint_suspicious(client):
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
    response = client.post("/api/predict", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "transaction_id" in data
    assert data["risk_level"] in ["MEDIUM", "HIGH"]
    assert len(data["reasons"]) > 0

def test_predict_endpoint_normal(client):
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
    response = client.post("/api/predict", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["risk_level"] == "LOW"
    assert data["decision"] == "PROCEED"
