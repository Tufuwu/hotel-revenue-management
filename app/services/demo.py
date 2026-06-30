from sqlalchemy.ext.asyncio import AsyncSession

from app.db.feedback import create_pricing_feedback
from app.schemas import PricingFeedbackResponse, SimulatePricingCycleResponse
from app.services.recommendations import predict_hotel_price


async def simulate_pricing_cycle(
    db: AsyncSession,
    hotel_id: int,
) -> SimulatePricingCycleResponse | None:
    prediction = await predict_hotel_price(db, hotel_id)
    if prediction is None:
        return None

    simulated_occupancy = simulate_actual_occupancy(prediction.decision)
    simulated_revenue = round(
        prediction.recommended_price * simulated_occupancy,
        2,
    )
    feedback = await create_pricing_feedback(
        db,
        recommendation_id=prediction.recommendation_id,
        executed_price=prediction.recommended_price,
        actual_occupancy=simulated_occupancy,
        actual_revenue=simulated_revenue,
        feedback_note="demo simulated pricing cycle",
    )
    if feedback is None:
        return None
    return SimulatePricingCycleResponse(
        prediction=prediction,
        feedback=PricingFeedbackResponse(**feedback),
    )


def simulate_actual_occupancy(decision: str) -> float:
    if decision == "raise_price":
        return 82.0
    if decision == "lower_price":
        return 58.0
    return 72.0
