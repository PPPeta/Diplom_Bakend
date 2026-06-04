from sqlalchemy.orm import DeclarativeBase


class CoreBase(DeclarativeBase):
    """Declarative base for the operational database (core_db)."""


class AnalyticsBase(DeclarativeBase):
    """Declarative base for the analytics database (analytics_db)."""
