from datetime import date

from pydantic import BaseModel, Field


class DailyMetricRequest(BaseModel):
    metric_date: date
    occupancy: float = Field(ge=0, le=100)
    revenue: float = Field(ge=0)
    adr: float = Field(ge=0)
    revpar: float = Field(ge=0)


class DailyMetricResponse(BaseModel):
    id: int
    hotel_id: int
    metric_date: date
    occupancy: float
    revenue: float
    adr: float
    revpar: float
