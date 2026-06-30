from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

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
def predict_price(
    payload: PricePredictionRequest,
    db: Session = Depends(get_db),
) -> PricePredictionResponse:
    prediction = predict_hotel_price(db, payload.hotel_id)
    if prediction is None:
        raise HTTPException(status_code=404, detail="hotel not found")
    return prediction


@router.get(
    "/hotels/{hotel_id}/recommendations",
    response_model=list[PricingRecommendationResponse],
)
def get_recommendations(
    hotel_id: int,
    db: Session = Depends(get_db),
) -> list[PricingRecommendationResponse]:
    recommendations = get_hotel_recommendations(db, hotel_id)
    if recommendations is None:
        raise HTTPException(status_code=404, detail="hotel not found")
    return recommendations
