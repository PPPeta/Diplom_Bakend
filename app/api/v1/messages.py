from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_user
from app.db.session import get_core_session
from app.models.order import Order
from app.models.user import User
from app.schemas.message import MessageCreate, MessageRead
from app.services import message_service, order_service

router = APIRouter(prefix="/orders/{order_id}/messages", tags=["messages"])

DbDep = Annotated[AsyncSession, Depends(get_core_session)]
UserDep = Annotated[User, Depends(get_current_user)]


async def _order_or_error(db: AsyncSession, order_id: int, user: User) -> Order:
    order = await order_service.get_order(db, order_id)
    if order is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Order not found"
        )
    # Partners may only access threads on their own orders.
    if user.role.code == "partner" and order.partner_id != user.partner_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden"
        )
    return order


@router.get("", response_model=list[MessageRead])
async def list_messages(
    order_id: int, db: DbDep, user: UserDep
) -> list[MessageRead]:
    await _order_or_error(db, order_id, user)
    return await message_service.list_for_order(db, order_id)


@router.post("", response_model=MessageRead, status_code=status.HTTP_201_CREATED)
async def post_message(
    order_id: int, data: MessageCreate, db: DbDep, user: UserDep
) -> MessageRead:
    await _order_or_error(db, order_id, user)
    return await message_service.create_message(db, order_id, user, data)
