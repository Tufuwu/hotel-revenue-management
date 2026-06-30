from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.db.model import CompetitorHotel, Hotel
from app.db.serializers import get_latest_snapshot


def list_hotels(session: Session) -> list[dict]:
    """List hotel records with only the fields needed by service workflows."""
    hotels = session.scalars(select(Hotel).order_by(Hotel.id)).all()
    return [
        {
            "id": hotel.id,
            "room_type": hotel.room_type,
            "base_price": hotel.base_price,
            "occupancy": hotel.occupancy,
            "latitude": hotel.latitude,
            "longitude": hotel.longitude,
        }
        for hotel in hotels
    ]


def get_hotel_pricing_input(session: Session, hotel_id: int) -> dict | None:
    """Load all inputs needed to price a hotel in a single query workflow."""
    hotel = session.scalar(
        select(Hotel)
        .options(
            selectinload(Hotel.competitor_hotels).selectinload(
                CompetitorHotel.rate_snapshots
            ),
            selectinload(Hotel.pricing_constraint),
        )
        .where(Hotel.id == hotel_id)
    )
    if hotel is None:
        return None

    # Use the latest rate from nearby competitors, ordered by distance.
    competitor_prices = [
        latest_snapshot.price
        for competitor in sorted(
            hotel.competitor_hotels,
            key=lambda item: item.distance_km,
        )
        if competitor.distance_km <= 5
        for latest_snapshot in [get_latest_snapshot(competitor.rate_snapshots)]
        if latest_snapshot is not None
    ]
    return {
        "hotel_id": hotel.id,
        "room_type": hotel.room_type,
        "base_price": hotel.base_price,
        "occupancy": hotel.occupancy,
        "latitude": hotel.latitude,
        "longitude": hotel.longitude,
        "competitor_prices": competitor_prices,
        "min_price": hotel.pricing_constraint.min_price
        if hotel.pricing_constraint
        else hotel.base_price * 0.7,
        "max_price": hotel.pricing_constraint.max_price
        if hotel.pricing_constraint
        else hotel.base_price * 1.3,
    }
