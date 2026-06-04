from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import require_roles
from app.db.session import get_core_session
from app.models.user import User
from app.schemas.payment import PaymentCreate, PaymentRead, PaymentStatusUpdate
from app.services import payment_service

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
