from sqlalchemy.orm import Session

from app.core.pricing import compute_comp_index, compute_demand_score, recommend_price
from app.db.feedback import list_pricing_feedback_for_hotel
from app.db.hotels import get_hotel_pricing_input
from app.db.recommendations import (
    create_pricing_recommendation,
    list_pricing_recommendations,
)
from app.schemas import (
    HotelPricingInput,
    PricePredictionResponse,
    PricingRecommendationResponse,
)
from app.services.learning import (
    apply_learning_adjustment,
    compute_learning_adjustment,
)


def predict_hotel_price(db: Session, hotel_id: int) -> PricePredictionResponse | None:
    pricing_input = get_hotel_pricing_input(db, hotel_id)
    if pricing_input is None:
        return None

    hotel = HotelPricingInput(**pricing_input)
    comp_index = compute_comp_index(hotel.competitor_prices)
    demand_score = compute_demand_score(
        hotel.base_price,
        comp_index,
        hotel.occupancy,
    )
    rule_price = recommend_price(
        hotel.base_price,
        comp_index,
        hotel.occupancy,
        min_price=hotel.min_price,
        max_price=hotel.max_price,
    )
    feedback_history = list_pricing_feedback_for_hotel(db, hotel.hotel_id)
    learning_adjustment_factor = compute_learning_adjustment(feedback_history)
    recommended_price = apply_learning_adjustment(
        rule_price,
        learning_adjustment_factor,
        hotel.min_price,
        hotel.max_price,
    )
    decision = get_pricing_decision(recommended_price, hotel.base_price)
    reason = build_pricing_reason(
        decision,
        hotel.base_price,
        hotel.min_price,
        hotel.max_price,
        comp_index,
        hotel.occupancy,
        learning_adjustment_factor,
        len(feedback_history),
    )
    recommendation = create_pricing_recommendation(
        db,
        hotel_id=hotel.hotel_id,
        recommended_price=round(recommended_price, 2),
        comp_index=round(comp_index, 2),
        demand_score=round(demand_score, 2),
        reason=reason,
    )

    return PricePredictionResponse(
        recommendation_id=recommendation["id"],
        hotel_id=hotel.hotel_id,
        room_type=hotel.room_type,
        base_price=round(hotel.base_price, 2),
        occupancy=round(hotel.occupancy, 2),
        latitude=hotel.latitude,
        longitude=hotel.longitude,
        competitor_prices=[round(price, 2) for price in hotel.competitor_prices],
        min_price=round(hotel.min_price, 2),
        max_price=round(hotel.max_price, 2) if hotel.max_price else None,
        recommended_price=round(recommended_price, 2),
        comp_index=round(comp_index, 2),
        demand_score=round(demand_score, 2),
        learning_adjustment_factor=round(learning_adjustment_factor, 4),
        feedback_count=len(feedback_history),
        decision=decision,
        reason=reason,
    )


def get_hotel_recommendations(
    db: Session,
    hotel_id: int,
) -> list[PricingRecommendationResponse] | None:
    if get_hotel_pricing_input(db, hotel_id) is None:
        return None
    return [
        PricingRecommendationResponse(**recommendation)
        for recommendation in list_pricing_recommendations(db, hotel_id)
    ]


def get_pricing_decision(recommended_price: float, base_price: float) -> str:
    if recommended_price > base_price * 1.02:
        return "raise_price"
    if recommended_price < base_price * 0.98:
        return "lower_price"
    return "keep_price"


def build_pricing_reason(
    decision: str,
    base_price: float,
    min_price: float,
    max_price: float | None,
    comp_index: float,
    occupancy: float,
    learning_adjustment_factor: float,
    feedback_count: int,
) -> str:
    parts = [
        f"decision={decision}",
        f"base_price={base_price:.2f}",
        f"comp_index={comp_index:.2f}",
        f"occupancy={occupancy:.1f}%",
        f"min_price={min_price:.2f}",
        f"learning_adjustment={learning_adjustment_factor:.2%}",
        f"feedback_count={feedback_count}",
    ]
    if max_price is not None:
        parts.append(f"max_price={max_price:.2f}")
    return "; ".join(parts)
