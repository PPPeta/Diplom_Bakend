"""Message thread on an order (comments between partner and staff)."""
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.message import Message
from app.models.user import User
from app.schemas.message import MessageCreate, MessageRead


def _to_read(message: Message, author_name: str | None) -> MessageRead:
    return MessageRead(
        id=message.id,
        order_id=message.order_id,
        author_id=message.author_id,
        author_name=author_name,
        body=message.body,
        created_at=message.created_at,
    )


async def list_for_order(db: AsyncSession, order_id: int) -> list[MessageRead]:
    stmt = (
        select(Message, User.full_name)
        .join(User, User.id == Message.author_id, isouter=True)
        .where(Message.order_id == order_id)
        .order_by(Message.created_at.asc())
    )
    rows = (await db.execute(stmt)).all()
    return [_to_read(message, author_name) for message, author_name in rows]


async def create_message(
    db: AsyncSession,
    order_id: int,
    author: User,
    data: MessageCreate,
) -> MessageRead:
    message = Message(
        order_id=order_id,
        author_id=author.id,
        body=data.body.strip(),
    )
    db.add(message)
    await db.commit()
    await db.refresh(message)
    return _to_read(message, author.full_name)
