from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.model import PricingRecommendation
from app.db.serializers import recommendation_to_dict


def create_pricing_recommendation(
    session: Session,
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
    session.commit()
    session.refresh(recommendation)
    return recommendation_to_dict(recommendation)


def list_pricing_recommendations(session: Session, hotel_id: int) -> list[dict]:
    recommendations = session.scalars(
        select(PricingRecommendation)
        .where(PricingRecommendation.hotel_id == hotel_id)
        .order_by(PricingRecommendation.created_at.desc())
    ).all()
    return [
        recommendation_to_dict(recommendation)
        for recommendation in recommendations
    ]
