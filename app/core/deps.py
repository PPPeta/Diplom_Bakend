from typing import Annotated, Callable

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import decode_token
from app.db.session import get_core_session
from app.models.user import User

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")

_credentials_error = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="Could not validate credentials",
    headers={"WWW-Authenticate": "Bearer"},
)


async def get_current_user(
    token: Annotated[str, Depends(oauth2_scheme)],
    db: Annotated[AsyncSession, Depends(get_core_session)],
) -> User:
    try:
        payload = decode_token(token)
        if payload.get("type") != "access":
            raise _credentials_error
        user_id = int(payload["sub"])
    except (JWTError, KeyError, ValueError):
        raise _credentials_error

    user = await db.get(User, user_id)
    if user is None or not user.is_active:
        raise _credentials_error
    return user


def require_roles(*roles: str) -> Callable:
    async def checker(
        user: Annotated[User, Depends(get_current_user)],
    ) -> User:
        if user.role.code not in roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient role permissions",
            )
        return user

    return checker
