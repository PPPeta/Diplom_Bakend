from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import require_roles
from app.db.session import get_core_session
from app.models.user import User
from app.schemas.partner import PartnerRead
from app.schemas.pricing import (
    PartnerPriceListUpdate,
    PartnerTermCreate,
    PartnerTermRead,
    PartnerTermUpdate,
)
from app.services import partner_service, pricing_admin_service

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


# ---------- Partner terms (discounts / commissions) ----------
@router.get("/{partner_id}/terms", response_model=list[PartnerTermRead])
async def list_partner_terms(
    partner_id: int, db: DbDep, _: StaffDep
) -> list[PartnerTermRead]:
    partner = await partner_service.get_partner(db, partner_id)
    if partner is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Partner not found"
        )
    return await pricing_admin_service.list_partner_terms(db, partner_id)


@router.post(
    "/{partner_id}/terms",
    response_model=PartnerTermRead,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_roles("admin", "manager"))],
)
async def create_partner_term(
    partner_id: int, data: PartnerTermCreate, db: DbDep
) -> PartnerTermRead:
    try:
        return await pricing_admin_service.create_partner_term(
            db, partner_id, data
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)
        )


@router.patch(
    "/{partner_id}/terms/{term_id}",
    response_model=PartnerTermRead,
    dependencies=[Depends(require_roles("admin", "manager"))],
)
async def update_partner_term(
    partner_id: int, term_id: int, data: PartnerTermUpdate, db: DbDep
) -> PartnerTermRead:
    term = await pricing_admin_service.get_partner_term(db, term_id)
    if term is None or term.partner_id != partner_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Partner term not found",
        )
    return await pricing_admin_service.update_partner_term(db, term, data)


@router.delete(
    "/{partner_id}/terms/{term_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(require_roles("admin", "manager"))],
)
async def delete_partner_term(
    partner_id: int, term_id: int, db: DbDep
) -> None:
    term = await pricing_admin_service.get_partner_term(db, term_id)
    if term is None or term.partner_id != partner_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Partner term not found",
        )
    await pricing_admin_service.delete_partner_term(db, term)


# ---------- Partner price list assignment ----------
@router.patch(
    "/{partner_id}/price-list",
    response_model=PartnerRead,
    dependencies=[Depends(require_roles("admin", "manager"))],
)
async def set_partner_price_list(
    partner_id: int, data: PartnerPriceListUpdate, db: DbDep
) -> PartnerRead:
    partner = await partner_service.get_partner(db, partner_id)
    if partner is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Partner not found"
        )
    try:
        return await pricing_admin_service.set_partner_price_list(
            db, partner, data.price_list_id
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)
        )
