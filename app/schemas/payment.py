from datetime import datetime
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class PaymentCreate(BaseModel):
    order_id: int
    partner_id: int | None = None
    amount: Decimal = Field(gt=0)
    direction: Literal["in", "out"]
    kind: Literal["payment", "commission"]


class PaymentStatusUpdate(BaseModel):
    status: Literal["pending", "paid"]


class YooKassaCheckoutCreate(BaseModel):
    """Запрос на создание оплаты заказа через ЮKassa."""

    order_id: int


class PaymentRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    order_id: int
    partner_id: int | None = None
    amount: Decimal
    direction: str
    kind: str
    status: str
    paid_at: datetime | None = None
    created_at: datetime
    provider: str | None = None
    external_id: str | None = None
    confirmation_url: str | None = None
    description: str | None = None
