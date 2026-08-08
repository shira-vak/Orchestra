"""Purpose: lifecycle facade for a task — create it, run it through an
agent, persist the result. This is the single place routers call into; they
never talk to the repository or an agent directly.

Phase 2's version calls one fixed agent directly (no planning step yet).
Phase 3's planner + execution engine will replace the single `run()` call in
the middle with a full multi-step plan; create/get stay the same shape.
"""

from typing import Any

from app.agents.base import BaseAgent
from app.enums import TaskStatus
from app.infrastructure.db.models import Task
from app.infrastructure.db.task_repository import TaskRepository


class TaskManager:
    def __init__(self, repository: TaskRepository, writing_agent: BaseAgent) -> None:
        self._repository = repository
        self._writing_agent = writing_agent

    async def submit(self, *, goal: str, constraints: dict[str, Any], output_format: str) -> Task:
        task = await self._repository.create(
            goal=goal, constraints=constraints, output_format=output_format
        )
        task = await self._repository.update_status(task, status=TaskStatus.EXECUTING)

        try:
            result = await self._writing_agent.run(goal)
        except Exception:
            return await self._repository.update_status(task, status=TaskStatus.FAILED)

        return await self._repository.update_status(
            task, status=TaskStatus.COMPLETED, result=result
        )

    async def get(self, task_id: str) -> Task | None:
        return await self._repository.get(task_id)
