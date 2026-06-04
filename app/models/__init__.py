"""SQLAlchemy models.

Import all models here so they get registered on CoreBase metadata and are
picked up by Alembic autogenerate.
"""
from app.models.partner import Partner
from app.models.role import Permission, Role, role_permissions
from app.models.user import User
from app.models.service import ServiceCatalog
from app.models.pricing import PartnerTerm, PriceList, PriceListItem
from app.models.request import Request
from app.models.order import Order, OrderItem
from app.models.task import Task
from app.models.document import Document
from app.models.payment import Payment
from app.models.message import Message

__all__ = [
    "Partner",
    "Permission",
    "Role",
    "role_permissions",
    "User",
    "ServiceCatalog",
    "PartnerTerm",
    "PriceList",
    "PriceListItem",
    "Request",
    "Order",
    "OrderItem",
    "Task",
    "Document",
    "Payment",
    "Message",
]
