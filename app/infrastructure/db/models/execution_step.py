from datetime import datetime
from functools import partial
from typing import TYPE_CHECKING, Any

from sqlalchemy import JSON, DateTime, ForeignKey, Integer, String, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.constants import EXECUTION_STEP_ID_PREFIX
from app.enums import AgentName, StepStatus
from app.infrastructure.db.base import Base
from app.utils import generate_id

if TYPE_CHECKING:
    from app.infrastructure.db.models.execution_plan import ExecutionPlan


class ExecutionStep(Base):
    __tablename__ = "execution_steps"
    __table_args__ = (UniqueConstraint("plan_id", "step_key", name="uq_execution_step_plan_key"),)

    id: Mapped[str] = mapped_column(
        String, primary_key=True, default=partial(generate_id, EXECUTION_STEP_ID_PREFIX)
    )
    plan_id: Mapped[str] = mapped_column(
        ForeignKey("execution_plans.id", ondelete="CASCADE"), nullable=False
    )

    # the plan-JSON id (e.g. "step_1"); dependencies reference this, not `id`
    step_key: Mapped[str] = mapped_column(String, nullable=False)

    agent: Mapped[AgentName] = mapped_column(String(20), nullable=False)
    action: Mapped[str] = mapped_column(String, nullable=False)
    input: Mapped[str] = mapped_column(String, nullable=False)
    dependencies: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)

    status: Mapped[StepStatus] = mapped_column(
        String(20), nullable=False, default=StepStatus.PENDING
    )
    output: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    # set only when status is FAILED — why the step's retries were exhausted
    error: Mapped[str | None] = mapped_column(String, nullable=True)
    tokens_used: Mapped[int | None] = mapped_column(Integer, nullable=True)
    execution_time_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)

    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    plan: Mapped["ExecutionPlan"] = relationship(back_populates="execution_steps")
