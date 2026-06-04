from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import CoreBase

if TYPE_CHECKING:
    from app.models.user import User


class Partner(CoreBase):
    """Company (legal entity): insurance / corporate / allied service."""

    __tablename__ = "partners"

    id: Mapped[int] = mapped_column(primary_key=True)
    org_name: Mapped[str] = mapped_column(String(255))
    inn: Mapped[str | None] = mapped_column(String(12), unique=True, nullable=True)
    type: Mapped[str] = mapped_column(String(32))
    contract_no: Mapped[str | None] = mapped_column(String(64), nullable=True)
    status: Mapped[str] = mapped_column(String(32), default="active")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    users: Mapped[list[User]] = relationship(back_populates="partner")
