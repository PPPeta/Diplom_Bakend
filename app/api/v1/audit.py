from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import require_roles
from app.db.session import get_analytics_session
from app.models.user import User
from app.schemas.audit import AuditLogRead
from app.services import audit_service

router = APIRouter(prefix="/audit", tags=["audit"])


@router.get("", response_model=list[AuditLogRead])
async def list_audit_logs(
    db: Annotated[AsyncSession, Depends(get_analytics_session)],
    # Только администратор имеет доступ к аудит-логу
    _: Annotated[User, Depends(require_roles("admin"))],
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
) -> list[AuditLogRead]:
    return await audit_service.list_logs(db, limit=limit, offset=offset)
