"""Purpose: all persistence access for execution plans — no session.execute() elsewhere."""

from sqlalchemy.ext.asyncio import AsyncSession

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
