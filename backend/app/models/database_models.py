import datetime
from sqlalchemy import Column, Integer, Float, String, Boolean, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from app.database.database import Base

class Customer(Base):
    __tablename__ = "customers"

    id = Column(Integer, primary_key=True, index=True)
    customer_id = Column(String, unique=True, index=True, nullable=False)
    name = Column(String, nullable=False, default="Standard Customer")
    avg_amount = Column(Float, nullable=False, default=2500.0)
    std_amount = Column(Float, nullable=False, default=500.0)
    usual_location = Column(String, nullable=False, default="Pune")
    usual_device_id = Column(String, nullable=False, default="DEV001")
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    transactions = relationship("Transaction", back_populates="customer")

class Transaction(Base):
    __tablename__ = "transactions"

    id = Column(Integer, primary_key=True, index=True)
    transaction_id = Column(String, unique=True, index=True, nullable=False)
    customer_id = Column(String, ForeignKey("customers.customer_id"), index=True, nullable=False)
    amount = Column(Float, nullable=False)
    merchant = Column(String, nullable=False, default="General Merchant")
    location = Column(String, nullable=False, default="Unknown")
    device_id = Column(String, nullable=False, default="UNKNOWN")
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)
    is_new_device = Column(Boolean, default=False)
    
    # Behavioral features snapshot
    transactions_last_10min = Column(Integer, default=0)
    transactions_last_1hour = Column(Integer, default=0)
    transactions_last_24hours = Column(Integer, default=0)
    hour = Column(Integer, default=12)
    day_of_week = Column(Integer, default=0)
    
    # ML & Risk Outputs
    fraud_probability = Column(Float, nullable=False, default=0.0)
    anomaly_score = Column(Float, nullable=False, default=0.0)
    risk_score = Column(Float, nullable=False, default=0.0)
    risk_level = Column(String, nullable=False, default="LOW")
    decision = Column(String, nullable=False, default="PROCEED")
    
    # Analyst status (separate from risk_level)
    investigation_status = Column(String, nullable=False, default="UNASSIGNED")
    reasons_json = Column(Text, nullable=True, default="[]")
    
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    customer = relationship("Customer", back_populates="transactions")
    alerts = relationship("Alert", back_populates="transaction")
    feedbacks = relationship("Feedback", back_populates="transaction")

class Alert(Base):
    __tablename__ = "alerts"

    id = Column(Integer, primary_key=True, index=True)
    transaction_id = Column(String, ForeignKey("transactions.transaction_id"), index=True, nullable=False)
    customer_id = Column(String, index=True, nullable=False)
    risk_score = Column(Float, nullable=False)
    risk_level = Column(String, nullable=False)
    status = Column(String, nullable=False, default="OPEN") # OPEN, UNDER_REVIEW, RESOLVED
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    transaction = relationship("Transaction", back_populates="alerts")

class Feedback(Base):
    __tablename__ = "feedbacks"

    id = Column(Integer, primary_key=True, index=True)
    transaction_id = Column(String, ForeignKey("transactions.transaction_id"), index=True, nullable=False)
    analyst_action = Column(String, nullable=False) # INVESTIGATE, MARK_LEGITIMATE, CONFIRM_FRAUD, ESCALATE
    label = Column(Integer, nullable=True) # 0 for legit, 1 for fraud
    comment = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    transaction = relationship("Transaction", back_populates="feedbacks")
