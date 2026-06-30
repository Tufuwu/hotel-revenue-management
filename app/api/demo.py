from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.schemas import SimulatePricingCycleRequest, SimulatePricingCycleResponse
from app.services.demo import simulate_pricing_cycle


router = APIRouter()


@router.post(
    "/demo/simulate-pricing-cycle",
    response_model=SimulatePricingCycleResponse,
)
async def simulate_cycle(
    payload: SimulatePricingCycleRequest,
    db: AsyncSession = Depends(get_db),
) -> SimulatePricingCycleResponse:
    result = await simulate_pricing_cycle(db, payload.hotel_id)
    if result is None:
        raise HTTPException(status_code=404, detail="hotel not found")
    return result
