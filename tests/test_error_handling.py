"""Purpose: a step that exhausts retries is marked failed; its dependents are skipped."""

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

MOCK_GOAL = "Research a topic, analyze it, then write it up"

# step_1 always fails; step_2/step_3 chain off it, testing two-layer propagation
CHAINED_PLAN = Plan(
    steps=[
        PlanStep(id="step_1", agent="research", action="research", input="topic", dependencies=[]),
        PlanStep(
            id="step_2", agent="analysis", action="analyze", input="x", dependencies=["step_1"]
        ),
        PlanStep(id="step_3", agent="writing", action="write", input="y", dependencies=["step_2"]),
    ],
    parallel_groups=[["step_1"], ["step_2"], ["step_3"]],
)


class _AlwaysFailingLLMClient(LLMClient):
    def __init__(self) -> None:
        self.call_count = 0

    async def complete(self, *, system: str, prompt: str, max_tokens: int) -> LLMResponse:
        self.call_count += 1
        raise RuntimeError("simulated LLM failure")


async def test_step_exhausting_retries_is_failed_and_dependents_are_skipped(
    db_session: AsyncSession,
) -> None:
    task = await TaskRepository(db_session).create(
        goal=MOCK_GOAL, constraints={}, output_format=OutputFormat.MARKDOWN
    )
    plan_row = await ExecutionPlanRepository(db_session).create(task_id=task.id, plan=CHAINED_PLAN)
    execution_steps = await ExecutionStepRepository(db_session).create_many(
        plan_id=plan_row.id, plan_steps=CHAINED_PLAN.steps
    )

    failing_llm_client = _AlwaysFailingLLMClient()
    retry_attempts = 2
    engine = ExecutionEngine(
        AgentRegistry(failing_llm_client),
        ExecutionStepRepository(db_session),
        max_concurrent_llm_calls=5,
        step_retry_attempts=retry_attempts,
    )

    outputs = await engine.run(CHAINED_PLAN, execution_steps)

    assert outputs == {}
    # step_1's attempts only — step_2/step_3 never call the LLM once blocked
    assert failing_llm_client.call_count == retry_attempts + 1

    await db_session.refresh(execution_steps["step_1"])
    await db_session.refresh(execution_steps["step_2"])
    await db_session.refresh(execution_steps["step_3"])
    assert execution_steps["step_1"].status == StepStatus.FAILED
    assert execution_steps["step_2"].status == StepStatus.SKIPPED
    assert execution_steps["step_3"].status == StepStatus.SKIPPED


async def test_independent_step_still_completes_when_a_sibling_fails(
    db_session: AsyncSession,
) -> None:
    plan = Plan(
        steps=[
            PlanStep(id="step_1", agent="research", action="research", input="x", dependencies=[]),
            PlanStep(id="step_2", agent="writing", action="write", input="y", dependencies=[]),
        ],
        parallel_groups=[["step_1", "step_2"]],
    )
    task = await TaskRepository(db_session).create(
        goal=MOCK_GOAL, constraints={}, output_format=OutputFormat.MARKDOWN
    )
    plan_row = await ExecutionPlanRepository(db_session).create(task_id=task.id, plan=plan)
    execution_steps = await ExecutionStepRepository(db_session).create_many(
        plan_id=plan_row.id, plan_steps=plan.steps
    )

    class _FailOnlyStepOne(LLMClient):
        async def complete(self, *, system: str, prompt: str, max_tokens: int) -> LLMResponse:
            if "x" in prompt:
                raise RuntimeError("simulated LLM failure")
            return LLMResponse(text="sibling output", tokens_used=3)

    engine = ExecutionEngine(
        AgentRegistry(_FailOnlyStepOne()),
        ExecutionStepRepository(db_session),
        max_concurrent_llm_calls=5,
        step_retry_attempts=0,
    )

    outputs = await engine.run(plan, execution_steps)

    assert outputs == {"step_2": "sibling output"}
    await db_session.refresh(execution_steps["step_1"])
    await db_session.refresh(execution_steps["step_2"])
    assert execution_steps["step_1"].status == StepStatus.FAILED
    assert execution_steps["step_2"].status == StepStatus.COMPLETED
