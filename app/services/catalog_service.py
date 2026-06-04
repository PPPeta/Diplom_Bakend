from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.service import ServiceCatalog
from app.schemas.service import ServiceCreate, ServiceUpdate


async def list_services(
    db: AsyncSession,
    only_active: bool = False,
    limit: int = 100,
    offset: int = 0,
) -> list[ServiceCatalog]:
    stmt = (
        select(ServiceCatalog)
        .order_by(ServiceCatalog.name.asc())
        .limit(limit)
        .offset(offset)
    )
    if only_active:
        stmt = stmt.where(ServiceCatalog.is_active.is_(True))
    return list((await db.execute(stmt)).scalars().all())


async def get_service(db: AsyncSession, service_id: int) -> ServiceCatalog | None:
    return await db.get(ServiceCatalog, service_id)


async def create_service(db: AsyncSession, data: ServiceCreate) -> ServiceCatalog:
    existing = (
        await db.execute(
            select(ServiceCatalog).where(ServiceCatalog.code == data.code)
        )
    ).scalar_one_or_none()
    if existing is not None:
        raise ValueError("service code already exists")
    service = ServiceCatalog(**data.model_dump())
    db.add(service)
    await db.commit()
    await db.refresh(service)
    return service


async def update_service(
    db: AsyncSession, service: ServiceCatalog, data: ServiceUpdate
) -> ServiceCatalog:
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(service, field, value)
    await db.commit()
    await db.refresh(service)
    return service


async def delete_service(db: AsyncSession, service: ServiceCatalog) -> None:
    await db.delete(service)
    await db.commit()
