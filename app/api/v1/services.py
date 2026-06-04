from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import require_roles
from app.db.session import get_core_session
from app.schemas.service import ServiceCreate, ServiceRead, ServiceUpdate
from app.services import catalog_service

router = APIRouter(prefix="/services", tags=["catalog"])

DbDep = Annotated[AsyncSession, Depends(get_core_session)]


@router.get("", response_model=list[ServiceRead])
async def list_services(db: DbDep, only_active: bool = False) -> list[ServiceRead]:
    return await catalog_service.list_services(db, only_active=only_active)


@router.get("/{service_id}", response_model=ServiceRead)
async def get_service(service_id: int, db: DbDep) -> ServiceRead:
    service = await catalog_service.get_service(db, service_id)
    if service is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Service not found"
        )
    return service


@router.post(
    "",
    response_model=ServiceRead,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_roles("admin", "manager"))],
)
async def create_service(data: ServiceCreate, db: DbDep) -> ServiceRead:
    try:
        return await catalog_service.create_service(db, data)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)
        )


@router.patch(
    "/{service_id}",
    response_model=ServiceRead,
    dependencies=[Depends(require_roles("admin", "manager"))],
)
async def update_service(
    service_id: int, data: ServiceUpdate, db: DbDep
) -> ServiceRead:
    service = await catalog_service.get_service(db, service_id)
    if service is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Service not found"
        )
    return await catalog_service.update_service(db, service, data)


@router.delete(
    "/{service_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(require_roles("admin"))],
)
async def delete_service(service_id: int, db: DbDep) -> None:
    service = await catalog_service.get_service(db, service_id)
    if service is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Service not found"
        )
    await catalog_service.delete_service(db, service)
