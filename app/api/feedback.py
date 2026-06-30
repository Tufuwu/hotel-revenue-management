from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas import PricingFeedbackRequest, PricingFeedbackResponse
from app.services.feedback import record_pricing_feedback


router = APIRouter()


@router.post("/pricing-feedback", response_model=PricingFeedbackResponse)
def create_feedback(
    payload: PricingFeedbackRequest,
    db: Session = Depends(get_db),
) -> PricingFeedbackResponse:
    feedback = record_pricing_feedback(db, payload)
    if feedback is None:
        raise HTTPException(status_code=404, detail="recommendation not found")
    return feedback
