from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.db.model import PricingFeedback, PricingRecommendation
from app.db.serializers import feedback_to_dict


async def list_pricing_feedback_for_hotel(session: AsyncSession, hotel_id: int) -> list[dict]:
    feedback_rows = (await session.scalars(
        select(PricingFeedback)
        .options(selectinload(PricingFeedback.recommendation))
        .join(PricingRecommendation)
        .where(PricingRecommendation.hotel_id == hotel_id)
        .order_by(PricingFeedback.created_at.desc())
    )).all()
    return [
        {
            **feedback_to_dict(feedback),
            "recommended_price": feedback.recommendation.recommended_price,
        }
        for feedback in feedback_rows
    ]


async def create_pricing_feedback(
    session: AsyncSession,
    recommendation_id: int,
    executed_price: float,
    actual_occupancy: float,
    actual_revenue: float,
    feedback_note: str | None = None,
) -> dict | None:
    recommendation = await session.get(PricingRecommendation, recommendation_id)
    if recommendation is None:
        return None

    feedback = await session.scalar(
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
    await session.commit()
    await session.refresh(feedback)
    return feedback_to_dict(feedback)
