from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.infrastructure.db.models import ExecutionPlan
from app.planner.schemas.plan import Plan


class ExecutionPlanRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(self, *, task_id: str, plan: Plan) -> ExecutionPlan:
        row = ExecutionPlan(
            task_id=task_id,
            steps=[step.model_dump() for step in plan.steps],
            parallel_groups=plan.parallel_groups,
        )
        self._session.add(row)
        await self._session.commit()
        await self._session.refresh(row)
        return row

    async def get_by_task_id(self, task_id: str) -> ExecutionPlan | None:
        result = await self._session.execute(
            select(ExecutionPlan)
            .options(selectinload(ExecutionPlan.execution_steps))
            .where(ExecutionPlan.task_id == task_id)
        )
        return result.scalar_one_or_none()
