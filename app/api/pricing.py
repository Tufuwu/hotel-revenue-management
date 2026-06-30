from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.schemas import (
    PricePredictionRequest,
    PricePredictionResponse,
    PricingRecommendationResponse,
)
from app.services.recommendations import (
    get_hotel_recommendations,
    predict_hotel_price,
)


router = APIRouter()


@router.post("/predict-price", response_model=PricePredictionResponse)
async def predict_price(
    payload: PricePredictionRequest,
    db: AsyncSession = Depends(get_db),
) -> PricePredictionResponse:
    prediction = await predict_hotel_price(db, payload.hotel_id)
    if prediction is None:
        raise HTTPException(status_code=404, detail="hotel not found")
    return prediction


@router.get(
    "/hotels/{hotel_id}/recommendations",
    response_model=list[PricingRecommendationResponse],
)
async def get_recommendations(
    hotel_id: int,
    db: AsyncSession = Depends(get_db),
) -> list[PricingRecommendationResponse]:
    recommendations = await get_hotel_recommendations(db, hotel_id)
    if recommendations is None:
        raise HTTPException(status_code=404, detail="hotel not found")
    return recommendations
