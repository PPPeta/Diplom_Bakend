from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.task import Task
from app.schemas.task import TaskCreate, TaskUpdate


async def create_task(db: AsyncSession, data: TaskCreate) -> Task:
    task = Task(**data.model_dump())
    db.add(task)
    await db.commit()
    await db.refresh(task)
    return task


async def list_tasks(
    db: AsyncSession,
    order_id: int | None = None,
    status: str | None = None,
    executor_id: int | None = None,
    limit: int = 100,
    offset: int = 0,
) -> list[Task]:
    stmt = (
        select(Task)
        .order_by(Task.created_at.desc())
        .limit(limit)
        .offset(offset)
    )
    if order_id is not None:
        stmt = stmt.where(Task.order_id == order_id)
    if status:
        stmt = stmt.where(Task.status == status)
    if executor_id is not None:
        stmt = stmt.where(Task.executor_id == executor_id)
    return list((await db.execute(stmt)).scalars().all())


async def get_task(db: AsyncSession, task_id: int) -> Task | None:
    return await db.get(Task, task_id)


async def update_task(db: AsyncSession, task: Task, data: TaskUpdate) -> Task:
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(task, field, value)
    await db.commit()
    await db.refresh(task)
    return task
