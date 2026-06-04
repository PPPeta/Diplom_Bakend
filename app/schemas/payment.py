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
