"""Purpose: ORM model for `tasks` — the root entity, tracked via `status`."""

from datetime import datetime
from functools import partial
from typing import TYPE_CHECKING, Any

from sqlalchemy import JSON, DateTime, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.constants import TASK_ID_PREFIX
from app.enums import OutputFormat, TaskStatus
from app.infrastructure.db.base import Base
from app.utils import generate_id

if TYPE_CHECKING:
    from app.infrastructure.db.models.execution_plan import ExecutionPlan


class Task(Base):
    __tablename__ = "tasks"

    id: Mapped[str] = mapped_column(
        String, primary_key=True, default=partial(generate_id, TASK_ID_PREFIX)
    )
    goal: Mapped[str] = mapped_column(String, nullable=False)

    # open-ended, caller-defined shape; validated at the API layer, not here
    constraints: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False, default=dict)

    output_format: Mapped[OutputFormat] = mapped_column(
        String, nullable=False, default=OutputFormat.MARKDOWN
    )
    status: Mapped[TaskStatus] = mapped_column(
        String(20), nullable=False, default=TaskStatus.PENDING
    )

    # set once the task completes; None while pending/planning/executing, or on failure
    result: Mapped[str | None] = mapped_column(String, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    plan: Mapped["ExecutionPlan | None"] = relationship(
        back_populates="task", uselist=False, cascade="all, delete-orphan"
    )
