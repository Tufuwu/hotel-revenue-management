from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.db.model import Hotel, PricingConstraint


async def update_pricing_constraint(
    session: AsyncSession,
    hotel_id: int,
    min_price: float | None = None,
    max_price: float | None = None,
    update_min_price: bool = False,
    update_max_price: bool = False,
) -> dict | None:
    hotel = await session.scalar(
        select(Hotel)
        .options(selectinload(Hotel.pricing_constraint))
        .where(Hotel.id == hotel_id)
    )
    if hotel is None:
        return None

    constraint = hotel.pricing_constraint
    if constraint is None:
        constraint = PricingConstraint(
            hotel_id=hotel_id,
            min_price=hotel.base_price * 0.7,
            max_price=hotel.base_price * 1.3,
        )
        session.add(constraint)

    if update_min_price:
        constraint.min_price = min_price
    if update_max_price:
        constraint.max_price = max_price

    await session.commit()
    await session.refresh(constraint)
    return {
        "hotel_id": hotel_id,
        "min_price": constraint.min_price,
        "max_price": constraint.max_price,
    }
