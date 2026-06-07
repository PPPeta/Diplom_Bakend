from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.security import hash_password
from app.models.partner import Partner
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


async def list_roles(db: AsyncSession) -> list[Role]:
    stmt = select(Role).order_by(Role.id.asc())
    return list((await db.execute(stmt)).scalars().all())


async def create_user(
    db: AsyncSession,
    *,
    email: str,
    password: str,
    full_name: str,
    role_code: str,
    phone: str | None = None,
    partner_id: int | None = None,
) -> User:
    existing = (
        await db.execute(select(User).where(User.email == email))
    ).scalar_one_or_none()
    if existing is not None:
        raise ValueError("Пользователь с таким email уже существует")
    role_obj = (
        await db.execute(select(Role).where(Role.code == role_code))
    ).scalar_one_or_none()
    if role_obj is None:
        raise ValueError("Неизвестный код роли")
    if partner_id is not None:
        partner = await db.get(Partner, partner_id)
        if partner is None:
            raise ValueError("Организация-партнёр не найдена")
    user = User(
        email=email,
        password_hash=hash_password(password),
        full_name=full_name,
        phone=phone,
        role_id=role_obj.id,
        partner_id=partner_id,
        is_active=True,
    )
    db.add(user)
    await db.commit()
    refreshed = await get_user(db, user.id)
    assert refreshed is not None
    return refreshed


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
