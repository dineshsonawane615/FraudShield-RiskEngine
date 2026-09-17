import os
import sys

# Ensure backend root is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

import json
import datetime
from sqlalchemy.orm import Session
from app.database.database import SessionLocal, engine, Base
from app.models.database_models import Customer, Transaction, Alert, Feedback


def seed_database():
    Base.metadata.create_all(bind=engine)
    db: Session = SessionLocal()

    try:
        # Check if already seeded
        if db.query(Customer).filter(Customer.customer_id == "C1001").first():
            print("[Seed] Customer C1001 already exists in database. Skipping seed.")
            return

        print("[Seed] Seeding database with demo customers and transactions...")

        # 1. Create Demo Customer C1001
        c1001 = Customer(
            customer_id="C1001",
            name="Rahul Sharma",
            avg_amount=2500.0,
            std_amount=500.0,
            usual_location="Pune",
            usual_device_id="DEV001",
            created_at=datetime.datetime.utcnow() - datetime.timedelta(days=30)
        )
        
        # Create Customer C1002
        c1002 = Customer(
            customer_id="C1002",
            name="Anita Patel",
            avg_amount=4500.0,
            std_amount=800.0,
            usual_location="Mumbai",
            usual_device_id="DEV002",
            created_at=datetime.datetime.utcnow() - datetime.timedelta(days=20)
        )

        db.add_all([c1001, c1002])
        db.commit()

        # 2. Add Normal Transactions for Customer C1001
        normal_txs = [
            ("TX1001_1", 1500.0, "Supermarket", "Pune", "DEV001", datetime.time(10, 30)),
            ("TX1001_2", 2200.0, "Dining", "Pune", "DEV001", datetime.time(14, 15)),
            ("TX1001_3", 3100.0, "Electronics", "Pune", "DEV001", datetime.time(18, 45)),
            ("TX1001_4", 2700.0, "Apparel", "Pune", "DEV001", datetime.time(20, 10)),
        ]

        now = datetime.datetime.utcnow()
        for idx, (tx_id, amt, merch, loc, dev, t_time) in enumerate(normal_txs):
            tx_datetime = datetime.datetime.combine(now.date() - datetime.timedelta(days=4-idx), t_time)
            tx = Transaction(
                transaction_id=tx_id,
                customer_id="C1001",
                amount=amt,
                merchant=merch,
                location=loc,
                device_id=dev,
                timestamp=tx_datetime,
                is_new_device=False,
                transactions_last_10min=0,
                transactions_last_1hour=1,
                transactions_last_24hours=3,
                hour=t_time.hour,
                day_of_week=tx_datetime.weekday(),
                fraud_probability=0.02,
                anomaly_score=0.05,
                risk_score=12.0,
                risk_level="LOW",
                decision="PROCEED",
                investigation_status="UNASSIGNED",
                reasons_json=json.dumps(["Transaction matches normal customer behavior profile"]),
                created_at=tx_datetime
            )
            db.add(tx)

        # 3. Add Suspicious Demo Transaction for Customer C1001
        suspicious_tx_id = "TX_DEMO_SUSPICIOUS_999"
        susp_time = datetime.datetime.combine(now.date(), datetime.time(3, 15))
        susp_tx = Transaction(
            transaction_id=suspicious_tx_id,
            customer_id="C1001",
            amount=45000.0,
            merchant="Luxury Electronics Store",
            location="Mumbai",
            device_id="DEV999",
            timestamp=susp_time,
            is_new_device=True,
            transactions_last_10min=8,
            transactions_last_1hour=12,
            transactions_last_24hours=15,
            hour=3,
            day_of_week=susp_time.weekday(),
            fraud_probability=0.91,
            anomaly_score=0.87,
            risk_score=94.0,
            risk_level="HIGH",
            decision="ALERT",
            investigation_status="UNASSIGNED",
            reasons_json=json.dumps([
                "Transaction amount is significantly above customer baseline",
                "New device detected",
                "Unusual transaction time",
                "High transaction velocity",
                "Unusual location"
            ]),
            created_at=susp_time
        )
        db.add(susp_tx)
        db.commit()

        # 4. Create Alert for Suspicious Demo Transaction
        demo_alert = Alert(
            transaction_id=suspicious_tx_id,
            customer_id="C1001",
            risk_score=94.0,
            risk_level="HIGH",
            status="OPEN",
            created_at=susp_time
        )
        db.add(demo_alert)
        db.commit()

        print(f"[Seed] Successfully seeded Customer C1001 and demo transactions (including {suspicious_tx_id} -> HIGH / ALERT).")

    except Exception as e:
        db.rollback()
        print(f"[Seed] Error seeding database: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    seed_database()
