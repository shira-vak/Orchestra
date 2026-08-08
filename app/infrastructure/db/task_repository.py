"""Purpose: all persistence access for tasks goes through `TaskRepository` —
no `session.execute(...)` calls for tasks anywhere else in the app.
"""

from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.enums import TaskStatus
from app.infrastructure.db.models import Task


class TaskRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(self, *, goal: str, constraints: dict[str, Any], output_format: str) -> Task:
        task = Task(goal=goal, constraints=constraints, output_format=output_format)
        self._session.add(task)
        await self._session.commit()
        await self._session.refresh(task)
        return task

    async def get(self, task_id: str) -> Task | None:
        return await self._session.get(Task, task_id)

    async def update_status(
        self, task: Task, *, status: TaskStatus, result: str | None = None
    ) -> Task:
        task.status = status
        if result is not None:
            task.result = result
        await self._session.commit()
        await self._session.refresh(task)
        return task
