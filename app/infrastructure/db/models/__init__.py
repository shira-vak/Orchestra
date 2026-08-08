"""Purpose: import every model here so `Base.metadata` is fully populated wherever
this package is imported — Alembic's autogenerate and the relationship
string references (e.g. Mapped["ExecutionPlan"]) both depend on that.
"""

from app.infrastructure.db.models.agent import Agent
from app.infrastructure.db.models.execution_plan import ExecutionPlan
from app.infrastructure.db.models.execution_step import ExecutionStep
from app.infrastructure.db.models.task import Task

__all__ = ["Agent", "ExecutionPlan", "ExecutionStep", "Task"]
