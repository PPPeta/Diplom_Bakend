from __future__ import annotations

from datetime import date
from decimal import Decimal

from sqlalchemy import Boolean, Date, ForeignKey, Integer, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import CoreBase


class PriceList(CoreBase):
    """Price list: base / partner-specific / promo deal."""

    __tablename__ = "price_lists"

    id: Mapped[int] = mapped_column(primary_key=True)
    code: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(255))
    kind: Mapped[str] = mapped_column(String(16))  # base | partner | promo
    partner_id: Mapped[int | None] = mapped_column(
        ForeignKey("partners.id", ondelete="CASCADE"), nullable=True
    )
    valid_from: Mapped[date | None] = mapped_column(Date, nullable=True)
    valid_to: Mapped[date | None] = mapped_column(Date, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    items: Mapped[list[PriceListItem]] = relationship(
        back_populates="price_list",
        cascade="all, delete-orphan",
        lazy="selectin",
    )


class PriceListItem(CoreBase):
    __tablename__ = "price_list_items"

    id: Mapped[int] = mapped_column(primary_key=True)
    price_list_id: Mapped[int] = mapped_column(
        ForeignKey("price_lists.id", ondelete="CASCADE")
    )
    service_id: Mapped[int] = mapped_column(
        ForeignKey("service_catalog.id", ondelete="CASCADE")
    )
    price: Mapped[Decimal] = mapped_column(Numeric(12, 2))

    price_list: Mapped[PriceList] = relationship(back_populates="items")


class PartnerTerm(CoreBase):
    """Commercial terms for a partner: discount, commission, priority."""

    __tablename__ = "partner_terms"

    id: Mapped[int] = mapped_column(primary_key=True)
    partner_id: Mapped[int] = mapped_column(
        ForeignKey("partners.id", ondelete="CASCADE")
    )
    discount_pct: Mapped[Decimal] = mapped_column(
        Numeric(5, 2), default=Decimal("0.00")
    )
    commission_pct: Mapped[Decimal] = mapped_column(
        Numeric(5, 2), default=Decimal("0.00")
    )
    priority: Mapped[int] = mapped_column(Integer, default=100)
    notes: Mapped[str | None] = mapped_column(String(255), nullable=True)
