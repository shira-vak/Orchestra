"""Purpose: task lifecycle facade — plans a task synchronously (so an invalid
plan still fails the request with 422), then hands execution off to
TaskRunner in the background, since that's the part slow enough to need
cancelling. Also the control plane for lookup, result, and cancellation.
"""

from typing import Any

from app.enums import OutputFormat, TaskStatus
from app.exceptions import (
    InvalidPlanError,
    InvalidTaskStateError,
    LLMServiceError,
    TaskNotFoundError,
)
from app.infrastructure.db.execution_plan_repository import ExecutionPlanRepository
from app.infrastructure.db.execution_step_repository import ExecutionStepRepository
from app.infrastructure.db.models import ExecutionStep, Task
from app.infrastructure.db.task_repository import TaskRepository
from app.planner.planner import Planner
from app.tasks.task_runner import TaskRunner

_TERMINAL_STATUSES = {TaskStatus.COMPLETED, TaskStatus.FAILED, TaskStatus.CANCELLED}


class TaskManager:
    def __init__(
        self,
        task_repository: TaskRepository,
        plan_repository: ExecutionPlanRepository,
        step_repository: ExecutionStepRepository,
        planner: Planner,
        task_runner: TaskRunner,
    ) -> None:
        self._task_repository = task_repository
        self._plan_repository = plan_repository
        self._step_repository = step_repository
        self._planner = planner
        self._task_runner = task_runner

    async def submit(
        self, *, goal: str, constraints: dict[str, Any], output_format: OutputFormat
    ) -> Task:
        task = await self._task_repository.create(
            goal=goal, constraints=constraints, output_format=output_format
        )
        task = await self._task_repository.update_status(task, status=TaskStatus.PLANNING)

        try:
            plan = await self._planner.decompose(goal=goal, constraints=constraints)
        except (InvalidPlanError, LLMServiceError):
            await self._task_repository.update_status(task, status=TaskStatus.FAILED)
            raise

        plan_row = await self._plan_repository.create(task_id=task.id, plan=plan)
        await self._step_repository.create_many(plan_id=plan_row.id, plan_steps=plan.steps)

        task = await self._task_repository.update_status(task, status=TaskStatus.EXECUTING)
        self._task_runner.start(task.id, plan)
        return task

    async def get(self, task_id: str) -> Task | None:
        return await self._task_repository.get(task_id)

    async def get_result(self, task_id: str) -> tuple[Task, list[ExecutionStep]] | None:
        task = await self._task_repository.get(task_id)
        if task is None:
            return None
        plan = await self._plan_repository.get_by_task_id(task_id)
        return task, (plan.execution_steps if plan else [])

    async def cancel(self, task_id: str) -> Task:
        task = await self._task_repository.get(task_id)
        if task is None:
            raise TaskNotFoundError(task_id)
        if task.status in _TERMINAL_STATUSES:
            raise InvalidTaskStateError(task_id, task.status)
        return await self._task_repository.update_status(task, status=TaskStatus.CANCELLED)
