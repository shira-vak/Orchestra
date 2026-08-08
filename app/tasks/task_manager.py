"""Purpose: lifecycle facade for a task — plan, execute, compose a result, persist each transition.
`_compose_result` is a placeholder; Phase 4's Synthesizer replaces it."""

from typing import Any

from app.enums import TaskStatus
from app.exceptions import InvalidPlanError
from app.execution.engine import ExecutionEngine
from app.infrastructure.db.execution_plan_repository import ExecutionPlanRepository
from app.infrastructure.db.execution_step_repository import ExecutionStepRepository
from app.infrastructure.db.models import ExecutionStep, Task
from app.infrastructure.db.task_repository import TaskRepository
from app.planner.planner import Planner
from app.planner.schemas.plan import Plan


class TaskManager:
    def __init__(
        self,
        task_repository: TaskRepository,
        plan_repository: ExecutionPlanRepository,
        step_repository: ExecutionStepRepository,
        planner: Planner,
        execution_engine: ExecutionEngine,
    ) -> None:
        self._task_repository = task_repository
        self._plan_repository = plan_repository
        self._step_repository = step_repository
        self._planner = planner
        self._execution_engine = execution_engine

    async def submit(self, *, goal: str, constraints: dict[str, Any], output_format: str) -> Task:
        task = await self._task_repository.create(
            goal=goal, constraints=constraints, output_format=output_format
        )

        try:
            plan, execution_steps = await self._plan(task, goal=goal, constraints=constraints)
        except InvalidPlanError:
            await self._task_repository.update_status(task, status=TaskStatus.FAILED)
            raise

        outputs = await self._execute(task, plan, execution_steps)
        return await self._finalize(task, plan, outputs)

    async def get(self, task_id: str) -> Task | None:
        return await self._task_repository.get(task_id)

    async def _plan(
        self, task: Task, *, goal: str, constraints: dict[str, Any]
    ) -> tuple[Plan, dict[str, ExecutionStep]]:
        """Decomposes the goal, then persists the plan+steps before any step runs."""
        await self._task_repository.update_status(task, status=TaskStatus.PLANNING)
        plan = await self._planner.decompose(goal=goal, constraints=constraints)

        plan_row = await self._plan_repository.create(task_id=task.id, plan=plan)
        execution_steps = await self._step_repository.create_many(
            plan_id=plan_row.id, plan_steps=plan.steps
        )
        return plan, execution_steps

    async def _execute(
        self, task: Task, plan: Plan, execution_steps: dict[str, ExecutionStep]
    ) -> dict[str, str]:
        await self._task_repository.update_status(task, status=TaskStatus.EXECUTING)
        return await self._execution_engine.run(plan, execution_steps)

    async def _finalize(self, task: Task, plan: Plan, outputs: dict[str, str]) -> Task:
        """Completed if any step produced output; failed if every step did."""
        status = TaskStatus.COMPLETED if outputs else TaskStatus.FAILED
        result = _compose_result(plan, outputs) if outputs else None
        return await self._task_repository.update_status(task, status=status, result=result)


def _compose_result(plan: Plan, outputs: dict[str, str]) -> str:
    return "\n\n".join(outputs[step.id] for step in plan.steps if step.id in outputs)
