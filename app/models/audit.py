from __future__ import annotations

from datetime import datetime

from sqlalchemy import BigInteger, DateTime, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import AnalyticsBase


class AuditLog(AnalyticsBase):
    """Запись аудита: кто, что и над каким объектом сделал.

    Лежит в отдельной аналитической БД, чтобы не мешать оперативным данным.
    """

    __tablename__ = "audit_logs"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)

    # Кто сделал действие (id пользователя из core_db; без FK, т.к. другая БД)
    user_id: Mapped[int | None] = mapped_column(Integer, nullable=True, index=True)
    user_role: Mapped[str | None] = mapped_column(String(50), nullable=True)

    # Что произошло: например "order.status_changed", "auth.login"
    action: Mapped[str] = mapped_column(String(100), index=True)

    # Над каким объектом: тип ("order") и его id
    entity_type: Mapped[str | None] = mapped_column(String(50), nullable=True)
    entity_id: Mapped[int | None] = mapped_column(Integer, nullable=True)

    # Свободное текстовое описание/детали
    details: Mapped[str | None] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), index=True
    )
