from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database.database import get_db
from app.models.schemas import FeedbackInput, FeedbackResponse
from app.services.feedback_service import process_analyst_feedback

router = APIRouter(prefix="/feedback", tags=["Feedback"])

@router.post("", response_model=FeedbackResponse)
def submit_feedback(payload: FeedbackInput, db: Session = Depends(get_db)):
    """
    Submits analyst action (INVESTIGATE, MARK_LEGITIMATE, CONFIRM_FRAUD, ESCALATE) 
    and updates investigation status without changing original model risk scores.
    """
    try:
        response = process_analyst_feedback(payload, db)
        return response
    except ValueError as ve:
        raise HTTPException(status_code=404, detail=str(ve))
    except Exception as e:
        import logging
        logging.getLogger(__name__).exception("Feedback submission error")
        raise HTTPException(status_code=500, detail="An internal error occurred during feedback submission.")
