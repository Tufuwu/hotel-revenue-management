from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.model import PricingRecommendation
from app.db.serializers import recommendation_to_dict


async def create_pricing_recommendation(
    session: AsyncSession,
    hotel_id: int,
    recommended_price: float,
    comp_index: float,
    demand_score: float,
    reason: str,
) -> dict:
    recommendation = PricingRecommendation(
        hotel_id=hotel_id,
        recommended_price=recommended_price,
        comp_index=comp_index,
        demand_score=demand_score,
        reason=reason,
    )
    session.add(recommendation)
    await session.commit()
    await session.refresh(recommendation)
    return recommendation_to_dict(recommendation)


async def list_pricing_recommendations(session: AsyncSession, hotel_id: int) -> list[dict]:
    recommendations = (await session.scalars(
        select(PricingRecommendation)
        .where(PricingRecommendation.hotel_id == hotel_id)
        .order_by(PricingRecommendation.created_at.desc())
    )).all()
    return [
        recommendation_to_dict(recommendation)
        for recommendation in recommendations
    ]
