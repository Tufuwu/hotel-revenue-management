from datetime import date

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

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


async def init_db() -> None:
    await create_tables()
    async with SessionLocal() as session:
        hotel_count = len((await session.scalars(select(Hotel.id))).all())
        if hotel_count == 0:
            await seed_hotels(session)


async def reset_db() -> None:
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.drop_all)
    await create_tables()
    async with SessionLocal() as session:
        await seed_hotels(session)


async def create_tables() -> None:
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)


async def seed_hotels(session: AsyncSession) -> None:
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
    await session.commit()
