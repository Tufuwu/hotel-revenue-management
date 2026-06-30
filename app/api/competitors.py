from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.schemas import (
    CompetitorHotelRequest,
    CompetitorHotelResponse,
    CompetitorRateSnapshotRequest,
    CompetitorRateSnapshotResponse,
)
from app.services.competitors import (
    get_hotel_competitors,
    record_competitor_rate_snapshot,
    register_competitor_hotel,
)


router = APIRouter()


@router.get(
    "/hotels/{hotel_id}/competitors",
    response_model=list[CompetitorHotelResponse],
)
async def get_competitors(
    hotel_id: int,
    db: AsyncSession = Depends(get_db),
) -> list[CompetitorHotelResponse]:
    competitors = await get_hotel_competitors(db, hotel_id)
    if competitors is None:
        raise HTTPException(status_code=404, detail="hotel not found")
    return competitors


@router.post(
    "/hotels/{hotel_id}/competitors",
    response_model=CompetitorHotelResponse,
)
async def create_competitor(
    hotel_id: int,
    payload: CompetitorHotelRequest,
    db: AsyncSession = Depends(get_db),
) -> CompetitorHotelResponse:
    try:
        competitor = await register_competitor_hotel(db, hotel_id, payload)
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error
    if competitor is None:
        raise HTTPException(status_code=404, detail="hotel not found")
    return competitor


@router.post(
    "/competitors/{competitor_id}/rates",
    response_model=CompetitorRateSnapshotResponse,
)
async def create_competitor_rate(
    competitor_id: int,
    payload: CompetitorRateSnapshotRequest,
    db: AsyncSession = Depends(get_db),
) -> CompetitorRateSnapshotResponse:
    snapshot = await record_competitor_rate_snapshot(db, competitor_id, payload)
    if snapshot is None:
        raise HTTPException(status_code=404, detail="competitor hotel not found")
    return snapshot
