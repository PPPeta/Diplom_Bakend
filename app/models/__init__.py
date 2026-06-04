"""SQLAlchemy models.

Import all models here so they get registered on CoreBase/AnalyticsBase
metadata and are picked up by Alembic autogenerate.
"""
from app.models.partner import Partner
from app.models.role import Permission, Role, role_permissions
from app.models.user import User

__all__ = ["Partner", "Permission", "Role", "role_permissions", "User"]
