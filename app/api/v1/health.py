from fastapi import APIRouter, Depends
from redis.asyncio import Redis
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.redis import get_redis
from app.db.session import get_analytics_session, get_core_session

router = APIRouter(tags=["health"])


@router.get("/health")
async def health() -> dict:
    return {"status": "ok"}


@router.get("/health/ready")
async def readiness(
    core: AsyncSession = Depends(get_core_session),
    analytics: AsyncSession = Depends(get_analytics_session),
    redis: Redis = Depends(get_redis),
) -> dict:
    checks: dict[str, str] = {}

    try:
        await core.execute(text("SELECT 1"))
        checks["core_db"] = "ok"
    except Exception as exc:  # noqa: BLE001
        checks["core_db"] = f"error: {exc}"

    try:
        await analytics.execute(text("SELECT 1"))
        checks["analytics_db"] = "ok"
    except Exception as exc:  # noqa: BLE001
        checks["analytics_db"] = f"error: {exc}"

    try:
        await redis.ping()
        checks["redis"] = "ok"
    except Exception as exc:  # noqa: BLE001
        checks["redis"] = f"error: {exc}"

    healthy = all(value == "ok" for value in checks.values())
    checks["status"] = "ok" if healthy else "degraded"
    return checks
