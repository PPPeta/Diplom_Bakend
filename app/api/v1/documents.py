from typing import Annotated

from fastapi import (
    APIRouter,
    Depends,
    File,
    Form,
    HTTPException,
    Response,
    UploadFile,
    status,
)
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import require_roles
from app.db.session import get_core_session
from app.models.order import Order
from app.models.user import User
from app.schemas.document import DocumentRead
from app.services import document_service

router = APIRouter(prefix="/documents", tags=["documents"])

DbDep = Annotated[AsyncSession, Depends(get_core_session)]
# Documents belong to orders (client PD) -> staff + owning partner only.
ViewerDep = Annotated[
    User, Depends(require_roles("admin", "manager", "partner"))
]
StaffDep = Annotated[User, Depends(require_roles("admin", "manager"))]

MAX_FILE_BYTES = 10 * 1024 * 1024  # 10 MB


async def _order_or_error(db: AsyncSession, order_id: int, user: User) -> Order:
    order = await document_service.order_for(db, order_id)
    if order is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Order not found"
        )
    if user.role.code == "partner" and order.partner_id != user.partner_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden"
        )
    return order


@router.get("", response_model=list[DocumentRead])
async def list_documents(
    db: DbDep, user: ViewerDep, order_id: int | None = None
) -> list[DocumentRead]:
    if order_id is not None:
        await _order_or_error(db, order_id, user)
        return await document_service.list_documents(db, order_id=order_id)
    # Partners see only documents on their own orders; staff sees all.
    if user.role.code == "partner":
        return await document_service.list_documents(
            db, partner_id=user.partner_id
        )
    return await document_service.list_documents(db)


@router.post("", response_model=DocumentRead, status_code=status.HTTP_201_CREATED)
async def upload_document(
    db: DbDep,
    user: StaffDep,
    order_id: Annotated[int, Form()],
    type: Annotated[str, Form()],
    file: Annotated[UploadFile, File()],
    number: Annotated[str | None, Form()] = None,
) -> DocumentRead:
    await _order_or_error(db, order_id, user)
    content = await file.read()
    if len(content) > MAX_FILE_BYTES:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail="File too large (max 10MB)",
        )
    return await document_service.create_document(
        db,
        order_id=order_id,
        type_=type,
        number=number,
        filename=file.filename,
        content_type=file.content_type,
        content=content,
        uploaded_by=user.id,
    )


@router.get("/{document_id}/download")
async def download_document(
    document_id: int, db: DbDep, user: ViewerDep
) -> Response:
    doc = await document_service.get_document(db, document_id)
    if doc is None or doc.content is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Document not found"
        )
    await _order_or_error(db, doc.order_id, user)
    filename = doc.filename or f"document-{doc.id}"
    return Response(
        content=doc.content,
        media_type=doc.content_type or "application/octet-stream",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.delete("/{document_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_document(
    document_id: int, db: DbDep, user: StaffDep
) -> None:
    doc = await document_service.get_document(db, document_id)
    if doc is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Document not found"
        )
    await document_service.delete_document(db, doc)
