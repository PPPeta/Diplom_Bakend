from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.request import Request
from app.schemas.request import RequestCreate


async def create_request(db: AsyncSession, data: RequestCreate) -> Request:
    request = Request(**data.model_dump())
    db.add(request)
    await db.commit()
    await db.refresh(request)
    return request


async def list_requests(
    db: AsyncSession,
    status: str | None = None,
    limit: int = 100,
    offset: int = 0,
) -> list[Request]:
    stmt = (
        select(Request)
        .order_by(Request.created_at.desc())
        .limit(limit)
        .offset(offset)
    )
    if status:
        stmt = stmt.where(Request.status == status)
    return list((await db.execute(stmt)).scalars().all())


async def get_request(db: AsyncSession, request_id: int) -> Request | None:
    return await db.get(Request, request_id)


async def set_status(db: AsyncSession, request: Request, status: str) -> Request:
    request.status = status
    await db.commit()
    await db.refresh(request)
    return request
