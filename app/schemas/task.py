from datetime import date, datetime

from pydantic import BaseModel, ConfigDict


class TaskCreate(BaseModel):
    order_id: int
    title: str
    executor_id: int | None = None
    due_date: date | None = None


class TaskUpdate(BaseModel):
    title: str | None = None
    executor_id: int | None = None
    status: str | None = None
    due_date: date | None = None


class TaskRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    order_id: int
    executor_id: int | None = None
    title: str
    status: str
    due_date: date | None = None
    created_at: datetime
