import uuid
from datetime import datetime, timedelta, timezone
from typing import Any

from jose import jwt
from passlib.context import CryptContext

from app.core.config import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain_password: str, password_hash: str) -> bool:
    return pwd_context.verify(plain_password, password_hash)


def create_access_token(subject: int, role: str, partner_id: int | None = None) -> str:
    now = datetime.now(timezone.utc)
    payload: dict[str, Any] = {
        "sub": str(subject),
        "role": role,
        "partner_id": partner_id,
        "type": "access",
        "iat": int(now.timestamp()),
        "exp": int(
            (now + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)).timestamp()
        ),
    }
    return jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def create_refresh_token(
    subject: int, role: str, partner_id: int | None = None
) -> tuple[str, str]:
    now = datetime.now(timezone.utc)
    jti = str(uuid.uuid4())
    payload: dict[str, Any] = {
        "sub": str(subject),
        "role": role,
        "partner_id": partner_id,
        "type": "refresh",
        "jti": jti,
        "iat": int(now.timestamp()),
        "exp": int(
            (now + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)).timestamp()
        ),
    }
    token = jwt.encode(
        payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM
    )
    return token, jti


def decode_token(token: str) -> dict[str, Any]:
    return jwt.decode(
        token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM]
    )
