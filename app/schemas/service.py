from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field


class ServiceCreate(BaseModel):
    code: str
    name: str
    category: str | None = None
    base_price: Decimal = Field(default=Decimal("0.00"), ge=0)
    is_active: bool = True


class ServiceUpdate(BaseModel):
    name: str | None = None
    category: str | None = None
    base_price: Decimal | None = Field(default=None, ge=0)
    is_active: bool | None = None


class ServiceRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    code: str
    name: str
    category: str | None = None
    base_price: Decimal
    is_active: bool
