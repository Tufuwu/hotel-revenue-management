from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.model import PricingFeedback, PricingRecommendation
from app.db.serializers import feedback_to_dict


def list_pricing_feedback_for_hotel(session: Session, hotel_id: int) -> list[dict]:
    feedback_rows = session.scalars(
        select(PricingFeedback)
        .join(PricingRecommendation)
        .where(PricingRecommendation.hotel_id == hotel_id)
        .order_by(PricingFeedback.created_at.desc())
    ).all()
    return [
        {
            **feedback_to_dict(feedback),
            "recommended_price": feedback.recommendation.recommended_price,
        }
        for feedback in feedback_rows
    ]


def create_pricing_feedback(
    session: Session,
    recommendation_id: int,
    executed_price: float,
    actual_occupancy: float,
    actual_revenue: float,
    feedback_note: str | None = None,
) -> dict | None:
    recommendation = session.get(PricingRecommendation, recommendation_id)
    if recommendation is None:
        return None

    feedback = session.scalar(
        select(PricingFeedback).where(
            PricingFeedback.recommendation_id == recommendation_id
        )
    )
    if feedback is None:
        feedback = PricingFeedback(recommendation_id=recommendation_id)
        session.add(feedback)

    feedback.executed_price = executed_price
    feedback.actual_occupancy = actual_occupancy
    feedback.actual_revenue = actual_revenue
    feedback.feedback_note = feedback_note
    session.commit()
    session.refresh(feedback)
    return feedback_to_dict(feedback)
