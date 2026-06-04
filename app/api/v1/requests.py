from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import require_roles
from app.db.session import get_core_session
from app.schemas.request import RequestCreate, RequestRead, RequestStatusUpdate
from app.services import request_service

router = APIRouter(prefix="/requests", tags=["requests"])

DbDep = Annotated[AsyncSession, Depends(get_core_session)]


@router.post("", response_model=RequestRead, status_code=status.HTTP_201_CREATED)
async def create_request(data: RequestCreate, db: DbDep) -> RequestRead:
    """Public endpoint: a private client leaves a lead from the site."""
    if not data.pdn_consent:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="\u0421\u043e\u0433\u043b\u0430\u0441\u0438\u0435 \u043d\u0430 \u043e\u0431\u0440\u0430\u0431\u043e\u0442\u043a\u0443 \u043f\u0435\u0440\u0441\u043e\u043d\u0430\u043b\u044c\u043d\u044b\u0445 \u0434\u0430\u043d\u043d\u044b\u0445 \u043e\u0431\u044f\u0437\u0430\u0442\u0435\u043b\u044c\u043d\u043e",
        )
    return await request_service.create_request(db, data)


@router.get(
    "",
    response_model=list[RequestRead],
    dependencies=[Depends(require_roles("admin", "manager"))],
)
async def list_requests(
    db: DbDep, status_filter: str | None = None
) -> list[RequestRead]:
    return await request_service.list_requests(db, status=status_filter)


@router.get(
    "/{request_id}",
    response_model=RequestRead,
    dependencies=[Depends(require_roles("admin", "manager"))],
)
async def get_request(request_id: int, db: DbDep) -> RequestRead:
    request = await request_service.get_request(db, request_id)
    if request is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Request not found"
        )
    return request


@router.patch(
    "/{request_id}",
    response_model=RequestRead,
    dependencies=[Depends(require_roles("admin", "manager"))],
)
async def update_request_status(
    request_id: int, data: RequestStatusUpdate, db: DbDep
) -> RequestRead:
    request = await request_service.get_request(db, request_id)
    if request is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Request not found"
        )
    return await request_service.set_status(db, request, data.status)
