from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api.routes import router as api_router
from app.db.lifecycle import init_db


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    yield


app = FastAPI(title="Hotel Dynamic Pricing MVP", lifespan=lifespan)
app.router.routes.extend(api_router.routes)
