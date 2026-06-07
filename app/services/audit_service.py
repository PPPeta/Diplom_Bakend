from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.audit import AuditLog


async def write_log(
    db: AsyncSession,
    *,
    action: str,
    user_id: int | None = None,
    user_role: str | None = None,
    entity_type: str | None = None,
    entity_id: int | None = None,
    details: str | None = None,
) -> None:
    """Сохранить одну запись аудита в аналитическую БД.

    Пишем максимально просто: создаём объект и коммитим.
    Параметры передаём по имени (звёздочка), чтобы вызовы читались понятно.
    """
    log = AuditLog(
        action=action,
        user_id=user_id,
        user_role=user_role,
        entity_type=entity_type,
        entity_id=entity_id,
        details=details,
    )
    db.add(log)
    await db.commit()


async def list_logs(
    db: AsyncSession,
    limit: int = 100,
    offset: int = 0,
) -> list[AuditLog]:
    """Вернуть последние записи аудита (для админ-панели)."""
    stmt = (
        select(AuditLog)
        .order_by(AuditLog.created_at.desc())
        .limit(limit)
        .offset(offset)
    )
    result = await db.execute(stmt)
    return list(result.scalars().all())
