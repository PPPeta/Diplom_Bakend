from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import require_roles
from app.db.session import get_core_session
from app.models.user import User
from app.schemas.user import UserAdminUpdate, UserCreate, UserRead
from app.services import audit_service, user_service

router = APIRouter(prefix="/users", tags=["users"])

DbDep = Annotated[AsyncSession, Depends(get_core_session)]
AdminDep = Annotated[User, Depends(require_roles("admin"))]
AdminOrManagerDep = Annotated[User, Depends(require_roles("admin", "manager"))]


def _read(u: User) -> UserRead:
    return UserRead(
        id=u.id,
        email=u.email,
        full_name=u.full_name,
        phone=getattr(u, "phone", None),
        role=u.role.code if u.role else "",
        partner_id=u.partner_id,
        is_active=u.is_active,
    )


@router.get("", response_model=list[UserRead])
async def list_users(
    db: DbDep,
    actor: AdminOrManagerDep,
    role: str | None = None,
    partner_id: int | None = None,
) -> list[UserRead]:
    # Менеджеру нужен только список исполнителей для назначения задач.
    # Поэтому даём доступ менеджеру, но ограничиваем выборку.
    if actor.role.code == "manager":
        if role not in (None, "executor"):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Managers may only list executors",
            )
        role = "executor"
        partner_id = None

    users = await user_service.list_users(db, role=role, partner_id=partner_id)
    return [_read(u) for u in users]


@router.post("", response_model=UserRead, status_code=status.HTTP_201_CREATED)
async def create_user(data: UserCreate, db: DbDep, admin: AdminDep) -> UserRead:
    try:
        user = await user_service.create_user(
            db,
            email=data.email,
            password=data.password,
            full_name=data.full_name,
            phone=data.phone,
            role_code=data.role_code,
            partner_id=data.partner_id,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)
        )
    await audit_service.log_event(
        action="user.created",
        user_id=admin.id,
        user_role="admin",
        entity_type="user",
        entity_id=user.id,
        details=f"{user.email} ({data.role_code})",
    )
    return _read(user)


@router.get("/{user_id}", response_model=UserRead)
async def get_user(user_id: int, db: DbDep, _: AdminDep) -> UserRead:
    user = await user_service.get_user(db, user_id)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )
    return _read(user)


@router.patch("/{user_id}", response_model=UserRead)
async def update_user(
    user_id: int, data: UserAdminUpdate, db: DbDep, admin: AdminDep
) -> UserRead:
    user = await user_service.get_user(db, user_id)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )
    if user.id == admin.id and data.is_active is False:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Нельзя заблокировать собственную учётную запись",
        )
    try:
        user = await user_service.admin_update(
            db, user, is_active=data.is_active, role_code=data.role_code
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)
        )
    await audit_service.log_event(
        action="user.updated",
        user_id=admin.id,
        user_role="admin",
        entity_type="user",
        entity_id=user.id,
        details=f"is_active={user.is_active}, role={user.role.code if user.role else ''}",
    )
    return _read(user)
