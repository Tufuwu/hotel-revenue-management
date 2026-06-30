from pydantic import BaseModel, Field, field_validator


class HotelPricingInput(BaseModel):
    hotel_id: int
    room_type: str = Field(min_length=1)
    base_price: float = Field(gt=0)
    occupancy: float = Field(ge=0, le=100)
    latitude: float
    longitude: float
    competitor_prices: list[float] = Field(min_length=1)
    min_price: float = Field(gt=0)
    max_price: float | None = Field(default=None, gt=0)

    @field_validator("competitor_prices")
    @classmethod
    def competitor_prices_must_be_positive(cls, prices: list[float]) -> list[float]:
        if any(price <= 0 for price in prices):
            raise ValueError("competitor prices must be positive")
        return prices
