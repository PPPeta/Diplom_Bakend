from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_user, require_roles
from app.db.session import get_core_session
from app.models.user import User
from app.schemas.order import OrderCreate, OrderRead, OrderStatusUpdate
from app.services import order_service

router = APIRouter(prefix="/orders", tags=["orders"])

DbDep = Annotated[AsyncSession, Depends(get_core_session)]


@router.post("", response_model=OrderRead, status_code=status.HTTP_201_CREATED)
async def create_order(
    data: OrderCreate,
    db: DbDep,
    user: Annotated[User, Depends(require_roles("admin", "manager", "partner"))],
) -> OrderRead:
    # A partner may only create orders on behalf of their own company.
    if user.role.code == "partner":
        partner_id = user.partner_id
    else:
        partner_id = data.partner_id
    try:
        return await order_service.create_order(db, data, partner_id)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)
        )


@router.get("", response_model=list[OrderRead])
async def list_orders(
    db: DbDep,
    user: Annotated[User, Depends(get_current_user)],
) -> list[OrderRead]:
    # Partners see only their own orders; staff sees everything.
    if user.role.code == "partner":
        return await order_service.list_orders(db, partner_id=user.partner_id)
    return await order_service.list_orders(db)


@router.get("/{order_id}", response_model=OrderRead)
async def get_order(
    order_id: int,
    db: DbDep,
    user: Annotated[User, Depends(get_current_user)],
) -> OrderRead:
    order = await order_service.get_order(db, order_id)
    if order is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Order not found"
        )
    if user.role.code == "partner" and order.partner_id != user.partner_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden"
        )
    return order


@router.patch(
    "/{order_id}/status",
    response_model=OrderRead,
    dependencies=[Depends(require_roles("admin", "manager"))],
)
async def change_order_status(
    order_id: int, data: OrderStatusUpdate, db: DbDep
) -> OrderRead:
    order = await order_service.get_order(db, order_id)
    if order is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Order not found"
        )
    try:
        return await order_service.change_status(db, order, data.status)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail=str(exc)
        )
