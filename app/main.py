from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.router import api_router
from app.core.config import settings
from app.db.redis import redis_client
from app.db.session import analytics_engine, core_engine


@asynccontextmanager
async def lifespan(app: FastAPI):
    yield
    await core_engine.dispose()
    await analytics_engine.dispose()
    await redis_client.aclose()


app = FastAPI(title=settings.APP_NAME, debug=settings.DEBUG, lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix=settings.API_V1_PREFIX)


@app.get("/")
async def root() -> dict:
    return {"service": settings.APP_NAME, "docs": "/docs"}
