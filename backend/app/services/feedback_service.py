from sqlalchemy.orm import Session
from app.models.database_models import Transaction, Feedback, Alert
from app.models.schemas import FeedbackInput, FeedbackResponse
import datetime

ACTION_TO_STATUS_MAP = {
    "INVESTIGATE": "UNDER_INVESTIGATION",
    "MARK_LEGITIMATE": "CLEARED",
    "CONFIRM_FRAUD": "CONFIRMED_FRAUD",
    "ESCALATE": "ESCALATED"
}

ACTION_TO_LABEL_MAP = {
    "MARK_LEGITIMATE": 0,
    "CONFIRM_FRAUD": 1,
    "INVESTIGATE": None,
    "ESCALATE": 1
}

def process_analyst_feedback(payload: FeedbackInput, db: Session) -> FeedbackResponse:
    """
    Stores analyst feedback and updates investigation status without altering historical risk scores.
    """
    # 1. Fetch transaction
    tx = db.query(Transaction).filter(Transaction.transaction_id == payload.transaction_id).first()
    if not tx:
        raise ValueError(f"Transaction with ID '{payload.transaction_id}' not found.")

    new_status = ACTION_TO_STATUS_MAP.get(payload.action.upper(), "UNDER_INVESTIGATION")
    label = ACTION_TO_LABEL_MAP.get(payload.action.upper(), None)

    # 2. Update transaction investigation status ONLY (preserve risk_score, risk_level, decision)
    tx.investigation_status = new_status

    # 3. Update alert status if alert exists for this transaction
    alert = db.query(Alert).filter(Alert.transaction_id == payload.transaction_id).first()
    if alert:
        if new_status == "CLEARED" or new_status == "CONFIRMED_FRAUD":
            alert.status = "RESOLVED"
        elif new_status == "UNDER_INVESTIGATION":
            alert.status = "UNDER_REVIEW"

    # 4. Create feedback record
    feedback = Feedback(
        transaction_id=payload.transaction_id,
        analyst_action=payload.action.upper(),
        label=label,
        comment=payload.comment,
        created_at=datetime.datetime.utcnow()
    )
    db.add(feedback)
    db.commit()
    db.refresh(feedback)
    db.refresh(tx)

    return FeedbackResponse(
        id=feedback.id,
        transaction_id=feedback.transaction_id,
        analyst_action=feedback.analyst_action,
        label=feedback.label,
        comment=feedback.comment,
        investigation_status=tx.investigation_status,
        created_at=feedback.created_at
    )

def export_feedback_retraining_buffer(db: Session):
    """
    Service helper function illustrating how feedback labels can be extracted for periodic retraining.
    """
    feedbacks = db.query(Feedback).filter(Feedback.label.isnot(None)).all()
    labeled_samples = []
    for fb in feedbacks:
        labeled_samples.append({
            "transaction_id": fb.transaction_id,
            "label": fb.label,
            "analyst_action": fb.analyst_action,
            "comment": fb.comment,
            "created_at": fb.created_at
        })
    return labeled_samples
