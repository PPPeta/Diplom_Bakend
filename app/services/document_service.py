"""Documents attached to orders (contracts, invoices, acts). Files stored in-DB."""
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.document import Document
from app.models.order import Order


async def order_for(db: AsyncSession, order_id: int) -> Order | None:
    return await db.get(Order, order_id)


async def get_document(db: AsyncSession, document_id: int) -> Document | None:
    return await db.get(Document, document_id)


async def list_documents(
    db: AsyncSession,
    *,
    partner_id: int | None = None,
    order_id: int | None = None,
) -> list[Document]:
    stmt = select(Document).order_by(Document.created_at.desc())
    if order_id is not None:
        stmt = stmt.where(Document.order_id == order_id)
    if partner_id is not None:
        stmt = stmt.join(Order, Order.id == Document.order_id).where(
            Order.partner_id == partner_id
        )
    return list((await db.execute(stmt)).scalars().all())


async def create_document(
    db: AsyncSession,
    *,
    order_id: int,
    type_: str,
    number: str | None,
    filename: str | None,
    content_type: str | None,
    content: bytes,
    uploaded_by: int | None,
) -> Document:
    doc = Document(
        order_id=order_id,
        type=type_,
        number=number,
        status="issued",
        filename=filename,
        content_type=content_type,
        size=len(content),
        content=content,
        uploaded_by=uploaded_by,
        issued_at=datetime.now(timezone.utc),
    )
    db.add(doc)
    await db.commit()
    await db.refresh(doc)
    return doc


async def delete_document(db: AsyncSession, doc: Document) -> None:
    await db.delete(doc)
    await db.commit()
