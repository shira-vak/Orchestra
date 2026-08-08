"""Purpose: ORM model for the `tasks` table — the root entity a client
submits (goal + constraints), with a status that tracks it through
planning/execution/completion, and an optional one-to-one ExecutionPlan."""

from datetime import datetime
from functools import partial
from typing import Any

from sqlalchemy import JSON, DateTime, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.constants import DEFAULT_OUTPUT_FORMAT, TASK_ID_PREFIX
from app.enums import TaskStatus
from app.infrastructure.db.base import Base
from app.utils import generate_id


class Task(Base):
    __tablename__ = "tasks"

    id: Mapped[str] = mapped_column(
        String, primary_key=True, default=partial(generate_id, TASK_ID_PREFIX)
    )
    goal: Mapped[str] = mapped_column(String, nullable=False)

    # Open-ended user input (e.g. {"max_words": 1500, "tone": "friendly"}).
    # `Any` is deliberate here — this is the one boundary where the shape is
    # genuinely caller-defined; it's validated for size/type at the API
    # layer (Pydantic schema), not here.
    constraints: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False, default=dict)

    output_format: Mapped[str] = mapped_column(
        String, nullable=False, default=DEFAULT_OUTPUT_FORMAT
    )
    status: Mapped[TaskStatus] = mapped_column(
        String(20), nullable=False, default=TaskStatus.PENDING
    )

    # Set once the task's agent finishes — None until then (pending/executing)
    # or if the task failed. Phase 2's single-agent vertical slice writes this
    # directly; Phase 3's synthesizer will be what writes it once a plan has
    # multiple steps.
    result: Mapped[str | None] = mapped_column(String, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    plan: Mapped["ExecutionPlan | None"] = relationship(
        back_populates="task", uselist=False, cascade="all, delete-orphan"
    )
