from pydantic import BaseModel


class RoleRead(BaseModel):
    """A system role (RBAC)."""

    id: int
    code: str
    name: str
