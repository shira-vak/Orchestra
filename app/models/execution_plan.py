"""Purpose: ORM model for the `execution_plans` table — one row per task,
storing the planner's output verbatim (see the `steps` field docstring
below for why this coexists with the normalized `ExecutionStep` rows)."""

from datetime import datetime
from functools import partial
from typing import Any

from sqlalchemy import JSON, DateTime, ForeignKey, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.constants import PLAN_ID_PREFIX
from app.db.base import Base
from app.utils import generate_id


class ExecutionPlan(Base):
    __tablename__ = "execution_plans"

    id: Mapped[str] = mapped_column(
        String, primary_key=True, default=partial(generate_id, PLAN_ID_PREFIX)
    )
    task_id: Mapped[str] = mapped_column(
        ForeignKey("tasks.id", ondelete="CASCADE"), nullable=False, unique=True
    )

    # The plan exactly as the planner returned it: a list of
    # {id, agent, action, input, dependencies} dicts. Kept verbatim even
    # though ExecutionStep rows (below) normalize the same data into
    # queryable columns — this lets us always compare "what the planner
    # proposed" against "what actually happened" during execution, which is
    # useful for debugging planner quality independently of execution bugs.
    steps: Mapped[list[dict[str, Any]]] = mapped_column(JSON, nullable=False)
    parallel_groups: Mapped[list[list[str]]] = mapped_column(JSON, nullable=False)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    task: Mapped["Task"] = relationship(back_populates="plan")
    execution_steps: Mapped[list["ExecutionStep"]] = relationship(
        back_populates="plan", cascade="all, delete-orphan"
    )
