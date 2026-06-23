from datetime import date
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field


# ---------- Price list items ----------
class PriceListItemCreate(BaseModel):
    service_id: int
    price: Decimal = Field(ge=0)


class PriceListItemRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    service_id: int
    price: Decimal


# ---------- Price lists ----------
class PriceListCreate(BaseModel):
    code: str
    name: str
    kind: str = "base"  # base | partner | promo
    partner_id: int | None = None
    valid_from: date | None = None
    valid_to: date | None = None
    is_active: bool = True
    items: list[PriceListItemCreate] = Field(default_factory=list)


class PriceListUpdate(BaseModel):
    code: str | None = None
    name: str | None = None
    kind: str | None = None
    partner_id: int | None = None
    valid_from: date | None = None
    valid_to: date | None = None
    is_active: bool | None = None


class PriceListRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    code: str
    name: str
    kind: str
    partner_id: int | None = None
    valid_from: date | None = None
    valid_to: date | None = None
    is_active: bool
    items: list[PriceListItemRead] = Field(default_factory=list)


# ---------- Partner terms (discounts / commissions) ----------
class PartnerTermCreate(BaseModel):
    discount_pct: Decimal = Field(default=Decimal("0.00"), ge=0, le=100)
    commission_pct: Decimal = Field(default=Decimal("0.00"), ge=0, le=100)
    priority: int = 100
    notes: str | None = None


class PartnerTermUpdate(BaseModel):
    discount_pct: Decimal | None = Field(default=None, ge=0, le=100)
    commission_pct: Decimal | None = Field(default=None, ge=0, le=100)
    priority: int | None = None
    notes: str | None = None


class PartnerTermRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    partner_id: int
    discount_pct: Decimal
    commission_pct: Decimal
    priority: int
    notes: str | None = None


class PartnerPriceListUpdate(BaseModel):
    price_list_id: int | None = None
