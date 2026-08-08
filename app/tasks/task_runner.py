"""Purpose: runs a validated plan's execution + synthesis in the background,
on its own DB session — the request's session is already closed by the time
this runs, since it must outlive the response that kicked it off. Planning
itself stays synchronous in TaskManager.submit (see task_manager.py) so a
bad plan still fails the request with 422, not silently in the background.
"""

import asyncio

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.agents.registry import AgentRegistry
from app.enums import TaskStatus
from app.execution.engine import ExecutionEngine
from app.infrastructure.db.execution_plan_repository import ExecutionPlanRepository
from app.infrastructure.db.execution_step_repository import ExecutionStepRepository
from app.infrastructure.db.models import Task
from app.infrastructure.db.task_repository import TaskRepository
from app.infrastructure.llm.client import LLMClient
from app.planner.schemas.plan import Plan
from app.synthesis.synthesizer import Synthesizer

# Holds a reference to every scheduled run so asyncio can't garbage-collect
# a task mid-flight — see the stdlib asyncio.create_task docs' warning.
_background_tasks: set[asyncio.Task[None]] = set()


class TaskRunner:
    def __init__(
        self,
        llm_client: LLMClient,
        session_factory: async_sessionmaker[AsyncSession],
        *,
        max_concurrent_llm_calls: int,
        step_retry_attempts: int,
    ) -> None:
        self._llm_client = llm_client
        self._session_factory = session_factory
        self._max_concurrent_llm_calls = max_concurrent_llm_calls
        self._step_retry_attempts = step_retry_attempts

    def start(self, task_id: str, plan: Plan) -> None:
        """Schedules `run` without blocking the caller."""
        task = asyncio.create_task(self.run(task_id, plan))
        _background_tasks.add(task)
        task.add_done_callback(_background_tasks.discard)

    async def run(self, task_id: str, plan: Plan) -> None:
        async with self._session_factory() as session:
            task_repository = TaskRepository(session)
            step_repository = ExecutionStepRepository(session)

            task = await task_repository.get(task_id)
            if task is None or task.status == TaskStatus.CANCELLED:
                return

            plan_row = await ExecutionPlanRepository(session).get_by_task_id(task_id)
            execution_steps = {step.step_key: step for step in plan_row.execution_steps}

            engine = ExecutionEngine(
                AgentRegistry(self._llm_client),
                step_repository,
                max_concurrent_llm_calls=self._max_concurrent_llm_calls,
                step_retry_attempts=self._step_retry_attempts,
            )
            outputs = await engine.run(
                plan,
                execution_steps,
                is_cancelled=lambda: self._is_cancelled(task_repository, task_id),
            )

            await self._finalize(task_repository, task, plan, outputs)

    async def _is_cancelled(self, task_repository: TaskRepository, task_id: str) -> bool:
        task = await task_repository.get(task_id)
        return task is not None and task.status == TaskStatus.CANCELLED

    async def _finalize(
        self, task_repository: TaskRepository, task: Task, plan: Plan, outputs: dict[str, str]
    ) -> None:
        if await self._is_cancelled(task_repository, task.id):
            await task_repository.update_status(task, status=TaskStatus.CANCELLED)
            return
        if not outputs:
            await task_repository.update_status(task, status=TaskStatus.FAILED)
            return

        result = await Synthesizer(self._llm_client).synthesize(
            goal=task.goal, plan=plan, outputs=outputs
        )
        await task_repository.update_status(task, status=TaskStatus.COMPLETED, result=result)
