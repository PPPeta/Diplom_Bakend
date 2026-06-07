from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import require_roles
from app.db.session import get_core_session
from app.models.user import User
from app.schemas.partner import PartnerRead
from app.services import partner_service

router = APIRouter(prefix="/partners", tags=["partners"])

DbDep = Annotated[AsyncSession, Depends(get_core_session)]
StaffDep = Annotated[User, Depends(require_roles("admin", "manager"))]


@router.get("", response_model=list[PartnerRead])
async def list_partners(db: DbDep, _: StaffDep) -> list[PartnerRead]:
    return await partner_service.list_partners(db)


@router.get("/{partner_id}", response_model=PartnerRead)
async def get_partner(
    partner_id: int, db: DbDep, _: StaffDep
) -> PartnerRead:
    partner = await partner_service.get_partner(db, partner_id)
    if partner is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Partner not found"
        )
    return partner
