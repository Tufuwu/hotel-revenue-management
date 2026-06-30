from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.schemas import (
    DailyMetricRequest,
    DailyMetricResponse,
    HotelPricingInput,
    PricingConstraintRequest,
    PricingConstraintResponse,
)
from app.services.hotels import (
    get_hotel_daily_metrics,
    get_hotel_pricing_inputs,
    record_hotel_daily_metric,
    revise_pricing_constraint,
)


router = APIRouter()


@router.get("/hotels", response_model=list[HotelPricingInput])
async def get_hotels(
    db: AsyncSession = Depends(get_db),
) -> list[HotelPricingInput]:
    return await get_hotel_pricing_inputs(db)


@router.get(
    "/hotels/{hotel_id}/metrics",
    response_model=list[DailyMetricResponse],
)
async def get_daily_metrics(
    hotel_id: int,
    db: AsyncSession = Depends(get_db),
) -> list[DailyMetricResponse]:
    metrics = await get_hotel_daily_metrics(db, hotel_id)
    if metrics is None:
        raise HTTPException(status_code=404, detail="hotel not found")
    return metrics


@router.post(
    "/hotels/{hotel_id}/metrics",
    response_model=DailyMetricResponse,
)
async def create_daily_metric(
    hotel_id: int,
    payload: DailyMetricRequest,
    db: AsyncSession = Depends(get_db),
) -> DailyMetricResponse:
    metric = await record_hotel_daily_metric(db, hotel_id, payload)
    if metric is None:
        raise HTTPException(status_code=404, detail="hotel not found")
    return metric


@router.patch(
    "/hotels/{hotel_id}/pricing-constraints",
    response_model=PricingConstraintResponse,
)
async def update_hotel_pricing_constraints(
    hotel_id: int,
    payload: PricingConstraintRequest,
    db: AsyncSession = Depends(get_db),
) -> PricingConstraintResponse:
    try:
        constraint = await revise_pricing_constraint(db, hotel_id, payload)
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error
    if constraint is None:
        raise HTTPException(status_code=404, detail="hotel not found")
    return constraint
