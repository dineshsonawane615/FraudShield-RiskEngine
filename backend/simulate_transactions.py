import time
import random
import requests
import argparse

API_URL = "http://127.0.0.1:8000/api/predict"

NORMAL_TRANSACTIONS = [
    {"customer_id": "C1001", "amount": 1450.0, "merchant": "Grocery Hub", "location": "Pune", "device_id": "DEV001", "is_new_device": False, "hour": 10, "transactions_last_10min": 0},
    {"customer_id": "C1001", "amount": 2300.0, "merchant": "Cafe Coffee Day", "location": "Pune", "device_id": "DEV001", "is_new_device": False, "hour": 14, "transactions_last_10min": 1},
    {"customer_id": "C1001", "amount": 3100.0, "merchant": "Bookstore", "location": "Pune", "device_id": "DEV001", "is_new_device": False, "hour": 17, "transactions_last_10min": 0},
    {"customer_id": "C1002", "amount": 4200.0, "merchant": "Supermarket", "location": "Mumbai", "device_id": "DEV002", "is_new_device": False, "hour": 11, "transactions_last_10min": 0},
    {"customer_id": "C1002", "amount": 2800.0, "merchant": "Fuel Station", "location": "Mumbai", "device_id": "DEV002", "is_new_device": False, "hour": 19, "transactions_last_10min": 0},
]

SUSPICIOUS_TRANSACTIONS = [
    {"customer_id": "C1001", "amount": 48500.0, "merchant": "Luxury Watch Store", "location": "Mumbai", "device_id": "DEV999", "is_new_device": True, "hour": 3, "transactions_last_10min": 7},
    {"customer_id": "C1001", "amount": 62000.0, "merchant": "Crypto Exchange Vendor", "location": "Delhi", "device_id": "DEV888", "is_new_device": True, "hour": 2, "transactions_last_10min": 9},
    {"customer_id": "C1002", "amount": 95000.0, "merchant": "Jewelry Emporium", "location": "Bangalore", "device_id": "DEV777", "is_new_device": True, "hour": 4, "transactions_last_10min": 6},
]

def run_simulation(count: int = 10, delay: float = 1.0):
    print("==================================================")
    print(" FraudShield AI — Real-Time Transaction Simulator ")
    print("==================================================")
    print(f"Target API Endpoint: {API_URL}")
    print(f"Simulating {count} transactions with {delay}s delay...\n")

    for i in range(1, count + 1):
        # 20% chance of generating a suspicious transaction
        is_suspicious = random.random() < 0.25
        payload = random.choice(SUSPICIOUS_TRANSACTIONS) if is_suspicious else random.choice(NORMAL_TRANSACTIONS)

        print(f"[{i}/{count}] Sending {'SUSPICIOUS' if is_suspicious else 'NORMAL'} transaction...")
        print(f"      Customer: {payload['customer_id']} | Amount: ₹{payload['amount']:,.2f} | Location: {payload['location']} | Device: {payload['device_id']}")

        try:
            res = requests.post(API_URL, json=payload, timeout=5)
            if res.status_code == 200:
                data = res.json()
                print(f"      -> Response: Risk Score: {data['risk_score']} | Level: {data['risk_level']} | Decision: {data['decision']}")
                if data['reasons']:
                    print(f"      -> Reasons: {', '.join(data['reasons'])}")
            else:
                print(f"      -> HTTP Error {res.status_code}: {res.text}")
        except Exception as e:
            print(f"      -> Connection Error: {e}")

        print("-" * 60)
        time.sleep(delay)

    print("\nSimulation completed successfully!")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Transaction Simulator for FraudShield AI Dashboard")
    parser.add_argument("--count", type=int, default=10, help="Number of transactions to simulate")
    parser.add_argument("--delay", type=float, default=1.0, help="Delay between transactions in seconds")
    args = parser.parse_args()

    run_simulation(count=args.count, delay=args.delay)
