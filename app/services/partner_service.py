from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.partner import Partner


async def list_partners(
    db: AsyncSession, limit: int = 500, offset: int = 0
) -> list[Partner]:
    stmt = (
        select(Partner)
        .order_by(Partner.id.asc())
        .limit(limit)
        .offset(offset)
    )
    return list((await db.execute(stmt)).scalars().all())


async def get_partner(db: AsyncSession, partner_id: int) -> Partner | None:
    return await db.get(Partner, partner_id)
