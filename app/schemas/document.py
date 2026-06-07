from datetime import datetime

from pydantic import BaseModel, ConfigDict


class DocumentRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    order_id: int
    type: str
    number: str | None = None
    status: str
    filename: str | None = None
    content_type: str | None = None
    size: int | None = None
    issued_at: datetime | None = None
    created_at: datetime
