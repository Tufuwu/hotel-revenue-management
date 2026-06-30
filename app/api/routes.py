from fastapi import APIRouter

from app.api import competitors, demo, feedback, home, hotels, pricing


router = APIRouter()
for child_router in (
    home.router,
    hotels.router,
    pricing.router,
    competitors.router,
    feedback.router,
    demo.router,
):
    router.routes.extend(child_router.routes)
