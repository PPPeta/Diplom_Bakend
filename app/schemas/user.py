from pydantic import BaseModel, Field


class PartnerRegister(BaseModel):
    org_name: str
    inn: str | None = None
    type: str = Field(description="insurance | corporate | allied")
    contract_no: str | None = None


class UserRegister(BaseModel):
    # Используем обычную строку, а не EmailStr: внутренние/тестовые домены
    # вроде admin@vp.local pydantic считает невалидными и роняет ответ.
    email: str
    password: str = Field(min_length=8)
    full_name: str
    partner: PartnerRegister


class UserRead(BaseModel):
    id: int
    email: str
    full_name: str
    phone: str | None = None
    role: str
    partner_id: int | None = None
    is_active: bool


class ProfileUpdate(BaseModel):
    full_name: str | None = Field(default=None, min_length=1, max_length=255)
    phone: str | None = Field(default=None, max_length=32)


class PasswordChange(BaseModel):
    current_password: str = Field(min_length=1)
    new_password: str = Field(min_length=8, max_length=128)


class UserAdminUpdate(BaseModel):
    """Administrative update of a user account."""

    is_active: bool | None = None
    role_code: str | None = None


class UserCreate(BaseModel):
    """Administrative creation of a user (staff member or partner contact)."""

    email: str
    password: str = Field(min_length=8, max_length=128)
    full_name: str = Field(min_length=1, max_length=255)
    phone: str | None = Field(default=None, max_length=32)
    role_code: str = Field(description="admin | manager | executor | partner")
    partner_id: int | None = None
