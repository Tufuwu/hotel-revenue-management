from datetime import date

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.db.model import CompetitorHotel, CompetitorRateSnapshot, Hotel
from app.db.serializers import (
    competitor_hotel_to_dict,
    competitor_rate_snapshot_to_dict,
)


async def list_competitor_hotels(session: AsyncSession, hotel_id: int) -> list[dict] | None:
    if await session.get(Hotel, hotel_id) is None:
        return None

    competitors = (await session.scalars(
        select(CompetitorHotel)
        .options(selectinload(CompetitorHotel.rate_snapshots))
        .where(
            CompetitorHotel.hotel_id == hotel_id,
            CompetitorHotel.distance_km <= 5,
        )
        .order_by(CompetitorHotel.distance_km)
    )).all()
    return [competitor_hotel_to_dict(competitor) for competitor in competitors]


async def create_competitor_hotel(
    session: AsyncSession,
    hotel_id: int,
    name: str,
    room_type: str,
    latitude: float,
    longitude: float,
    distance_km: float,
) -> dict | None:
    if await session.get(Hotel, hotel_id) is None:
        return None

    competitor = CompetitorHotel(
        hotel_id=hotel_id,
        name=name,
        room_type=room_type,
        latitude=latitude,
        longitude=longitude,
        distance_km=distance_km,
    )
    session.add(competitor)
    await session.commit()
    await session.refresh(competitor)
    return {
        "id": competitor.id,
        "hotel_id": competitor.hotel_id,
        "name": competitor.name,
        "room_type": competitor.room_type,
        "latitude": competitor.latitude,
        "longitude": competitor.longitude,
        "distance_km": competitor.distance_km,
        "latest_price": None,
        "latest_stay_date": None,
    }


async def create_competitor_rate_snapshot(
    session: AsyncSession,
    competitor_hotel_id: int,
    stay_date: date,
    price: float,
    source: str | None = None,
) -> dict | None:
    competitor = await session.get(CompetitorHotel, competitor_hotel_id)
    if competitor is None:
        return None

    snapshot = CompetitorRateSnapshot(
        competitor_hotel_id=competitor_hotel_id,
        stay_date=stay_date,
        price=price,
        source=source,
    )
    session.add(snapshot)
    await session.commit()
    await session.refresh(snapshot)
    return competitor_rate_snapshot_to_dict(snapshot)
