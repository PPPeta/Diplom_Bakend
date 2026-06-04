"""Price resolution for an order line.

Precedence (decision 5):
    1) active promo deal of the partner (within validity window)
    2) partner personal price list
    3) base price from the catalog
    4) apply partner discount_pct (from partner_terms)

Private clients (partner_id is None) always get base_price.
The resolved price is snapshotted into order_items.price at order creation.
"""
from __future__ import annotations

from datetime import date
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.pricing import PartnerTerm, PriceList, PriceListItem
from app.models.service import ServiceCatalog

_CENTS = Decimal("0.01")


async def _price_from_lists(
    db: AsyncSession,
    service_id: int,
    partner_id: int,
    kinds: list[str],
    today: date,
) -> Decimal | None:
    stmt = (
        select(PriceListItem.price, PriceList.valid_from, PriceList.valid_to)
        .join(PriceList, PriceList.id == PriceListItem.price_list_id)
        .where(
            PriceListItem.service_id == service_id,
            PriceList.partner_id == partner_id,
            PriceList.kind.in_(kinds),
            PriceList.is_active.is_(True),
        )
        .order_by(PriceListItem.price.asc())
    )
    rows = (await db.execute(stmt)).all()
    valid = [
        price
        for price, valid_from, valid_to in rows
        if (valid_from is None or valid_from <= today)
        and (valid_to is None or valid_to >= today)
    ]
    return valid[0] if valid else None


async def resolve_price(
    db: AsyncSession, service_id: int, partner_id: int | None = None
) -> Decimal:
    service = await db.get(ServiceCatalog, service_id)
    if service is None:
        raise ValueError("service not found")

    base: Decimal = service.base_price
    if partner_id is None:
        return base

    today = date.today()

    promo = await _price_from_lists(db, service_id, partner_id, ["promo"], today)
    if promo is not None:
        return promo

    partner_price = await _price_from_lists(
        db, service_id, partner_id, ["partner"], today
    )
    price = partner_price if partner_price is not None else base

    term = (
        (
            await db.execute(
                select(PartnerTerm)
                .where(PartnerTerm.partner_id == partner_id)
                .order_by(PartnerTerm.priority.asc())
            )
        )
        .scalars()
        .first()
    )
    if term is not None and term.discount_pct:
        price = price * (Decimal(100) - term.discount_pct) / Decimal(100)

    return price.quantize(_CENTS)
