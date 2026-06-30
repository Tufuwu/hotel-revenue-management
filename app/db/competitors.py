from datetime import date

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.db.model import CompetitorHotel, CompetitorRateSnapshot, Hotel
from app.db.serializers import (
    competitor_hotel_to_dict,
    competitor_rate_snapshot_to_dict,
)


def list_competitor_hotels(session: Session, hotel_id: int) -> list[dict] | None:
    if session.get(Hotel, hotel_id) is None:
        return None

    competitors = session.scalars(
        select(CompetitorHotel)
        .options(selectinload(CompetitorHotel.rate_snapshots))
        .where(
            CompetitorHotel.hotel_id == hotel_id,
            CompetitorHotel.distance_km <= 5,
        )
        .order_by(CompetitorHotel.distance_km)
    ).all()
    return [competitor_hotel_to_dict(competitor) for competitor in competitors]


def create_competitor_hotel(
    session: Session,
    hotel_id: int,
    name: str,
    room_type: str,
    latitude: float,
    longitude: float,
    distance_km: float,
) -> dict | None:
    if session.get(Hotel, hotel_id) is None:
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
    session.commit()
    session.refresh(competitor)
    return competitor_hotel_to_dict(competitor)


def create_competitor_rate_snapshot(
    session: Session,
    competitor_hotel_id: int,
    stay_date: date,
    price: float,
    source: str | None = None,
) -> dict | None:
    competitor = session.get(CompetitorHotel, competitor_hotel_id)
    if competitor is None:
        return None

    snapshot = CompetitorRateSnapshot(
        competitor_hotel_id=competitor_hotel_id,
        stay_date=stay_date,
        price=price,
        source=source,
    )
    session.add(snapshot)
    session.commit()
    session.refresh(snapshot)
    return competitor_rate_snapshot_to_dict(snapshot)
