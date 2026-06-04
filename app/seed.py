"""Idempotent seed / bootstrap data for the prototype.

Run inside the api container (after migrations are applied):

    docker compose exec api alembic upgrade head
    docker compose exec api python -m app.seed

Seeds:
    * service catalog (ritual services with base prices)
    * system administrator account
    * demo B2B partner (insurance company) with a favorable partner price
      list and commercial terms, plus a partner-admin login

Roles/permissions are created by migration 0001, not here.
Running the script multiple times will not create duplicates.
"""

from __future__ import annotations

import asyncio
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import hash_password
from app.db.session import CoreSessionLocal
from app.models.partner import Partner
from app.models.pricing import PartnerTerm, PriceList, PriceListItem
from app.models.role import Role
from app.models.service import ServiceCatalog
from app.models.user import User

# --- demo credentials -------------------------------------------------------
ADMIN_EMAIL = "admin@vp.local"
ADMIN_PASSWORD = "admin12345"
PARTNER_ADMIN_EMAIL = "partner@vp.local"
PARTNER_ADMIN_PASSWORD = "partner12345"

PARTNER_ORG_NAME = "\u0421\u041a \u00ab\u041d\u0430\u0434\u0451\u0436\u043d\u0430\u044f \u0437\u0430\u0449\u0438\u0442\u0430\u00bb"
PARTNER_PRICE_LIST_CODE = "PL-PARTNER-NZ"

# code, name, category, base_price
SERVICES: list[tuple[str, str, str, str]] = [
    ("COFFIN-STD", "\u0413\u0440\u043e\u0431 \u0441\u0442\u0430\u043d\u0434\u0430\u0440\u0442", "\u0420\u0438\u0442\u0443\u0430\u043b\u044c\u043d\u044b\u0435 \u043f\u0440\u0438\u043d\u0430\u0434\u043b\u0435\u0436\u043d\u043e\u0441\u0442\u0438", "12000.00"),
    ("COFFIN-LUX", "\u0413\u0440\u043e\u0431 \u043f\u0440\u0435\u043c\u0438\u0443\u043c", "\u0420\u0438\u0442\u0443\u0430\u043b\u044c\u043d\u044b\u0435 \u043f\u0440\u0438\u043d\u0430\u0434\u043b\u0435\u0436\u043d\u043e\u0441\u0442\u0438", "45000.00"),
    ("WREATH", "\u0412\u0435\u043d\u043e\u043a \u0442\u0440\u0430\u0443\u0440\u043d\u044b\u0439", "\u0420\u0438\u0442\u0443\u0430\u043b\u044c\u043d\u044b\u0435 \u043f\u0440\u0438\u043d\u0430\u0434\u043b\u0435\u0436\u043d\u043e\u0441\u0442\u0438", "2500.00"),
    ("HEARSE", "\u041a\u0430\u0442\u0430\u0444\u0430\u043b\u043a (\u043f\u043e \u0433\u043e\u0440\u043e\u0434\u0443)", "\u0422\u0440\u0430\u043d\u0441\u043f\u043e\u0440\u0442", "6000.00"),
    ("AGENT", "\u0423\u0441\u043b\u0443\u0433\u0438 \u0440\u0438\u0442\u0443\u0430\u043b\u044c\u043d\u043e\u0433\u043e \u0430\u0433\u0435\u043d\u0442\u0430", "\u041e\u0440\u0433\u0430\u043d\u0438\u0437\u0430\u0446\u0438\u044f", "8000.00"),
    ("GRAVE-DIG", "\u041a\u043e\u043f\u043a\u0430 \u043c\u043e\u0433\u0438\u043b\u044b", "\u041a\u043b\u0430\u0434\u0431\u0438\u0449\u0435\u043d\u0441\u043a\u0438\u0435 \u0440\u0430\u0431\u043e\u0442\u044b", "9000.00"),
    ("CREMATION", "\u041a\u0440\u0435\u043c\u0430\u0446\u0438\u044f", "\u041a\u043b\u0430\u0434\u0431\u0438\u0449\u0435\u043d\u0441\u043a\u0438\u0435 \u0440\u0430\u0431\u043e\u0442\u044b", "18000.00"),
    ("FAREWELL-HALL", "\u0417\u0430\u043b \u043f\u0440\u043e\u0449\u0430\u043d\u0438\u044f (1 \u0447\u0430\u0441)", "\u041e\u0440\u0433\u0430\u043d\u0438\u0437\u0430\u0446\u0438\u044f", "5000.00"),
    ("EMBALMING", "\u0411\u0430\u043b\u044c\u0437\u0430\u043c\u0438\u0440\u043e\u0432\u0430\u043d\u0438\u0435", "\u041f\u043e\u0434\u0433\u043e\u0442\u043e\u0432\u043a\u0430", "7000.00"),
    ("MONUMENT-STD", "\u041f\u0430\u043c\u044f\u0442\u043d\u0438\u043a \u0433\u0440\u0430\u043d\u0438\u0442 \u0441\u0442\u0430\u043d\u0434\u0430\u0440\u0442", "\u041f\u0430\u043c\u044f\u0442\u043d\u0438\u043a\u0438", "35000.00"),
]

# Favorable partner prices (\u00ab\u0432\u044b\u0433\u043e\u0434\u043d\u044b\u0435 \u0441\u0434\u0435\u043b\u043a\u0438\u00bb), keyed by service code.
PARTNER_PRICES: dict[str, str] = {
    "COFFIN-STD": "10000.00",
    "HEARSE": "5000.00",
    "AGENT": "6500.00",
}


