from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.config import get_settings

settings = get_settings()

# pool_pre_ping replaces silently-dropped connections instead of erroring mid-request
engine = create_async_engine(settings.database_url, pool_pre_ping=True)

# keeps ORM objects usable after commit; async sessions can't lazy-reload
async_session_factory = async_sessionmaker(engine, expire_on_commit=False)


async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI dependency: one session per request, always closed after."""
    async with async_session_factory() as session:
        yield session


def get_session_factory() -> async_sessionmaker[AsyncSession]:
    """FastAPI dependency for code that must open its own session outside a
    request's lifecycle (e.g. TaskRunner's background execution)."""
    return async_session_factory
