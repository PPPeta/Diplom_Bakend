from __future__ import annotations

from datetime import datetime
from decimal import Decimal

from sqlalchemy import DateTime, ForeignKey, Numeric, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import CoreBase


class Payment(CoreBase):
    """Mutual settlement entry for an order (payment in / commission out)."""

    __tablename__ = "payments"

    id: Mapped[int] = mapped_column(primary_key=True)
    order_id: Mapped[int] = mapped_column(
        ForeignKey("orders.id", ondelete="CASCADE")
    )
    partner_id: Mapped[int | None] = mapped_column(
        ForeignKey("partners.id", ondelete="SET NULL"), nullable=True
    )
    amount: Mapped[Decimal] = mapped_column(Numeric(12, 2))
    direction: Mapped[str] = mapped_column(String(8))  # in | out
    kind: Mapped[str] = mapped_column(String(16))  # payment | commission
    status: Mapped[str] = mapped_column(String(20), default="pending")

    # Внешний платёжный провайдер (например, "yookassa").
    provider: Mapped[str | None] = mapped_column(String(20), nullable=True)
    # Идентификатор платежа на стороне провайдера.
    external_id: Mapped[str | None] = mapped_column(
        String(64), nullable=True, index=True
    )
    # Ссылка на страницу оплаты (confirmation_url у ЮKassa).
    confirmation_url: Mapped[str | None] = mapped_column(String(512), nullable=True)
    # Назначение платежа (отображается покупателю).
    description: Mapped[str | None] = mapped_column(String(255), nullable=True)

    paid_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
