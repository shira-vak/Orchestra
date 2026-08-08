"""Purpose: ORM model for the `execution_steps` table — one row per step of
a plan, normalized into queryable/mutable columns (status, output, timing)
that change as execution proceeds, unlike ExecutionPlan.steps which is an
immutable snapshot of what the planner proposed."""

from datetime import datetime
from functools import partial
from typing import Any

from sqlalchemy import JSON, DateTime, ForeignKey, Integer, String, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.constants import EXECUTION_STEP_ID_PREFIX
from app.enums import AgentName, StepStatus
from app.infrastructure.db.base import Base
from app.utils import generate_id


class ExecutionStep(Base):
    __tablename__ = "execution_steps"
    __table_args__ = (
        UniqueConstraint("plan_id", "step_key", name="uq_execution_step_plan_key"),
    )

    id: Mapped[str] = mapped_column(
        String, primary_key=True, default=partial(generate_id, EXECUTION_STEP_ID_PREFIX)
    )
    plan_id: Mapped[str] = mapped_column(
        ForeignKey("execution_plans.id", ondelete="CASCADE"), nullable=False
    )

    # The human-readable id from the plan JSON (e.g. "step_1"). Dependencies
    # reference *this* value, not the surrogate `id` above. The surrogate
    # exists only so the primary key is globally unique — "step_1" repeats
    # across every plan, since the planner numbers steps per-task.
    step_key: Mapped[str] = mapped_column(String, nullable=False)

    agent: Mapped[AgentName] = mapped_column(String(20), nullable=False)
    action: Mapped[str] = mapped_column(String, nullable=False)
    input: Mapped[str] = mapped_column(String, nullable=False)
    dependencies: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)

    status: Mapped[StepStatus] = mapped_column(
        String(20), nullable=False, default=StepStatus.PENDING
    )
    output: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    tokens_used: Mapped[int | None] = mapped_column(Integer, nullable=True)
    execution_time_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)

    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    plan: Mapped["ExecutionPlan"] = relationship(back_populates="execution_steps")
