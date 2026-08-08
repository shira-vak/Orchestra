"""Purpose: creates the app's async SQLAlchemy engine/session factory and
exposes `get_db_session` as the FastAPI dependency every route/service uses
to get a database session — the one place a session is constructed.
"""

from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.config import get_settings

settings = get_settings()

# pool_pre_ping checks a pooled connection is still alive before handing it
# out — without it, a connection Postgres silently dropped (idle timeout,
# container restart) surfaces as a confusing mid-request error instead of
# being transparently replaced.
engine = create_async_engine(settings.database_url, pool_pre_ping=True)

# expire_on_commit=False keeps ORM objects usable (attribute access without
# a fresh DB round trip) after a commit. The default (True) would mark every
# attribute stale after commit, and re-fetching them from an async session
# outside of an active `await` context raises rather than lazy-loading.
async_session_factory = async_sessionmaker(engine, expire_on_commit=False)


async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI dependency: one session per request, always closed after."""
    async with async_session_factory() as session:
        yield session
