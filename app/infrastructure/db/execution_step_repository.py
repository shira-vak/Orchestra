"""Purpose: all persistence access for execution steps — no session.execute() elsewhere."""

from datetime import UTC, datetime
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.enums import StepStatus
from app.infrastructure.db.models import ExecutionStep
from app.planner.schemas.plan_step import PlanStep


class ExecutionStepRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create_many(
        self, *, plan_id: str, plan_steps: list[PlanStep]
    ) -> dict[str, ExecutionStep]:
        rows = {
            step.id: ExecutionStep(
                plan_id=plan_id,
                step_key=step.id,
                agent=step.agent,
                action=step.action,
                input=step.input,
                dependencies=step.dependencies,
            )
            for step in plan_steps
        }
        self._session.add_all(rows.values())
        await self._session.commit()
        for row in rows.values():
            await self._session.refresh(row)
        return rows

    async def update_status(
        self,
        step: ExecutionStep,
        *,
        status: StepStatus,
        output: dict[str, Any] | None = None,
        tokens_used: int | None = None,
        execution_time_ms: int | None = None,
    ) -> ExecutionStep:
        step.status = status
        if output is not None:
            step.output = output
        if tokens_used is not None:
            step.tokens_used = tokens_used
        if execution_time_ms is not None:
            step.execution_time_ms = execution_time_ms
        if status == StepStatus.RUNNING:
            step.started_at = datetime.now(UTC)
        if status in (StepStatus.COMPLETED, StepStatus.FAILED, StepStatus.SKIPPED):
            step.completed_at = datetime.now(UTC)
        await self._session.commit()
        await self._session.refresh(step)
        return step
