from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field


class OrderItemCreate(BaseModel):
    service_id: int
    qty: int = Field(default=1, ge=1)


class OrderCreate(BaseModel):
    client_ref: str | None = None
    partner_id: int | None = None
    manager_id: int | None = None
    items: list[OrderItemCreate] = Field(min_length=1)


class OrderStatusUpdate(BaseModel):
    status: str


class OrderItemRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    service_id: int
    qty: int
    price: Decimal
    sum: Decimal


class OrderRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    number: str
    client_ref: str | None = None
    partner_id: int | None = None
    manager_id: int | None = None
    status: str
    total_amount: Decimal
    created_at: datetime
    items: list[OrderItemRead] = []
