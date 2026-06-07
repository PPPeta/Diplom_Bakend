from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_user
from app.core.rate_limit import rate_limit_login
from app.db.session import get_core_session
from app.models.user import User
from app.schemas.auth import RefreshRequest, Token
from app.schemas.user import PasswordChange, ProfileUpdate, UserRead, UserRegister
from app.services import audit_service, auth_service

router = APIRouter(prefix="/auth", tags=["auth"])


def _user_read(user: User) -> UserRead:
    return UserRead(
        id=user.id,
        email=user.email,
        full_name=user.full_name,
        phone=user.phone,
        role=user.role.code,
        partner_id=user.partner_id,
        is_active=user.is_active,
    )


@router.post("/register", response_model=UserRead, status_code=status.HTTP_201_CREATED)
async def register(
    data: UserRegister,
    db: Annotated[AsyncSession, Depends(get_core_session)],
) -> UserRead:
    try:
        user = await auth_service.register_partner(db, data)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
    return UserRead(
        id=user.id,
        email=user.email,
        full_name=user.full_name,
        phone=user.phone,
        role="partner",
        partner_id=user.partner_id,
        is_active=user.is_active,
    )


@router.post(
    "/login",
    response_model=Token,
    dependencies=[Depends(rate_limit_login)],
)
async def login(
    form: Annotated[OAuth2PasswordRequestForm, Depends()],
    db: Annotated[AsyncSession, Depends(get_core_session)],
) -> Token:
    user = await auth_service.authenticate(db, form.username, form.password)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
        )
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="User is inactive"
        )
    access, refresh = await auth_service.issue_tokens(
        user.id, user.role.code, user.partner_id
    )
    # Пишем вход в аудит-лог.
    await audit_service.log_event(
        action="auth.login",
        user_id=user.id,
        user_role=user.role.code,
        entity_type="user",
        entity_id=user.id,
        details=user.email,
    )
    return Token(access_token=access, refresh_token=refresh)


@router.post("/refresh", response_model=Token)
async def refresh(
    data: RefreshRequest,
    db: Annotated[AsyncSession, Depends(get_core_session)],
) -> Token:
    try:
        access, refresh_token = await auth_service.rotate_refresh(db, data.refresh_token)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token",
        )
    return Token(access_token=access, refresh_token=refresh_token)


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(user: Annotated[User, Depends(get_current_user)]) -> None:
    await auth_service.revoke_all(user.id)


@router.get("/me", response_model=UserRead)
async def me(user: Annotated[User, Depends(get_current_user)]) -> UserRead:
    return _user_read(user)


@router.patch("/me", response_model=UserRead)
async def update_me(
    data: ProfileUpdate,
    db: Annotated[AsyncSession, Depends(get_core_session)],
    user: Annotated[User, Depends(get_current_user)],
) -> UserRead:
    updated = await auth_service.update_profile(
        db, user, full_name=data.full_name, phone=data.phone
    )
    return _user_read(updated)


@router.post("/change-password", status_code=status.HTTP_204_NO_CONTENT)
async def change_password(
    data: PasswordChange,
    db: Annotated[AsyncSession, Depends(get_core_session)],
    user: Annotated[User, Depends(get_current_user)],
) -> None:
    try:
        await auth_service.change_password(
            db, user, data.current_password, data.new_password
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)
        )
