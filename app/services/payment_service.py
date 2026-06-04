from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.payment import Payment
from app.schemas.payment import PaymentCreate


async def create_payment(db: AsyncSession, data: PaymentCreate) -> Payment:
    payment = Payment(**data.model_dump())
    db.add(payment)
    await db.commit()
    await db.refresh(payment)
    return payment


async def list_payments(
    db: AsyncSession,
    order_id: int | None = None,
    partner_id: int | None = None,
    limit: int = 100,
    offset: int = 0,
) -> list[Payment]:
    stmt = (
        select(Payment)
        .order_by(Payment.created_at.desc())
        .limit(limit)
        .offset(offset)
    )
    if order_id is not None:
        stmt = stmt.where(Payment.order_id == order_id)
    if partner_id is not None:
        stmt = stmt.where(Payment.partner_id == partner_id)
    return list((await db.execute(stmt)).scalars().all())


async def get_payment(db: AsyncSession, payment_id: int) -> Payment | None:
    return await db.get(Payment, payment_id)


async def set_status(db: AsyncSession, payment: Payment, status: str) -> Payment:
    payment.status = status
    payment.paid_at = datetime.now(timezone.utc) if status == "paid" else None
    await db.commit()
    await db.refresh(payment)
    return payment
