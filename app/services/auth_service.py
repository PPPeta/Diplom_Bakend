from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    verify_password,
)
from app.db.redis import redis_client
from app.models.partner import Partner
from app.models.role import Role
from app.models.user import User
from app.schemas.user import UserRegister


def _refresh_key(user_id: int, jti: str) -> str:
    return f"refresh:{user_id}:{jti}"


async def authenticate(db: AsyncSession, email: str, password: str) -> User | None:
    result = await db.execute(select(User).where(User.email == email))
    user = result.scalar_one_or_none()
    if user is None or not verify_password(password, user.password_hash):
        return None
    return user


async def issue_tokens(
    user_id: int, role_code: str, partner_id: int | None
) -> tuple[str, str]:
    access = create_access_token(user_id, role_code, partner_id)
    refresh, jti = create_refresh_token(user_id, role_code, partner_id)
    await redis_client.set(
        _refresh_key(user_id, jti),
        "1",
        ex=settings.REFRESH_TOKEN_EXPIRE_DAYS * 24 * 3600,
    )
    return access, refresh


async def rotate_refresh(db: AsyncSession, refresh_token: str) -> tuple[str, str]:
    payload = decode_token(refresh_token)
    if payload.get("type") != "refresh":
        raise ValueError("invalid token type")
    user_id = int(payload["sub"])
    jti = payload["jti"]
    key = _refresh_key(user_id, jti)
    if not await redis_client.get(key):
        raise ValueError("refresh token revoked")
    await redis_client.delete(key)
    user = await db.get(User, user_id)
    if user is None or not user.is_active:
        raise ValueError("user inactive")
    return await issue_tokens(user.id, user.role.code, user.partner_id)


async def revoke_all(user_id: int) -> None:
    keys = [key async for key in redis_client.scan_iter(match=f"refresh:{user_id}:*")]
    if keys:
        await redis_client.delete(*keys)


async def register_partner(db: AsyncSession, data: UserRegister) -> User:
    existing = await db.execute(select(User).where(User.email == data.email))
    if existing.scalar_one_or_none() is not None:
        raise ValueError("email already registered")

    role_result = await db.execute(select(Role).where(Role.code == "partner"))
    role = role_result.scalar_one_or_none()
    if role is None:
        raise ValueError("partner role is missing; run migrations")

    partner = Partner(
        org_name=data.partner.org_name,
        inn=data.partner.inn,
        type=data.partner.type,
        contract_no=data.partner.contract_no,
    )
    db.add(partner)
    await db.flush()

    user = User(
        email=data.email,
        password_hash=hash_password(data.password),
        full_name=data.full_name,
        role_id=role.id,
        partner_id=partner.id,
        is_partner_admin=True,
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user
