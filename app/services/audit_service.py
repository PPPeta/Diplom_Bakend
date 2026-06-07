from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import AnalyticsSessionLocal
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


async def log_event(
    *,
    action: str,
    user_id: int | None = None,
    user_role: str | None = None,
    entity_type: str | None = None,
    entity_id: int | None = None,
    details: str | None = None,
) -> None:
    """Удобная обёртка: пишет событие в собственной сессии аналитической БД.

    Эндпоинты работают с core-сессией, а аудит лежит в отдельной БД, поэтому
    открываем здесь свою сессию. Аудит не должен ронять основную операцию,
    поэтому любые ошибки тут просто гасим.
    """
    try:
        async with AnalyticsSessionLocal() as session:
            await write_log(
                session,
                action=action,
                user_id=user_id,
                user_role=user_role,
                entity_type=entity_type,
                entity_id=entity_id,
                details=details,
            )
    except Exception:
        # Журнал аудита не критичен для ответа пользователю — не падаем.
        pass


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
