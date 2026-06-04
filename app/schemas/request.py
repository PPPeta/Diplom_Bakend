from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr


class RequestCreate(BaseModel):
    client_name: str
    phone: str | None = None
    email: EmailStr | None = None
    message: str | None = None
    source: str = "site"
    pdn_consent: bool


class RequestStatusUpdate(BaseModel):
    status: str


class RequestRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    client_name: str
    phone: str | None = None
    email: EmailStr | None = None
    message: str | None = None
    source: str
    status: str
    pdn_consent: bool
    created_at: datetime
