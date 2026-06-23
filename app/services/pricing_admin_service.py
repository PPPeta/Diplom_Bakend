from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.partner import Partner
from app.models.pricing import PartnerTerm, PriceList, PriceListItem
from app.schemas.pricing import (
    PartnerTermCreate,
    PartnerTermUpdate,
    PriceListCreate,
    PriceListItemCreate,
    PriceListUpdate,
)

_ALLOWED_KINDS = {"base", "partner", "promo"}


# ---------- Price lists ----------
async def list_price_lists(
    db: AsyncSession,
    kind: str | None = None,
    partner_id: int | None = None,
) -> list[PriceList]:
    stmt = (
        select(PriceList)
        .options(selectinload(PriceList.items))
        .order_by(PriceList.id.asc())
    )
    if kind is not None:
        stmt = stmt.where(PriceList.kind == kind)
    if partner_id is not None:
        stmt = stmt.where(PriceList.partner_id == partner_id)
    return list((await db.execute(stmt)).scalars().all())


async def get_price_list(
    db: AsyncSession, price_list_id: int
) -> PriceList | None:
    stmt = (
        select(PriceList)
        .options(selectinload(PriceList.items))
        .where(PriceList.id == price_list_id)
    )
    return (await db.execute(stmt)).scalar_one_or_none()


async def create_price_list(
    db: AsyncSession, data: PriceListCreate
) -> PriceList:
    if data.kind not in _ALLOWED_KINDS:
        raise ValueError("kind must be one of: base, partner, promo")

    existing = (
        await db.execute(select(PriceList).where(PriceList.code == data.code))
    ).scalar_one_or_none()
    if existing is not None:
        raise ValueError("price list code already exists")

    if data.kind == "partner" and data.partner_id is None:
        raise ValueError("partner_id is required for a partner price list")
    if data.partner_id is not None:
        partner = await db.get(Partner, data.partner_id)
        if partner is None:
            raise ValueError("partner not found")

    price_list = PriceList(
        code=data.code,
        name=data.name,
        kind=data.kind,
        partner_id=data.partner_id,
        valid_from=data.valid_from,
        valid_to=data.valid_to,
        is_active=data.is_active,
        items=[
            PriceListItem(service_id=it.service_id, price=it.price)
            for it in data.items
        ],
    )
    db.add(price_list)
    await db.flush()
    new_id = price_list.id
    await db.commit()
    return await get_price_list(db, new_id)


async def update_price_list(
    db: AsyncSession, price_list: PriceList, data: PriceListUpdate
) -> PriceList:
    pl_id = price_list.id
    payload = data.model_dump(exclude_unset=True)

    if "kind" in payload and payload["kind"] not in _ALLOWED_KINDS:
        raise ValueError("kind must be one of: base, partner, promo")
    if "code" in payload and payload["code"] != price_list.code:
        existing = (
            await db.execute(
                select(PriceList).where(PriceList.code == payload["code"])
            )
        ).scalar_one_or_none()
        if existing is not None:
            raise ValueError("price list code already exists")
    if "partner_id" in payload and payload["partner_id"] is not None:
        partner = await db.get(Partner, payload["partner_id"])
        if partner is None:
            raise ValueError("partner not found")

    for field, value in payload.items():
        setattr(price_list, field, value)
    await db.commit()
    return await get_price_list(db, pl_id)


async def delete_price_list(db: AsyncSession, price_list: PriceList) -> None:
    await db.delete(price_list)
    await db.commit()


# ---------- Price list items ----------
async def replace_items(
    db: AsyncSession,
    price_list: PriceList,
    items: list[PriceListItemCreate],
) -> PriceList:
    pl_id = price_list.id
    existing_items = (
        (
            await db.execute(
                select(PriceListItem).where(
                    PriceListItem.price_list_id == pl_id
                )
            )
        )
        .scalars()
        .all()
    )
    for it in existing_items:
        await db.delete(it)
    for it in items:
        db.add(
            PriceListItem(
                price_list_id=pl_id,
                service_id=it.service_id,
                price=it.price,
            )
        )
    await db.commit()
    return await get_price_list(db, pl_id)


# ---------- Partner terms ----------
async def list_partner_terms(
    db: AsyncSession, partner_id: int
) -> list[PartnerTerm]:
    stmt = (
        select(PartnerTerm)
        .where(PartnerTerm.partner_id == partner_id)
        .order_by(PartnerTerm.priority.asc(), PartnerTerm.id.asc())
    )
    return list((await db.execute(stmt)).scalars().all())


async def get_partner_term(
    db: AsyncSession, term_id: int
) -> PartnerTerm | None:
    return await db.get(PartnerTerm, term_id)


async def create_partner_term(
    db: AsyncSession, partner_id: int, data: PartnerTermCreate
) -> PartnerTerm:
    partner = await db.get(Partner, partner_id)
    if partner is None:
        raise ValueError("partner not found")
    term = PartnerTerm(
        partner_id=partner_id,
        discount_pct=data.discount_pct,
        commission_pct=data.commission_pct,
        priority=data.priority,
        notes=data.notes,
    )
    db.add(term)
    await db.commit()
    await db.refresh(term)
    return term


async def update_partner_term(
    db: AsyncSession, term: PartnerTerm, data: PartnerTermUpdate
) -> PartnerTerm:
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(term, field, value)
    await db.commit()
    await db.refresh(term)
    return term


async def delete_partner_term(db: AsyncSession, term: PartnerTerm) -> None:
    await db.delete(term)
    await db.commit()


# ---------- Partner price list assignment ----------
async def set_partner_price_list(
    db: AsyncSession, partner: Partner, price_list_id: int | None
) -> Partner:
    if price_list_id is not None:
        pl = await db.get(PriceList, price_list_id)
        if pl is None:
            raise ValueError("price list not found")
    partner.price_list_id = price_list_id
    await db.commit()
    await db.refresh(partner)
    return partner
