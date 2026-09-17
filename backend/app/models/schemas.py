from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
import datetime

# --- Prediction Schemas ---

class PredictionInput(BaseModel):
    customer_id: str = Field(..., example="C1001", description="ID of the customer", max_length=64)
    amount: float = Field(..., example=45000.0, gt=0, le=10_000_000, description="Transaction amount")
    merchant: Optional[str] = Field("Electronics", example="Electronics", max_length=128)
    location: Optional[str] = Field("Mumbai", example="Mumbai", max_length=128)
    device_id: Optional[str] = Field("DEV999", example="DEV999", max_length=64)
    is_new_device: Optional[bool] = Field(True, description="Whether device is new to customer")
    hour: Optional[int] = Field(3, ge=0, le=23, description="Hour of the day (0-23)")
    day_of_week: Optional[int] = Field(None, ge=0, le=6, description="Day of week (0=Mon, 6=Sun)")
    transactions_last_10min: Optional[int] = Field(8, ge=0, le=1000, description="Transactions count in last 10 minutes")
    transactions_last_1hour: Optional[int] = Field(None, ge=0, le=10000, description="Transactions count in last 1 hour")
    transactions_last_24hours: Optional[int] = Field(None, ge=0, le=100000, description="Transactions count in last 24 hours")

class FeatureContribution(BaseModel):
    feature: str
    importance: float
    description: str

class PredictionOutput(BaseModel):
    transaction_id: str
    customer_id: str
    amount: float
    merchant: str
    location: str
    device_id: str
    is_new_device: bool
    fraud_probability: float
    anomaly_score: float
    risk_score: float
    risk_level: str  # LOW, MEDIUM, HIGH
    decision: str    # PROCEED, REVIEW, ALERT
    reasons: List[str]
    top_risk_factors: List[FeatureContribution] = []
    shap_values: Optional[Dict[str, float]] = None
    timestamp: datetime.datetime

# --- Transaction Schemas ---

class TransactionResponse(BaseModel):
    id: int
    transaction_id: str
    customer_id: str
    amount: float
    merchant: str
    location: str
    device_id: str
    timestamp: datetime.datetime
    is_new_device: bool
    transactions_last_10min: int
    fraud_probability: float
    anomaly_score: float
    risk_score: float
    risk_level: str
    decision: str
    investigation_status: str
    reasons: List[str] = []
    created_at: datetime.datetime

    class Config:
        from_attributes = True

# --- Alert Schemas ---

class AlertResponse(BaseModel):
    id: int
    transaction_id: str
    customer_id: str
    risk_score: float
    risk_level: str
    status: str
    created_at: datetime.datetime

    class Config:
        from_attributes = True

# --- Customer Schemas ---

class CustomerResponse(BaseModel):
    id: int
    customer_id: str
    name: str
    avg_amount: float
    std_amount: float
    usual_location: str
    usual_device_id: str
    created_at: datetime.datetime

    class Config:
        from_attributes = True

class CustomerHistoryResponse(BaseModel):
    customer: CustomerResponse
    total_transactions: int
    transactions: List[TransactionResponse]

# --- Feedback Schemas ---

class FeedbackInput(BaseModel):
    transaction_id: str = Field(..., example="TX123", max_length=64)
    action: str = Field(..., example="MARK_LEGITIMATE", description="Action: INVESTIGATE, MARK_LEGITIMATE, CONFIRM_FRAUD, ESCALATE", max_length=32)
    comment: Optional[str] = Field(None, example="Customer confirmed transaction via phone verification", max_length=1024)

class FeedbackResponse(BaseModel):
    id: int
    transaction_id: str
    analyst_action: str
    label: Optional[int]
    comment: Optional[str]
    investigation_status: str
    created_at: datetime.datetime

    class Config:
        from_attributes = True

# --- Metrics Schemas ---

class MetricsResponse(BaseModel):
    precision: float
    recall: float
    f1: float
    pr_auc: float
    false_positive_rate: float
    false_negative_rate: float
    transaction_count: int
    high_risk_count: int
    medium_risk_count: int
    low_risk_count: int
    average_risk_score: float
