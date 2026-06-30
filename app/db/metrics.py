from datetime import date

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.model import DailyMetric, Hotel
from app.db.serializers import daily_metric_to_dict


async def list_daily_metrics(session: AsyncSession, hotel_id: int) -> list[dict]:
    metrics = (await session.scalars(
        select(DailyMetric)
        .where(DailyMetric.hotel_id == hotel_id)
        .order_by(DailyMetric.metric_date)
    )).all()
    return [daily_metric_to_dict(metric) for metric in metrics]


async def upsert_daily_metric(
    session: AsyncSession,
    hotel_id: int,
    metric_date: date,
    occupancy: float,
    revenue: float,
    adr: float,
    revpar: float,
) -> dict | None:
    hotel = await session.get(Hotel, hotel_id)
    if hotel is None:
        return None

    metric = await session.scalar(
        select(DailyMetric).where(
            DailyMetric.hotel_id == hotel_id,
            DailyMetric.metric_date == metric_date,
        )
    )
    if metric is None:
        metric = DailyMetric(hotel_id=hotel_id, metric_date=metric_date)
        session.add(metric)

    metric.occupancy = occupancy
    metric.revenue = revenue
    metric.adr = adr
    metric.revpar = revpar
    hotel.occupancy = occupancy
    await session.commit()
    await session.refresh(metric)
    return daily_metric_to_dict(metric)
