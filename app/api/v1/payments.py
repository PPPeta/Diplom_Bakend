from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.deps import require_roles
from app.db.session import get_core_session
from app.models.user import User
from app.schemas.payment import (
    PaymentCreate,
    PaymentRead,
    PaymentStatusUpdate,
    YooKassaCheckoutCreate,
)
from app.services import audit_service, order_service, payment_service
from app.services.yookassa_service import YooKassaError

router = APIRouter(prefix="/payments", tags=["payments"])

DbDep = Annotated[AsyncSession, Depends(get_core_session)]
FinanceViewer = Annotated[
    User, Depends(require_roles("admin", "manager", "partner"))
]


@router.post(
    "",
    response_model=PaymentRead,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_roles("admin", "manager"))],
)
async def create_payment(data: PaymentCreate, db: DbDep) -> PaymentRead:
    return await payment_service.create_payment(db, data)


@router.post(
    "/yookassa/checkout",
    response_model=PaymentRead,
    status_code=status.HTTP_201_CREATED,
)
async def create_yookassa_checkout(
    data: YooKassaCheckoutCreate, db: DbDep, user: FinanceViewer
) -> PaymentRead:
    """Создаёт оплату заказа через ЮKassa и возвращает ссылку на оплату."""
    if not settings.yookassa_enabled:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Приём оплаты через ЮKassa не настроен",
        )
    order = await order_service.get_order(db, data.order_id)
    if order is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Order not found"
        )
    # Партнёр может оплачивать только свои заказы.
    if user.role.code == "partner" and order.partner_id != user.partner_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden"
        )
    try:
        payment = await payment_service.create_yookassa_checkout(
            db, order, settings.YOOKASSA_RETURN_URL
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)
        )
    except YooKassaError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY, detail=str(exc)
        )
    await audit_service.log_event(
        action="payment.yookassa.created",
        user_id=user.id,
        user_role=user.role.code,
        entity_type="payment",
        entity_id=payment.id,
        details=f"Заказ {order.number}, сумма {payment.amount}",
    )
    return payment


@router.get("", response_model=list[PaymentRead])
async def list_payments(
    db: DbDep, user: FinanceViewer, order_id: int | None = None
) -> list[PaymentRead]:
    # Partners only see their own settlements.
    if user.role.code == "partner":
        return await payment_service.list_payments(
            db, order_id=order_id, partner_id=user.partner_id
        )
    return await payment_service.list_payments(db, order_id=order_id)


@router.get("/{payment_id}", response_model=PaymentRead)
async def get_payment(
    payment_id: int, db: DbDep, user: FinanceViewer
) -> PaymentRead:
    payment = await payment_service.get_payment(db, payment_id)
    if payment is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Payment not found"
        )
    if user.role.code == "partner" and payment.partner_id != user.partner_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden"
        )
    return payment


@router.patch(
    "/{payment_id}/status",
    response_model=PaymentRead,
    dependencies=[Depends(require_roles("admin", "manager"))],
)
async def update_payment_status(
    payment_id: int, data: PaymentStatusUpdate, db: DbDep
) -> PaymentRead:
    payment = await payment_service.get_payment(db, payment_id)
    if payment is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Payment not found"
        )
    return await payment_service.set_status(db, payment, data.status)


@router.post("/{payment_id}/yookassa/sync", response_model=PaymentRead)
async def sync_yookassa_payment(
    payment_id: int, db: DbDep, user: FinanceViewer
) -> PaymentRead:
    """Опрашивает статус платежа в ЮKassa и обновляет локальный платёж."""
    payment = await payment_service.get_payment(db, payment_id)
    if payment is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Payment not found"
        )
    if user.role.code == "partner" and payment.partner_id != user.partner_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden"
        )
    was_paid = payment.status == "paid"
    try:
        payment = await payment_service.sync_yookassa_payment(db, payment)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)
        )
    except YooKassaError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY, detail=str(exc)
        )
    if payment.status == "paid" and not was_paid:
        await audit_service.log_event(
            action="payment.paid",
            user_id=user.id,
            user_role=user.role.code,
            entity_type="payment",
            entity_id=payment.id,
            details=f"ЮKassa: заказ #{payment.order_id}, сумма {payment.amount}",
        )
    return payment
