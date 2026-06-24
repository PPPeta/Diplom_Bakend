from datetime import datetime, timezone

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.order import Order
from app.models.payment import Payment
from app.schemas.payment import PaymentCreate
from app.services import yookassa_service

# Маппинг статусов ЮKassa -> локальный статус платежа.
_YK_STATUS_MAP = {
    "succeeded": "paid",
    "canceled": "canceled",
    "pending": "pending",
    "waiting_for_capture": "pending",
}


class OrderAlreadyPaidError(RuntimeError):
    """Заказ уже полностью оплачен — повторная оплата не требуется."""


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


async def _order_paid_total(db: AsyncSession, order_id: int):
    """Сумма успешно прошедших входящих оплат по заказу."""
    stmt = select(func.coalesce(func.sum(Payment.amount), 0)).where(
        Payment.order_id == order_id,
        Payment.direction == "in",
        Payment.status == "paid",
    )
    return (await db.execute(stmt)).scalar_one()


async def set_status(db: AsyncSession, payment: Payment, status: str) -> Payment:
    payment.status = status
    payment.paid_at = datetime.now(timezone.utc) if status == "paid" else None
    await db.commit()
    await db.refresh(payment)
    return payment


async def create_yookassa_checkout(
    db: AsyncSession, order: Order, return_url: str
) -> Payment:
    """Создаёт локальный платёж и платёж в ЮKassa, возвращает платёж с ссылкой на оплату.

    Значения заказа фиксируем в локальные переменные ДО commit, чтобы не
    дёргать ленивые связи на уже сохранённом объекте (иначе MissingGreenlet).
    """
    amount = order.total_amount
    order_id = order.id
    partner_id = order.partner_id
    number = order.number

    if amount is None or amount <= 0:
        raise ValueError("Сумма заказа должна быть больше нуля")

    # Не создаём новую оплату, если заказ уже полностью оплачен.
    paid_total = await _order_paid_total(db, order_id)
    if paid_total >= amount:
        raise OrderAlreadyPaidError("Заказ уже полностью оплачен")

    description = f"Оплата заказа {number}"
    payment = Payment(
        order_id=order_id,
        partner_id=partner_id,
        amount=amount,
        direction="in",
        kind="payment",
        status="pending",
        provider="yookassa",
        description=description,
    )
    db.add(payment)
    await db.flush()  # назначает payment.id
    local_id = payment.id

    try:
        result = await yookassa_service.create_payment(
            amount=amount,
            description=description,
            return_url=return_url,
            metadata={"order_id": str(order_id), "payment_id": str(local_id)},
        )
    except Exception:
        await db.rollback()
        raise

    payment.external_id = result.get("id")
    payment.confirmation_url = result.get("confirmation_url")
    # Если ЮKassa сразу вернула финальный статус — отразим его локально.
    if _YK_STATUS_MAP.get(result.get("status") or "") == "paid":
        payment.status = "paid"
        payment.paid_at = datetime.now(timezone.utc)
    await db.commit()
    await db.refresh(payment)
    return payment


async def sync_yookassa_payment(
    db: AsyncSession, payment: Payment
) -> Payment:
    """Запрашивает актуальный статус платежа в ЮKassa и обновляет локальный."""
    if payment.provider != "yookassa" or not payment.external_id:
        raise ValueError("Платёж не относится к ЮKassa")
    if payment.status == "paid":
        return payment

    result = await yookassa_service.get_payment(payment.external_id)
    mapped = _YK_STATUS_MAP.get(result.get("status") or "")
    if mapped == "paid":
        payment.status = "paid"
        payment.paid_at = datetime.now(timezone.utc)
    elif mapped == "canceled":
        payment.status = "canceled"
        payment.paid_at = None
    # pending / waiting_for_capture — оставляем как есть.
    await db.commit()
    await db.refresh(payment)
    return payment
