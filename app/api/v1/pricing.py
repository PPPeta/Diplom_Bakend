from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import require_roles
from app.db.session import get_core_session
from app.models.user import User
from app.schemas.pricing import (
    PriceListCreate,
    PriceListItemCreate,
    PriceListRead,
    PriceListUpdate,
)
from app.services import pricing_admin_service

router = APIRouter(prefix="/price-lists", tags=["pricing"])

DbDep = Annotated[AsyncSession, Depends(get_core_session)]
StaffDep = Annotated[User, Depends(require_roles("admin", "manager"))]


@router.get("", response_model=list[PriceListRead])
async def list_price_lists(
    db: DbDep,
    _: StaffDep,
    kind: str | None = None,
    partner_id: int | None = None,
) -> list[PriceListRead]:
    return await pricing_admin_service.list_price_lists(
        db, kind=kind, partner_id=partner_id
    )


@router.get("/{price_list_id}", response_model=PriceListRead)
async def get_price_list(
    price_list_id: int, db: DbDep, _: StaffDep
) -> PriceListRead:
    pl = await pricing_admin_service.get_price_list(db, price_list_id)
    if pl is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Price list not found"
        )
    return pl


@router.post(
    "",
    response_model=PriceListRead,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_roles("admin", "manager"))],
)
async def create_price_list(data: PriceListCreate, db: DbDep) -> PriceListRead:
    try:
        return await pricing_admin_service.create_price_list(db, data)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)
        )


@router.patch(
    "/{price_list_id}",
    response_model=PriceListRead,
    dependencies=[Depends(require_roles("admin", "manager"))],
)
async def update_price_list(
    price_list_id: int, data: PriceListUpdate, db: DbDep
) -> PriceListRead:
    pl = await pricing_admin_service.get_price_list(db, price_list_id)
    if pl is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Price list not found"
        )
    try:
        return await pricing_admin_service.update_price_list(db, pl, data)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)
        )


@router.put(
    "/{price_list_id}/items",
    response_model=PriceListRead,
    dependencies=[Depends(require_roles("admin", "manager"))],
)
async def replace_price_list_items(
    price_list_id: int, items: list[PriceListItemCreate], db: DbDep
) -> PriceListRead:
    pl = await pricing_admin_service.get_price_list(db, price_list_id)
    if pl is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Price list not found"
        )
    try:
        return await pricing_admin_service.replace_items(db, pl, items)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)
        )


@router.delete(
    "/{price_list_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(require_roles("admin"))],
)
async def delete_price_list(price_list_id: int, db: DbDep) -> None:
    pl = await pricing_admin_service.get_price_list(db, price_list_id)
    if pl is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Price list not found"
        )
    await pricing_admin_service.delete_price_list(db, pl)
