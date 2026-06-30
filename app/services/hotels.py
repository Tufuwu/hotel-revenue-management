from sqlalchemy.ext.asyncio import AsyncSession

from app.db.constraints import update_pricing_constraint
from app.db.hotels import get_hotel_pricing_input, list_hotels
from app.db.metrics import (
    list_daily_metrics,
    upsert_daily_metric,
)
from app.schemas import (
    DailyMetricRequest,
    DailyMetricResponse,
    HotelPricingInput,
    PricingConstraintRequest,
    PricingConstraintResponse,
)


async def get_hotel_pricing_inputs(db: AsyncSession) -> list[HotelPricingInput]:
    """Return pricing-ready inputs for every configured hotel."""
    hotels = []
    for hotel in await list_hotels(db):
        pricing_input = await get_hotel_pricing_input(db, hotel["id"])
        if pricing_input is not None:
            hotels.append(HotelPricingInput(**pricing_input))
    return hotels


async def get_hotel_daily_metrics(
    db: AsyncSession,
    hotel_id: int,
) -> list[DailyMetricResponse] | None:
    """Return daily performance metrics after validating the hotel exists."""
    if await get_hotel_pricing_input(db, hotel_id) is None:
        return None
    return [
        DailyMetricResponse(**metric)
        for metric in await list_daily_metrics(db, hotel_id)
    ]


async def record_hotel_daily_metric(
    db: AsyncSession,
    hotel_id: int,
    payload: DailyMetricRequest,
) -> DailyMetricResponse | None:
    """Create or update one daily operating metric for a hotel."""
    metric = await upsert_daily_metric(
        db,
        hotel_id=hotel_id,
        metric_date=payload.metric_date,
        occupancy=payload.occupancy,
        revenue=payload.revenue,
        adr=payload.adr,
        revpar=payload.revpar,
    )
    if metric is None:
        return None
    return DailyMetricResponse(**metric)


async def revise_pricing_constraint(
    db: AsyncSession,
    hotel_id: int,
    payload: PricingConstraintRequest,
) -> PricingConstraintResponse | None:
    """Update floor and ceiling prices used to bound recommendations."""
    pricing_input = await get_hotel_pricing_input(db, hotel_id)
    if pricing_input is None:
        return None

    min_price = (
        payload.min_price
        if "min_price" in payload.model_fields_set
        else pricing_input["min_price"]
    )
    max_price = (
        payload.max_price
        if "max_price" in payload.model_fields_set
        else pricing_input["max_price"]
    )
    if max_price is not None and max_price < min_price:
        raise ValueError("max_price must be greater than or equal to min_price")

    constraint = await update_pricing_constraint(
        db,
        hotel_id=hotel_id,
        min_price=payload.min_price,
        max_price=payload.max_price,
        update_min_price="min_price" in payload.model_fields_set,
        update_max_price="max_price" in payload.model_fields_set,
    )
    if constraint is None:
        return None
    return PricingConstraintResponse(**constraint)
