def test_feedback_flow(client):
    # 1. Post a transaction
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
    pred_res = client.post("/api/predict", json=payload)
    tx_id = pred_res.json()["transaction_id"]

    # 2. Submit analyst feedback
    feedback_payload = {
        "transaction_id": tx_id,
        "action": "MARK_LEGITIMATE",
        "comment": "Confirmed with cardholder via OTP verification"
    }
    fb_res = client.post("/api/feedback", json=feedback_payload)
    assert fb_res.status_code == 200
    fb_data = fb_res.json()
    assert fb_data["analyst_action"] == "MARK_LEGITIMATE"
    assert fb_data["investigation_status"] == "CLEARED"

    # 3. Check transaction GET endpoint to verify original risk_score preserved and investigation_status updated
    tx_res = client.get(f"/api/transactions/{tx_id}")
    assert tx_res.status_code == 200
    tx_data = tx_res.json()
    assert tx_data["investigation_status"] == "CLEARED"
    assert tx_data["risk_score"] == pred_res.json()["risk_score"]
