"""Purpose: shared test fixtures. Tests run against a real, migrated Postgres
database (`orchestra_test`), truncated back to clean after each test."""

import asyncio
from collections.abc import AsyncGenerator
from typing import Any

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
from app.infrastructure.db.session import get_db_session, get_session_factory
from app.infrastructure.llm.anthropic_client import get_llm_client
from app.infrastructure.llm.client import LLMClient
from app.infrastructure.llm.response import LLMResponse
from app.main import app
from tests.settings import get_test_database_name, get_test_database_url

_TERMINAL_TASK_STATUSES = {"completed", "failed", "cancelled"}

settings = get_settings()


def _maintenance_dsn() -> str:
    """DSN for the default 'postgres' database — CREATE DATABASE can't run against itself."""
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
    """Ensures the test DB exists and is migrated, once per session. Runs
    migrations in a worker thread since Alembic's env.py calls
    asyncio.run(), which can't nest inside pytest-asyncio's running loop."""
    await _ensure_test_database_exists()
    await asyncio.to_thread(_run_migrations)


@pytest.fixture(scope="session")
def test_engine(_prepared_test_database: None) -> AsyncEngine:
    return create_async_engine(get_test_database_url())


async def _truncate_all_tables(session: AsyncSession) -> None:
    # reversed: child tables before parents (CASCADE makes this moot, but reads clearer)
    for table in reversed(Base.metadata.sorted_tables):
        if table.name == "agents":
            continue  # seed data, not test data
        await session.execute(text(f'TRUNCATE TABLE "{table.name}" RESTART IDENTITY CASCADE'))
    await session.commit()


@pytest.fixture
async def db_session(test_engine: AsyncEngine) -> AsyncGenerator[AsyncSession, None]:
    session_factory = async_sessionmaker(test_engine, expire_on_commit=False)
    async with session_factory() as session:
        yield session
        await session.rollback()
        await _truncate_all_tables(session)


class MockLLMClient(LLMClient):
    """Deterministic stand-in for AnthropicClient; `calls` records every prompt sent. `responses`,
    if given, is consumed one-per-call then repeats its last entry — otherwise every call gets
    `default_response`."""

    def __init__(
        self,
        default_response: LLMResponse | None = None,
        responses: list[LLMResponse] | None = None,
    ) -> None:
        self.default_response = default_response or LLMResponse(
            text="mock response", tokens_used=10
        )
        self._responses = list(responses) if responses else None
        self.calls: list[dict[str, str]] = []

    async def complete(self, *, system: str, prompt: str, max_tokens: int) -> LLMResponse:
        self.calls.append({"system": system, "prompt": prompt})
        if self._responses:
            response = self._responses[0]
            if len(self._responses) > 1:
                self._responses.pop(0)
            return response
        return self.default_response


@pytest.fixture
def mock_llm_client() -> MockLLMClient:
    return MockLLMClient()


@pytest.fixture
async def client(
    db_session: AsyncSession, test_engine: AsyncEngine, mock_llm_client: MockLLMClient
) -> AsyncGenerator[httpx.AsyncClient, None]:
    """httpx client wired to the app, with DB session + LLM client swapped for test doubles.

    Task execution runs in a detached background asyncio task (see TaskRunner),
    which opens its own session rather than reusing the request's `db_session` —
    a session isn't safe for concurrent/cross-coroutine use. It's given its own
    factory bound to `test_engine` so it still hits the same test database.
    """

    async def _override_get_db_session() -> AsyncGenerator[AsyncSession, None]:
        yield db_session

    app.dependency_overrides[get_db_session] = _override_get_db_session
    app.dependency_overrides[get_llm_client] = lambda: mock_llm_client
    app.dependency_overrides[get_session_factory] = lambda: async_sessionmaker(
        test_engine, expire_on_commit=False
    )

    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as async_client:
        yield async_client

    app.dependency_overrides.clear()


async def wait_for_terminal_status(
    client: httpx.AsyncClient, task_id: str, *, timeout_seconds: float = 5.0
) -> dict[str, Any]:
    """Polls GET /tasks/{id} until its status is terminal — task execution
    runs in a detached background asyncio task, not inline with the request
    that created it (see TaskRunner).
    """
    deadline = asyncio.get_running_loop().time() + timeout_seconds
    while True:
        body = (await client.get(f"/tasks/{task_id}")).json()
        if body["status"] in _TERMINAL_TASK_STATUSES:
            return body
        if asyncio.get_running_loop().time() > deadline:
            raise TimeoutError(f"task {task_id} did not reach a terminal status in time")
        await asyncio.sleep(0.02)
