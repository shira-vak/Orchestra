"""Purpose: verifies a dependent step runs after its dependency and receives its output in-prompt"""

from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.registry import AgentRegistry
from app.enums import OutputFormat, StepStatus
from app.execution.engine import ExecutionEngine
from app.infrastructure.db.execution_plan_repository import ExecutionPlanRepository
from app.infrastructure.db.execution_step_repository import ExecutionStepRepository
from app.infrastructure.db.models import ExecutionStep
from app.infrastructure.db.task_repository import TaskRepository
from app.infrastructure.llm.response import LLMResponse
from app.planner.schemas.plan import Plan
from app.planner.schemas.plan_step import PlanStep
from tests.conftest import MockLLMClient

MOCK_GOAL = "Research a topic and write a summary"

SEQUENTIAL_PLAN = Plan(
    steps=[
        PlanStep(id="step_1", agent="research", action="research", input="topic", dependencies=[]),
        PlanStep(
            id="step_2", agent="writing", action="write", input="summarize", dependencies=["step_1"]
        ),
    ],
    parallel_groups=[["step_1"], ["step_2"]],
)


async def _persist_plan(db_session: AsyncSession, plan: Plan) -> dict[str, ExecutionStep]:
    task = await TaskRepository(db_session).create(
        goal=MOCK_GOAL, constraints={}, output_format=OutputFormat.MARKDOWN
    )
    plan_row = await ExecutionPlanRepository(db_session).create(task_id=task.id, plan=plan)
    return await ExecutionStepRepository(db_session).create_many(
        plan_id=plan_row.id, plan_steps=plan.steps
    )


async def test_engine_passes_dependency_output_into_dependent_steps_prompt(
    db_session: AsyncSession,
) -> None:
    execution_steps = await _persist_plan(db_session, SEQUENTIAL_PLAN)
    mock_llm_client = MockLLMClient(
        responses=[
            LLMResponse(text="research findings", tokens_used=5),
            LLMResponse(text="final summary", tokens_used=7),
        ]
    )
    engine = ExecutionEngine(
        AgentRegistry(mock_llm_client),
        ExecutionStepRepository(db_session),
        max_concurrent_llm_calls=5,
        step_retry_attempts=0,
    )

    outputs = await engine.run(SEQUENTIAL_PLAN, execution_steps)

    assert outputs == {"step_1": "research findings", "step_2": "final summary"}
    assert "research findings" in mock_llm_client.calls[1]["prompt"]


async def test_engine_marks_every_step_completed_with_output_and_tokens(
    db_session: AsyncSession,
) -> None:
    execution_steps = await _persist_plan(db_session, SEQUENTIAL_PLAN)
    mock_llm_client = MockLLMClient(
        responses=[
            LLMResponse(text="research findings", tokens_used=5),
            LLMResponse(text="final summary", tokens_used=7),
        ]
    )
    engine = ExecutionEngine(
        AgentRegistry(mock_llm_client),
        ExecutionStepRepository(db_session),
        max_concurrent_llm_calls=5,
        step_retry_attempts=0,
    )

    await engine.run(SEQUENTIAL_PLAN, execution_steps)

    for step_id, tokens in (("step_1", 5), ("step_2", 7)):
        await db_session.refresh(execution_steps[step_id])
        assert execution_steps[step_id].status == StepStatus.COMPLETED
        assert execution_steps[step_id].tokens_used == tokens
        assert execution_steps[step_id].output is not None


async def test_engine_skips_remaining_groups_once_cancelled(db_session: AsyncSession) -> None:
    execution_steps = await _persist_plan(db_session, SEQUENTIAL_PLAN)
    mock_llm_client = MockLLMClient(
        default_response=LLMResponse(text="research findings", tokens_used=5)
    )
    engine = ExecutionEngine(
        AgentRegistry(mock_llm_client),
        ExecutionStepRepository(db_session),
        max_concurrent_llm_calls=5,
        step_retry_attempts=0,
    )

    # cancelled is checked before each group: step_1's group runs, step_2's doesn't
    calls = iter([False, True])

    async def is_cancelled() -> bool:
        return next(calls)

    outputs = await engine.run(SEQUENTIAL_PLAN, execution_steps, is_cancelled=is_cancelled)

    assert outputs == {"step_1": "research findings"}
    await db_session.refresh(execution_steps["step_1"])
    await db_session.refresh(execution_steps["step_2"])
    assert execution_steps["step_1"].status == StepStatus.COMPLETED
    assert execution_steps["step_2"].status == StepStatus.SKIPPED
