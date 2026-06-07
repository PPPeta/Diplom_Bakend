from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import require_roles
from app.db.session import get_core_session
from app.models.user import User
from app.schemas.role import RoleRead
from app.services import user_service

router = APIRouter(prefix="/roles", tags=["roles"])

DbDep = Annotated[AsyncSession, Depends(get_core_session)]
AdminDep = Annotated[User, Depends(require_roles("admin"))]


@router.get("", response_model=list[RoleRead])
async def list_roles(db: DbDep, _: AdminDep) -> list[RoleRead]:
    roles = await user_service.list_roles(db)
    return [RoleRead(id=r.id, code=r.code, name=r.name) for r in roles]
