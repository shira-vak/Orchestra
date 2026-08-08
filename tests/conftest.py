"""Purpose: shared test fixtures.

Two things worth understanding about how tests are isolated here:

1. Tests run against a *real* Postgres database (`orchestra_test`, a
   separate database on the same instance as the dev DB), with the actual
   Alembic migrations applied — not `Base.metadata.create_all()`. That's
   deliberate: it's the only way a test can actually prove the migrations
   are correct, not just that the ORM models are internally consistent.

2. Each test gets a clean slate via table truncation after it runs, not a
   rolled-back transaction. A SAVEPOINT-nesting pattern is the "more
   correct" textbook answer for async SQLAlchemy, but it's fiddly to get
   right; truncation is a few obvious lines and isolation is what actually
   matters here, not shaving milliseconds off the suite.
"""

import asyncio
from collections.abc import AsyncGenerator

import asyncpg
import httpx
import pytest
from alembic.config import Config
from sqlalchemy import text
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from alembic import command
from app.config import get_settings
from app.infrastructure.db.base import Base
from app.infrastructure.db.session import get_db_session
from app.infrastructure.llm.anthropic_client import get_llm_client
from app.infrastructure.llm.client import LLMClient
from app.infrastructure.llm.response import LLMResponse
from app.main import app
from tests.settings import get_test_database_name, get_test_database_url

settings = get_settings()


def _maintenance_dsn() -> str:
    """DSN for the instance's default 'postgres' database.

    CREATE DATABASE / DROP DATABASE can't run inside a transaction against
    the database being created or dropped, so this connects to a different,
    always-present database to issue that one statement.
    """
    return (
        f"postgresql://{settings.postgres_user}:{settings.postgres_password}"
        f"@{settings.postgres_host}:{settings.postgres_port}/postgres"
    )


async def _ensure_test_database_exists() -> None:
    conn = await asyncpg.connect(_maintenance_dsn())
    try:
        db_name = get_test_database_name()
        already_exists = await conn.fetchval(
            "SELECT 1 FROM pg_database WHERE datname = $1", db_name
        )
        if not already_exists:
            await conn.execute(f'CREATE DATABASE "{db_name}"')
    finally:
        await conn.close()


def _run_migrations() -> None:
    alembic_cfg = Config("alembic.ini")
    alembic_cfg.set_main_option("sqlalchemy.url", get_test_database_url())
    command.upgrade(alembic_cfg, "head")


@pytest.fixture(scope="session", autouse=True)
async def _prepared_test_database() -> None:
    """Runs once per test session, before any test: ensure the test
    database exists, then bring it up to the latest migration.

    `_run_migrations` is dispatched to a worker thread because Alembic's
    `env.py` calls `asyncio.run(...)` internally (see alembic/env.py) — that
    fails with "asyncio.run() cannot be called from a running event loop"
    if invoked directly from here, since this fixture is itself already
    running inside pytest-asyncio's event loop. A plain thread has no
    running loop of its own, so `asyncio.run()` inside it works normally.
    """
    await _ensure_test_database_exists()
    await asyncio.to_thread(_run_migrations)


@pytest.fixture(scope="session")
def test_engine(_prepared_test_database: None) -> AsyncEngine:
    return create_async_engine(get_test_database_url())


async def _truncate_all_tables(session: AsyncSession) -> None:
    # Reversed so child tables (with FKs) are truncated before parents —
    # irrelevant with CASCADE below, but keeps the intent readable.
    for table in reversed(Base.metadata.sorted_tables):
        if table.name == "agents":
            continue  # seed data, not test data — left in place for every test
        await session.execute(text(f'TRUNCATE TABLE "{table.name}" RESTART IDENTITY CASCADE'))
    await session.commit()


@pytest.fixture
async def db_session(test_engine: AsyncEngine) -> AsyncGenerator[AsyncSession, None]:
    session_factory = async_sessionmaker(test_engine, expire_on_commit=False)
    async with session_factory() as session:
        yield session
        await session.rollback()
        await _truncate_all_tables(session)


class FakeLLMClient(LLMClient):
    """Deterministic stand-in for AnthropicClient. Every test goes through
    this — no test ever makes a real network call to an LLM provider.

    `calls` records every prompt sent to it, so a test can assert on what
    the planner/agent actually asked for, not just what came back.
    """

    def __init__(self, default_response: LLMResponse | None = None) -> None:
        self.default_response = default_response or LLMResponse(
            text="fake response", tokens_used=10
        )
        self.calls: list[dict[str, str]] = []

    async def complete(self, *, system: str, prompt: str, max_tokens: int) -> LLMResponse:
        self.calls.append({"system": system, "prompt": prompt})
        return self.default_response


@pytest.fixture
def fake_llm_client() -> FakeLLMClient:
    return FakeLLMClient()


@pytest.fixture
async def client(
    db_session: AsyncSession, fake_llm_client: FakeLLMClient
) -> AsyncGenerator[httpx.AsyncClient, None]:
    """An httpx client wired to the FastAPI app, with the DB session and LLM
    client swapped for test doubles via FastAPI's dependency_overrides — no
    test ever hits a real LLM or a session outside the truncate-after-test
    one `db_session` already manages.
    """

    async def _override_get_db_session() -> AsyncGenerator[AsyncSession, None]:
        yield db_session

    app.dependency_overrides[get_db_session] = _override_get_db_session
    app.dependency_overrides[get_llm_client] = lambda: fake_llm_client

    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as async_client:
        yield async_client

    app.dependency_overrides.clear()
