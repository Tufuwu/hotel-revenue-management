from datetime import date, datetime

from pydantic import BaseModel, Field


class CompetitorHotelRequest(BaseModel):
    name: str = Field(min_length=1)
    room_type: str = Field(min_length=1)
    latitude: float
    longitude: float


class CompetitorHotelResponse(BaseModel):
    id: int
    hotel_id: int
    name: str
    room_type: str
    latitude: float
    longitude: float
    distance_km: float
    latest_price: float | None = None
    latest_stay_date: date | None = None


class CompetitorRateSnapshotRequest(BaseModel):
    stay_date: date
    price: float = Field(gt=0)
    source: str | None = Field(default=None, max_length=100)


class CompetitorRateSnapshotResponse(BaseModel):
    id: int
    competitor_hotel_id: int
    stay_date: date
    price: float
    source: str | None = None
    collected_at: datetime
