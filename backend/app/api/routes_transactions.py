import json
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.database.database import get_db
from app.models.database_models import Transaction
from app.models.schemas import TransactionResponse

router = APIRouter(prefix="/transactions", tags=["Transactions"])

def _format_transaction(tx: Transaction) -> TransactionResponse:
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

@router.get("", response_model=List[TransactionResponse])
def get_transactions(
    risk_level: Optional[str] = Query(None, description="Filter by risk level (LOW, MEDIUM, HIGH)"),
    decision: Optional[str] = Query(None, description="Filter by decision (PROCEED, REVIEW, ALERT)"),
    customer_id: Optional[str] = Query(None, description="Filter by customer ID"),
    limit: int = Query(50, ge=1, le=500, description="Max transactions to return"),
    db: Session = Depends(get_db)
):
    query = db.query(Transaction)
    if risk_level:
        query = query.filter(Transaction.risk_level == risk_level.upper())
    if decision:
        query = query.filter(Transaction.decision == decision.upper())
    if customer_id:
        query = query.filter(Transaction.customer_id == customer_id)

    txs = query.order_by(Transaction.created_at.desc()).limit(limit).all()
    return [_format_transaction(tx) for tx in txs]

@router.get("/{transaction_id}", response_model=TransactionResponse)
def get_transaction_by_id(transaction_id: str, db: Session = Depends(get_db)):
    tx = db.query(Transaction).filter(Transaction.transaction_id == transaction_id).first()
    if not tx:
        raise HTTPException(status_code=404, detail=f"Transaction with ID '{transaction_id}' not found.")
    return _format_transaction(tx)
