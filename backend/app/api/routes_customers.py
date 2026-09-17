import json
import datetime
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database.database import get_db
from app.models.database_models import Customer, Transaction
from app.models.schemas import CustomerResponse, CustomerHistoryResponse, TransactionResponse

router = APIRouter(prefix="/customers", tags=["Customers"])

def _format_tx(tx: Transaction) -> TransactionResponse:
    reasons = []
    if tx.reasons_json:
        try:
            reasons = json.loads(tx.reasons_json)
        except Exception:
            reasons = [tx.reasons_json]

    return TransactionResponse(
        id=tx.id,
        transaction_id=tx.transaction_id,
        customer_id=tx.customer_id,
        amount=tx.amount,
        merchant=tx.merchant,
        location=tx.location,
        device_id=tx.device_id,
        timestamp=tx.timestamp,
        is_new_device=tx.is_new_device,
        transactions_last_10min=tx.transactions_last_10min,
        fraud_probability=tx.fraud_probability,
        anomaly_score=tx.anomaly_score,
        risk_score=tx.risk_score,
        risk_level=tx.risk_level,
        decision=tx.decision,
        investigation_status=tx.investigation_status,
        reasons=reasons,
        created_at=tx.created_at
    )

@router.get("/{customer_id}", response_model=CustomerResponse)
def get_customer(customer_id: str, db: Session = Depends(get_db)):
    customer = db.query(Customer).filter(Customer.customer_id == customer_id).first()
    if not customer:
        raise HTTPException(status_code=404, detail=f"Customer with ID '{customer_id}' not found.")
    return customer

@router.get("/{customer_id}/history", response_model=CustomerHistoryResponse)
def get_customer_history(customer_id: str, db: Session = Depends(get_db)):
    customer = db.query(Customer).filter(Customer.customer_id == customer_id).first()
    
    txs = db.query(Transaction).filter(
        Transaction.customer_id == customer_id
    ).order_by(Transaction.created_at.desc()).all()
    
    if not customer:
        # Generate on-the-fly virtual customer response for unknown customer
        customer_resp = CustomerResponse(
            id=0,
            customer_id=customer_id,
            name=f"Customer {customer_id}",
            avg_amount=2500.0,
            std_amount=500.0,
            usual_location="Unknown",
            usual_device_id="UNKNOWN",
            created_at=datetime.datetime.utcnow()
        )
        return CustomerHistoryResponse(
            customer=customer_resp,
            total_transactions=len(txs),
            transactions=[_format_tx(t) for t in txs]
        )

    return CustomerHistoryResponse(
        customer=CustomerResponse.model_validate(customer, from_attributes=True),
        total_transactions=len(txs),
        transactions=[_format_tx(t) for t in txs]
    )

