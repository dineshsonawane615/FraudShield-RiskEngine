import os
import json
from fastapi import APIRouter, Depends
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.config import settings
from app.database.database import get_db
from app.models.database_models import Transaction
from app.models.schemas import MetricsResponse

router = APIRouter(prefix="/metrics", tags=["Metrics"])

@router.get("", response_model=MetricsResponse)
def get_metrics(db: Session = Depends(get_db)):
    """
    Returns model evaluation metrics (Precision, Recall, F1, PR-AUC, FPR, FNR) 
    and live transaction risk statistics.
    """
    # 1. Load trained model metrics from JSON file
    metrics_path = settings.METRICS_PATH
    precision, recall, f1, pr_auc, fpr, fnr = 0.0, 0.0, 0.0, 0.0, 0.0, 0.0

    if os.path.exists(metrics_path):
        try:
            with open(metrics_path, "r") as f:
                data = json.load(f)
                precision = float(data.get("precision", 0.0))
                recall = float(data.get("recall", 0.0))
                f1 = float(data.get("f1", 0.0))
                pr_auc = float(data.get("pr_auc", 0.0))
                fpr = float(data.get("false_positive_rate", 0.0))
                fnr = float(data.get("false_negative_rate", 0.0))
        except Exception as e:
            print(f"[Metrics] Error reading metrics file: {e}")

    # 2. Live database transaction metrics
    total_txs = db.query(Transaction).count()
    high_count = db.query(Transaction).filter(Transaction.risk_level == "HIGH").count()
    medium_count = db.query(Transaction).filter(Transaction.risk_level == "MEDIUM").count()
    low_count = db.query(Transaction).filter(Transaction.risk_level == "LOW").count()

    avg_score_res = db.query(func.avg(Transaction.risk_score)).scalar()
    avg_score = float(round(avg_score_res, 2)) if avg_score_res is not None else 0.0

    return MetricsResponse(
        precision=precision,
        recall=recall,
        f1=f1,
        pr_auc=pr_auc,
        false_positive_rate=fpr,
        false_negative_rate=fnr,
        transaction_count=total_txs,
        high_risk_count=high_count,
        medium_risk_count=medium_count,
        low_risk_count=low_count,
        average_risk_score=avg_score
    )
