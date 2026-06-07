from datetime import datetime

from pydantic import BaseModel, ConfigDict


class AuditLogRead(BaseModel):
    # Позволяет создавать схему прямо из ORM-объекта
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int | None
    user_role: str | None
    action: str
    entity_type: str | None
    entity_id: int | None
    details: str | None
    created_at: datetime
