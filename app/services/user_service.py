from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.role import Role
from app.models.user import User


async def list_users(
    db: AsyncSession,
    role: str | None = None,
    partner_id: int | None = None,
    limit: int = 500,
    offset: int = 0,
) -> list[User]:
    stmt = (
        select(User)
        .options(selectinload(User.role))
        .order_by(User.id.asc())
        .limit(limit)
        .offset(offset)
    )
    if partner_id is not None:
        stmt = stmt.where(User.partner_id == partner_id)
    if role:
        role_obj = (
            await db.execute(select(Role).where(Role.code == role))
        ).scalar_one_or_none()
        if role_obj is None:
            return []
        stmt = stmt.where(User.role_id == role_obj.id)
    return list((await db.execute(stmt)).scalars().all())


async def get_user(db: AsyncSession, user_id: int) -> User | None:
    stmt = (
        select(User).options(selectinload(User.role)).where(User.id == user_id)
    )
    return (await db.execute(stmt)).scalar_one_or_none()


async def admin_update(
    db: AsyncSession,
    user: User,
    is_active: bool | None = None,
    role_code: str | None = None,
) -> User:
    if is_active is not None:
        user.is_active = is_active
    if role_code is not None:
        role_obj = (
            await db.execute(select(Role).where(Role.code == role_code))
        ).scalar_one_or_none()
        if role_obj is None:
            raise ValueError("unknown role code")
        user.role_id = role_obj.id
    await db.commit()
    refreshed = await get_user(db, user.id)
    assert refreshed is not None
    return refreshed
