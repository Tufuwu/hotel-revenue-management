from sqlalchemy.orm import Session

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


def get_hotel_pricing_inputs(db: Session) -> list[HotelPricingInput]:
    hotels = []
    for hotel in list_hotels(db):
        pricing_input = get_hotel_pricing_input(db, hotel["id"])
        if pricing_input is not None:
            hotels.append(HotelPricingInput(**pricing_input))
    return hotels


def get_hotel_daily_metrics(
    db: Session,
    hotel_id: int,
) -> list[DailyMetricResponse] | None:
    if get_hotel_pricing_input(db, hotel_id) is None:
        return None
    return [
        DailyMetricResponse(**metric)
        for metric in list_daily_metrics(db, hotel_id)
    ]


def record_hotel_daily_metric(
    db: Session,
    hotel_id: int,
    payload: DailyMetricRequest,
) -> DailyMetricResponse | None:
    metric = upsert_daily_metric(
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


def revise_pricing_constraint(
    db: Session,
    hotel_id: int,
    payload: PricingConstraintRequest,
) -> PricingConstraintResponse | None:
    pricing_input = get_hotel_pricing_input(db, hotel_id)
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

    constraint = update_pricing_constraint(
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
