from pydantic import BaseModel, Field, model_validator


class PricingConstraintRequest(BaseModel):
    min_price: float | None = Field(default=None, gt=0)
    max_price: float | None = Field(default=None, gt=0)

    @model_validator(mode="after")
    def validate_patch_payload(self) -> "PricingConstraintRequest":
        if not self.model_fields_set:
            raise ValueError("at least one pricing constraint field is required")
        if "min_price" in self.model_fields_set and self.min_price is None:
            raise ValueError("min_price cannot be null")
        if (
            "min_price" in self.model_fields_set
            and "max_price" in self.model_fields_set
            and self.min_price is not None
            and self.max_price is not None
            and self.max_price < self.min_price
        ):
            raise ValueError("max_price must be greater than or equal to min_price")
        return self


class PricingConstraintResponse(BaseModel):
    hotel_id: int
    min_price: float
    max_price: float | None = None
