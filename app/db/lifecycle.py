from datetime import date

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.model import (
    Base,
    CompetitorHotel,
    CompetitorRateSnapshot,
    DailyMetric,
    Hotel,
    PricingConstraint,
)
from app.db.seed import get_seed_hotels
from app.db.session import SessionLocal, engine


def init_db() -> None:
    create_tables()
    with SessionLocal() as session:
        hotel_count = len(session.scalars(select(Hotel.id)).all())
        if hotel_count == 0:
            seed_hotels(session)


def reset_db() -> None:
    Base.metadata.drop_all(bind=engine)
    create_tables()
    with SessionLocal() as session:
        seed_hotels(session)


def create_tables() -> None:
    Base.metadata.create_all(bind=engine)


def seed_hotels(session: Session) -> None:
    for hotel in get_seed_hotels():
        session.add(
            Hotel(
                id=hotel["hotel_id"],
                room_type=hotel["room_type"],
                base_price=hotel["base_price"],
                occupancy=hotel["occupancy"],
                latitude=hotel["latitude"],
                longitude=hotel["longitude"],
                competitor_hotels=[
                    CompetitorHotel(
                        name=competitor["name"],
                        room_type=competitor["room_type"],
                        latitude=competitor["latitude"],
                        longitude=competitor["longitude"],
                        distance_km=competitor["distance_km"],
                        rate_snapshots=[
                            CompetitorRateSnapshot(
                                stay_date=date.fromisoformat(snapshot["stay_date"]),
                                price=snapshot["price"],
                                source=snapshot["source"],
                            )
                            for snapshot in competitor["rate_snapshots"]
                        ],
                    )
                    for competitor in hotel["competitor_hotels"]
                ],
                pricing_constraint=PricingConstraint(
                    min_price=hotel["min_price"],
                    max_price=hotel["max_price"],
                ),
                daily_metrics=[
                    DailyMetric(
                        metric_date=date.fromisoformat(metric["metric_date"]),
                        occupancy=metric["occupancy"],
                        revenue=metric["revenue"],
                        adr=metric["adr"],
                        revpar=metric["revpar"],
                    )
                    for metric in hotel["daily_metrics"]
                ],
            )
        )
    session.commit()
