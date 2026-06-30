from sqlalchemy.orm import Session

from app.db.model import Hotel, PricingConstraint


def update_pricing_constraint(
    session: Session,
    hotel_id: int,
    min_price: float | None = None,
    max_price: float | None = None,
    update_min_price: bool = False,
    update_max_price: bool = False,
) -> dict | None:
    hotel = session.get(Hotel, hotel_id)
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

    session.commit()
    session.refresh(constraint)
    return {
        "hotel_id": hotel_id,
        "min_price": constraint.min_price,
        "max_price": constraint.max_price,
    }
