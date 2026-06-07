from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.router import api_router
from app.core.config import settings
from app.db.base import AnalyticsBase
from app.db.redis import redis_client
from app.db.session import analytics_engine, core_engine
from app.models import audit  # noqa: F401 — регистрируем модель AuditLog в metadata


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Создаём таблицы аудита в analytics_db, если их ещё нет.
    async with analytics_engine.begin() as conn:
        await conn.run_sync(AnalyticsBase.metadata.create_all)
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
