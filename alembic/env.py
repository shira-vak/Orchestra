"""Purpose: Alembic's entry point, run by the `alembic` CLI for every
migration command (upgrade/downgrade/autogenerate). Adapted to run against
the async engine.
"""

import asyncio

from alembic import context
from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine

from app.config import get_settings
from app.db.base import Base
from app.models import *  # noqa: F401,F403 -- populates Base.metadata for autogenerate

config = context.config
target_metadata = Base.metadata


def _database_url() -> str:
    # Reads the URL Alembic already has (set by tests/conftest.py for the
    # test database) if present, otherwise falls back to Settings — this is
    # the one seam that lets tests point migrations at orchestra_test
    # without touching this file.
    return config.get_main_option("sqlalchemy.url") or get_settings().database_url


def run_migrations_offline() -> None:
    context.configure(url=_database_url(), target_metadata=target_metadata, literal_binds=True)
    with context.begin_transaction():
        context.run_migrations()


def _run_sync_migrations(connection: object) -> None:
    context.configure(connection=connection, target_metadata=target_metadata)
    with context.begin_transaction():
        context.run_migrations()


async def run_migrations_online() -> None:
    connectable: AsyncEngine = create_async_engine(_database_url())
    async with connectable.connect() as connection:
        await connection.run_sync(_run_sync_migrations)
    await connectable.dispose()


if context.is_offline_mode():
    run_migrations_offline()
else:
    asyncio.run(run_migrations_online())
