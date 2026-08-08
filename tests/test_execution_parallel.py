"""Purpose: verifies steps in the same parallel_groups layer genuinely overlap in
time (wall-clock, not just outputs)."""

import asyncio
import time

from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.registry import AgentRegistry
from app.enums import OutputFormat, StepStatus
from app.execution.engine import ExecutionEngine
from app.infrastructure.db.execution_plan_repository import ExecutionPlanRepository
from app.infrastructure.db.execution_step_repository import ExecutionStepRepository
from app.infrastructure.db.task_repository import TaskRepository
from app.infrastructure.llm.client import LLMClient
from app.infrastructure.llm.response import LLMResponse
from app.planner.schemas.plan import Plan
from app.planner.schemas.plan_step import PlanStep

MOCK_GOAL = "Research two unrelated topics"
STEP_DELAY_SECONDS = 0.2

PARALLEL_PLAN = Plan(
    steps=[
        PlanStep(
            id="step_1", agent="research", action="research", input="topic a", dependencies=[]
        ),
        PlanStep(
            id="step_2", agent="research", action="research", input="topic b", dependencies=[]
        ),
    ],
    parallel_groups=[["step_1", "step_2"]],
)


class _DelayedLLMClient(LLMClient):
    """Sleeps before responding, so timing can prove calls overlapped."""

    async def complete(self, *, system: str, prompt: str, max_tokens: int) -> LLMResponse:
        await asyncio.sleep(STEP_DELAY_SECONDS)
        return LLMResponse(text=f"result for: {prompt}", tokens_used=1)


async def test_engine_runs_independent_steps_in_the_same_group_concurrently(
    db_session: AsyncSession,
) -> None:
    task = await TaskRepository(db_session).create(
        goal=MOCK_GOAL, constraints={}, output_format=OutputFormat.MARKDOWN
    )
    plan_row = await ExecutionPlanRepository(db_session).create(task_id=task.id, plan=PARALLEL_PLAN)
    execution_steps = await ExecutionStepRepository(db_session).create_many(
        plan_id=plan_row.id, plan_steps=PARALLEL_PLAN.steps
    )

    engine = ExecutionEngine(
        AgentRegistry(_DelayedLLMClient()),
        ExecutionStepRepository(db_session),
        max_concurrent_llm_calls=5,
        step_retry_attempts=0,
    )

    started_at = time.monotonic()
    outputs = await engine.run(PARALLEL_PLAN, execution_steps)
    elapsed_seconds = time.monotonic() - started_at

    # sequential would take >= 2x the delay; well under that proves overlap
    assert STEP_DELAY_SECONDS <= elapsed_seconds < 1.5 * STEP_DELAY_SECONDS
    assert set(outputs) == {"step_1", "step_2"}

    for step in execution_steps.values():
        await db_session.refresh(step)
        assert step.status == StepStatus.COMPLETED
