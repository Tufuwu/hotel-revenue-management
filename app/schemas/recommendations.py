from datetime import datetime

from pydantic import BaseModel, Field


class PricePredictionRequest(BaseModel):
    hotel_id: int = Field(gt=0)


class PricePredictionResponse(BaseModel):
    recommendation_id: int
    hotel_id: int
    room_type: str
    base_price: float
    occupancy: float
    latitude: float
    longitude: float
    competitor_prices: list[float]
    min_price: float
    max_price: float | None = None
    recommended_price: float
    comp_index: float
    demand_score: float
    learning_adjustment_factor: float
    feedback_count: int
    decision: str
    reason: str


class PricingRecommendationResponse(BaseModel):
    id: int
    hotel_id: int
    recommended_price: float
    comp_index: float
    demand_score: float
    reason: str
    created_at: datetime
