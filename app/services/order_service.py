import uuid
from datetime import datetime, timezone
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.order import Order, OrderItem
from app.schemas.order import OrderCreate
from app.services import pricing_service

# Order state machine: allowed target statuses per current status.
ALLOWED_TRANSITIONS: dict[str, set[str]] = {
    "new": {"confirmed", "cancelled"},
    "confirmed": {"in_progress", "cancelled"},
    "in_progress": {"done", "cancelled"},
    "done": {"closed"},
    "closed": set(),
    "cancelled": set(),
}


async def get_order(db: AsyncSession, order_id: int) -> Order | None:
    stmt = (
        select(Order)
        .options(selectinload(Order.items))
        .where(Order.id == order_id)
    )
    return (await db.execute(stmt)).scalar_one_or_none()


async def list_orders(
    db: AsyncSession,
    partner_id: int | None = None,
    limit: int = 100,
    offset: int = 0,
) -> list[Order]:
    stmt = (
        select(Order)
        .options(selectinload(Order.items))
        .order_by(Order.created_at.desc())
        .limit(limit)
        .offset(offset)
    )
    if partner_id is not None:
        stmt = stmt.where(Order.partner_id == partner_id)
    return list((await db.execute(stmt)).scalars().all())


async def create_order(
    db: AsyncSession, data: OrderCreate, partner_id: int | None
) -> Order:
    # Колонка number ограничена VARCHAR(32). Финальный номер вида
    # ORD-2026-00001 короткий, но временный нужен только до получения id,
    # поэтому берём короткий кусок uuid (tmp-xxxxxxxx = 12 символов).
    order = Order(
        client_ref=data.client_ref,
        partner_id=partner_id,
        manager_id=data.manager_id,
        status="new",
        number=f"tmp-{uuid.uuid4().hex[:8]}",
        total_amount=Decimal("0.00"),
    )
    db.add(order)
    await db.flush()  # assigns order.id

    total = Decimal("0.00")
    for item in data.items:
        price = await pricing_service.resolve_price(db, item.service_id, partner_id)
        line_sum = price * item.qty
        order.items.append(
            OrderItem(
                service_id=item.service_id,
                qty=item.qty,
                price=price,
                sum=line_sum,
            )
        )
        total += line_sum

    order.total_amount = total
    order.number = f"ORD-{datetime.now(timezone.utc).year}-{order.id:05d}"
    await db.commit()

    created = await get_order(db, order.id)
    assert created is not None
    return created


async def change_status(
    db: AsyncSession, order: Order, new_status: str
) -> Order:
    allowed = ALLOWED_TRANSITIONS.get(order.status, set())
    if new_status not in allowed:
        raise ValueError(
            f"cannot transition from '{order.status}' to '{new_status}'"
        )
    order.status = new_status
    await db.commit()

    updated = await get_order(db, order.id)
    assert updated is not None
    return updated
