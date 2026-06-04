from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import require_roles
from app.db.session import get_core_session
from app.models.user import User
from app.schemas.task import TaskCreate, TaskRead, TaskUpdate
from app.services import task_service

router = APIRouter(prefix="/tasks", tags=["tasks"])

DbDep = Annotated[AsyncSession, Depends(get_core_session)]
StaffOrExecutor = Annotated[
    User, Depends(require_roles("admin", "manager", "executor"))
]


@router.post(
    "",
    response_model=TaskRead,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_roles("admin", "manager"))],
)
async def create_task(data: TaskCreate, db: DbDep) -> TaskRead:
    return await task_service.create_task(db, data)


@router.get("", response_model=list[TaskRead])
async def list_tasks(
    db: DbDep,
    user: StaffOrExecutor,
    order_id: int | None = None,
    status_filter: str | None = None,
) -> list[TaskRead]:
    # Executors only see tasks assigned to them.
    if user.role.code == "executor":
        return await task_service.list_tasks(
            db, order_id=order_id, status=status_filter, executor_id=user.id
        )
    return await task_service.list_tasks(
        db, order_id=order_id, status=status_filter
    )


@router.get("/{task_id}", response_model=TaskRead)
async def get_task(task_id: int, db: DbDep, user: StaffOrExecutor) -> TaskRead:
    task = await task_service.get_task(db, task_id)
    if task is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Task not found"
        )
    if user.role.code == "executor" and task.executor_id != user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden"
        )
    return task


@router.patch("/{task_id}", response_model=TaskRead)
async def update_task(
    task_id: int, data: TaskUpdate, db: DbDep, user: StaffOrExecutor
) -> TaskRead:
    task = await task_service.get_task(db, task_id)
    if task is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Task not found"
        )
    if user.role.code == "executor":
        if task.executor_id != user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden"
            )
        changed = set(data.model_dump(exclude_unset=True))
        if changed - {"status"}:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Executor may only change task status",
            )
    return await task_service.update_task(db, task, data)
