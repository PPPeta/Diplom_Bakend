from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.core.config import settings

core_engine = create_async_engine(
    settings.core_db_url, echo=settings.DEBUG, pool_pre_ping=True
)
analytics_engine = create_async_engine(
    settings.analytics_db_url, echo=settings.DEBUG, pool_pre_ping=True
)

CoreSessionLocal = async_sessionmaker(
    bind=core_engine, class_=AsyncSession, expire_on_commit=False
)
AnalyticsSessionLocal = async_sessionmaker(
    bind=analytics_engine, class_=AsyncSession, expire_on_commit=False
)


async def get_core_session() -> AsyncGenerator[AsyncSession, None]:
    async with CoreSessionLocal() as session:
        yield session


async def get_analytics_session() -> AsyncGenerator[AsyncSession, None]:
    async with AnalyticsSessionLocal() as session:
        yield session
