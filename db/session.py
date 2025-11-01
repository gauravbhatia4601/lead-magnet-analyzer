"""Async SQLAlchemy engine and session management."""

from __future__ import annotations

import contextlib
from typing import AsyncGenerator, Dict, Any

from sqlalchemy.engine import URL
from sqlalchemy.engine.url import make_url
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase

from core.config import settings


class Base(DeclarativeBase):
    """Declarative base for all ORM models."""

    pass


def _build_engine_kwargs(url: URL) -> Dict[str, Any]:
    """Compose engine keyword arguments based on the driver."""

    kwargs: Dict[str, Any] = {
        "echo": settings.database_echo,
        "pool_pre_ping": True,
    }

    backend = url.get_backend_name()
    if backend.startswith("sqlite"):
        # SQLite drivers handle pooling internally; avoid pool configuration
        kwargs["pool_pre_ping"] = False
        kwargs["connect_args"] = {"timeout": 30}
    else:
        if settings.database_pool_size is not None:
            kwargs["pool_size"] = settings.database_pool_size
        if settings.database_max_overflow is not None:
            kwargs["max_overflow"] = settings.database_max_overflow
        if settings.database_pool_timeout is not None:
            kwargs["pool_timeout"] = settings.database_pool_timeout
        if settings.database_pool_recycle is not None:
            kwargs["pool_recycle"] = settings.database_pool_recycle

    return kwargs


_DATABASE_URL = make_url(settings.database_url)
async_engine: AsyncEngine = create_async_engine(
    settings.database_url, **_build_engine_kwargs(_DATABASE_URL)
)
AsyncSessionFactory = async_sessionmaker(
    async_engine, expire_on_commit=False, class_=AsyncSession
)


async def get_async_session() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI dependency that yields an async database session."""

    async with AsyncSessionFactory() as session:
        try:
            yield session
        finally:
            await session.close()


async def init_db() -> None:
    """Verify database connectivity during application startup."""

    async with contextlib.AsyncExitStack() as stack:
        connection = await stack.enter_async_context(async_engine.connect())
        await connection.run_sync(lambda conn: None)
