from pydantic import BaseModel, Field

from app.schemas.feedback import PricingFeedbackResponse
from app.schemas.recommendations import PricePredictionResponse


class SimulatePricingCycleRequest(BaseModel):
    hotel_id: int = Field(gt=0)


class SimulatePricingCycleResponse(BaseModel):
    prediction: PricePredictionResponse
    feedback: PricingFeedbackResponse