async def _get_role(db: AsyncSession, code: str) -> Role:
    role = (
        await db.execute(select(Role).where(Role.code == code))
    ).scalar_one_or_none()
    if role is None:
        raise RuntimeError(
            f"Role '{code}' not found \u2014 run migrations first "
            "(alembic upgrade head)"
        )
    return role


async def seed_services(db: AsyncSession) -> dict[str, ServiceCatalog]:
    catalog: dict[str, ServiceCatalog] = {}
    for code, name, category, price in SERVICES:
        service = (
            await db.execute(
                select(ServiceCatalog).where(ServiceCatalog.code == code)
            )
        ).scalar_one_or_none()
        if service is None:
            service = ServiceCatalog(
                code=code,
                name=name,
                category=category,
                base_price=Decimal(price),
                is_active=True,
            )
            db.add(service)
        catalog[code] = service
    await db.flush()
    return catalog


async def seed_admin(db: AsyncSession) -> None:
    existing = (
        await db.execute(select(User).where(User.email == ADMIN_EMAIL))
    ).scalar_one_or_none()
    if existing is not None:
        return
    admin_role = await _get_role(db, "admin")
    db.add(
        User(
            email=ADMIN_EMAIL,
            password_hash=hash_password(ADMIN_PASSWORD),
            full_name="\u0421\u0438\u0441\u0442\u0435\u043c\u043d\u044b\u0439 \u0430\u0434\u043c\u0438\u043d\u0438\u0441\u0442\u0440\u0430\u0442\u043e\u0440",
            is_active=True,
            role_id=admin_role.id,
        )
    )


async def seed_partner(
    db: AsyncSession, catalog: dict[str, ServiceCatalog]
) -> None:
    partner = (
        await db.execute(
            select(Partner).where(Partner.org_name == PARTNER_ORG_NAME)
        )
    ).scalar_one_or_none()
    if partner is None:
        partner = Partner(
            org_name=PARTNER_ORG_NAME,
            inn="7701234567",
            type="insurance",
            contract_no="VP-2026-001",
            status="active",
        )
        db.add(partner)
        await db.flush()

    # Favorable partner price list (\u00ab\u0432\u044b\u0433\u043e\u0434\u043d\u044b\u0435 \u0441\u0434\u0435\u043b\u043a\u0438\u00bb).
    price_list = (
        await db.execute(
            select(PriceList).where(
                PriceList.code == PARTNER_PRICE_LIST_CODE
            )
        )
    ).scalar_one_or_none()
    if price_list is None:
        price_list = PriceList(
            code=PARTNER_PRICE_LIST_CODE,
            name="\u041f\u0430\u0440\u0442\u043d\u0451\u0440\u0441\u043a\u0438\u0439 \u043f\u0440\u0430\u0439\u0441 \u2014 \u041d\u0430\u0434\u0451\u0436\u043d\u0430\u044f \u0437\u0430\u0449\u0438\u0442\u0430",
            kind="partner",
            partner_id=partner.id,
            is_active=True,
        )
        db.add(price_list)
        await db.flush()
        for code, price in PARTNER_PRICES.items():
            db.add(
                PriceListItem(
                    price_list_id=price_list.id,
                    service_id=catalog[code].id,
                    price=Decimal(price),
                )
            )

    partner.price_list_id = price_list.id

    term = (
        await db.execute(
            select(PartnerTerm).where(PartnerTerm.partner_id == partner.id)
        )
    ).scalar_one_or_none()
    if term is None:
        db.add(
            PartnerTerm(
                partner_id=partner.id,
                discount_pct=Decimal("10.00"),
                commission_pct=Decimal("5.00"),
                priority=10,
                notes="\u0411\u0430\u0437\u043e\u0432\u044b\u0435 \u0443\u0441\u043b\u043e\u0432\u0438\u044f \u0441\u0442\u0440\u0430\u0445\u043e\u0432\u043e\u0433\u043e \u043f\u0430\u0440\u0442\u043d\u0451\u0440\u0430",
            )
        )

    existing_user = (
        await db.execute(
            select(User).where(User.email == PARTNER_ADMIN_EMAIL)
        )
    ).scalar_one_or_none()
    if existing_user is None:
        partner_role = await _get_role(db, "partner")
        db.add(
            User(
                email=PARTNER_ADMIN_EMAIL,
                password_hash=hash_password(PARTNER_ADMIN_PASSWORD),
                full_name="\u041a\u043e\u043d\u0442\u0430\u043a\u0442\u043d\u043e\u0435 \u043b\u0438\u0446\u043e \u043f\u0430\u0440\u0442\u043d\u0451\u0440\u0430",
                is_active=True,
                is_partner_admin=True,
                role_id=partner_role.id,
                partner_id=partner.id,
            )
        )


async def main() -> None:
    async with CoreSessionLocal() as db:
        catalog = await seed_services(db)
        await seed_admin(db)
        await seed_partner(db, catalog)
        await db.commit()
    print("\u2705 Seed complete")
    print(f"   admin:   {ADMIN_EMAIL} / {ADMIN_PASSWORD}")
    print(f"   partner: {PARTNER_ADMIN_EMAIL} / {PARTNER_ADMIN_PASSWORD}")


if __name__ == "__main__":
    asyncio.run(main())
