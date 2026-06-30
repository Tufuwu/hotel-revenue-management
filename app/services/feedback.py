from sqlalchemy.orm import Session

from app.db.feedback import create_pricing_feedback
from app.schemas import PricingFeedbackRequest, PricingFeedbackResponse


def record_pricing_feedback(
    db: Session,
    payload: PricingFeedbackRequest,
) -> PricingFeedbackResponse | None:
    feedback = create_pricing_feedback(
        db,
        recommendation_id=payload.recommendation_id,
        executed_price=payload.executed_price,
        actual_occupancy=payload.actual_occupancy,
        actual_revenue=payload.actual_revenue,
        feedback_note=payload.feedback_note,
    )
    if feedback is None:
        return None
    return PricingFeedbackResponse(**feedback)
