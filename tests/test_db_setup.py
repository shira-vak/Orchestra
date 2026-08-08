"""Purpose: verifies Phase 1's infrastructure actually works against a real
database — migrations create the expected tables, seed the 4 agent rows,
and a model round-trips through Postgres correctly.
"""

from sqlalchemy import inspect, select
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession

from app.enums import TaskStatus
from app.models import Agent, Task
from tests.consts import EXPECTED_AGENT_NAMES, EXPECTED_TABLES


async def test_migrations_create_expected_tables(test_engine: AsyncEngine) -> None:
    async with test_engine.connect() as conn:
        table_names = await conn.run_sync(lambda sync_conn: set(inspect(sync_conn).get_table_names()))

    assert EXPECTED_TABLES.issubset(table_names)


async def test_migrations_seed_all_four_agents(db_session: AsyncSession) -> None:
    result = await db_session.execute(select(Agent))
    agent_names = {agent.name for agent in result.scalars().all()}

    assert agent_names == EXPECTED_AGENT_NAMES


async def test_task_roundtrip_persists_and_reads_back(db_session: AsyncSession) -> None:
    task = Task(goal="Write a comparison blog post", constraints={"max_words": 1500})
    db_session.add(task)
    await db_session.commit()

    fetched = await db_session.get(Task, task.id)

    assert fetched is not None
    assert fetched.goal == "Write a comparison blog post"
    assert fetched.constraints == {"max_words": 1500}
    assert fetched.status == TaskStatus.PENDING
    assert fetched.id.startswith("task_")
