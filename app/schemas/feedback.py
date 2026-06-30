from datetime import datetime

from pydantic import BaseModel, Field


class PricingFeedbackRequest(BaseModel):
    recommendation_id: int = Field(gt=0)
    executed_price: float = Field(gt=0)
    actual_occupancy: float = Field(ge=0, le=100)
    actual_revenue: float = Field(ge=0)
    feedback_note: str | None = None


class PricingFeedbackResponse(BaseModel):
    id: int
    recommendation_id: int
    executed_price: float
    actual_occupancy: float
    actual_revenue: float
    feedback_note: str | None = None
    created_at: datetime
