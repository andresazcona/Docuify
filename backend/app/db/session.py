"""Database session management."""

from collections.abc import AsyncGenerator
from typing import Any

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.pool import NullPool

from app.core.config import get_settings


class Base(DeclarativeBase):
    """Base class for SQLAlchemy models."""

    pass


# Global engine and session factory (initialized in lifespan)
_engine: Any = None
_async_session_factory: async_sessionmaker[AsyncSession] | None = None


async def init_db() -> None:
    """Initialize database engine and session factory."""
    global _engine, _async_session_factory

    settings = get_settings()

    engine_kwargs: dict[str, Any] = {
        "echo": settings.db_echo,
        "pool_pre_ping": True,
    }

    if settings.database_url.startswith("sqlite"):
        engine_kwargs["poolclass"] = NullPool
    else:
        engine_kwargs.update(
            {
                "pool_size": settings.db_pool_size,
                "max_overflow": settings.db_max_overflow,
            }
        )

    _engine = create_async_engine(settings.database_url, **engine_kwargs)

    _async_session_factory = async_sessionmaker(
        _engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )

    if settings.auto_create_tables:
        async with _engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Dependency to get database session.

    Yields:
        AsyncSession: Database session
    """
    if _async_session_factory is None:
        raise RuntimeError("Database not initialized. Call init_db() first.")

    async with _async_session_factory() as session:
        try:
            yield session
        finally:
            await session.close()


def get_session_factory() -> async_sessionmaker[AsyncSession]:
    """Session factory for code that outlives the request (e.g. streaming responses)."""
    if _async_session_factory is None:
        raise RuntimeError("Database not initialized. Call init_db() first.")
    return _async_session_factory


async def close_db() -> None:
    """Close database connections."""
    global _engine
    if _engine:
        await _engine.dispose()


async def check_db_connection() -> bool:
    """
    Check if database connection is working.

    Returns:
        bool: True if connection successful
    """
    try:
        if _engine is None:
            return False

        async with _engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        return True
    except Exception:
        return False
