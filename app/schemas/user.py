from pydantic import BaseModel, EmailStr, Field


class PartnerRegister(BaseModel):
    org_name: str
    inn: str | None = None
    type: str = Field(description="insurance | corporate | allied")
    contract_no: str | None = None


class UserRegister(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8)
    full_name: str
    partner: PartnerRegister


class UserRead(BaseModel):
    id: int
    email: EmailStr
    full_name: str
    role: str
    partner_id: int | None = None
    is_active: bool
