from math import asin, cos, radians, sin, sqrt

from sqlalchemy.orm import Session

from app.db.competitors import (
    create_competitor_hotel,
    create_competitor_rate_snapshot,
    list_competitor_hotels,
)
from app.db.hotels import get_hotel_pricing_input
from app.schemas import (
    CompetitorHotelRequest,
    CompetitorHotelResponse,
    CompetitorRateSnapshotRequest,
    CompetitorRateSnapshotResponse,
)


def get_hotel_competitors(
    db: Session,
    hotel_id: int,
) -> list[CompetitorHotelResponse] | None:
    """Return competitors for a hotel, or None when the hotel is unknown."""
    competitors = list_competitor_hotels(db, hotel_id)
    if competitors is None:
        return None
    return [CompetitorHotelResponse(**competitor) for competitor in competitors]


def register_competitor_hotel(
    db: Session,
    hotel_id: int,
    payload: CompetitorHotelRequest,
) -> CompetitorHotelResponse | None:
    """Register a nearby competitor that is relevant to local pricing."""
    pricing_input = get_hotel_pricing_input(db, hotel_id)
    if pricing_input is None:
        return None

    distance_km = calculate_distance_km(
        pricing_input["latitude"],
        pricing_input["longitude"],
        payload.latitude,
        payload.longitude,
    )
    if distance_km > 5:
        raise ValueError("competitor hotel must be within 5 kilometers")

    competitor = create_competitor_hotel(
        db,
        hotel_id=hotel_id,
        name=payload.name,
        room_type=payload.room_type,
        latitude=payload.latitude,
        longitude=payload.longitude,
        distance_km=round(distance_km, 2),
    )
    if competitor is None:
        return None
    return CompetitorHotelResponse(**competitor)


def record_competitor_rate_snapshot(
    db: Session,
    competitor_hotel_id: int,
    payload: CompetitorRateSnapshotRequest,
) -> CompetitorRateSnapshotResponse | None:
    """Store one observed competitor rate used by future price predictions."""
    snapshot = create_competitor_rate_snapshot(
        db,
        competitor_hotel_id=competitor_hotel_id,
        stay_date=payload.stay_date,
        price=payload.price,
        source=payload.source,
    )
    if snapshot is None:
        return None
    return CompetitorRateSnapshotResponse(**snapshot)


def calculate_distance_km(
    from_latitude: float,
    from_longitude: float,
    to_latitude: float,
    to_longitude: float,
) -> float:
    """Calculate great-circle distance between two latitude/longitude points."""
    earth_radius_km = 6371.0
    lat_delta = radians(to_latitude - from_latitude)
    lon_delta = radians(to_longitude - from_longitude)
    from_lat = radians(from_latitude)
    to_lat = radians(to_latitude)
    haversine = (
        sin(lat_delta / 2) ** 2
        + cos(from_lat) * cos(to_lat) * sin(lon_delta / 2) ** 2
    )
    return 2 * earth_radius_km * asin(sqrt(haversine))
