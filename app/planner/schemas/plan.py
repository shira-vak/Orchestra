"""Purpose: the planner's output. `parallel_groups` is never LLM-provided —
always computed by validate_plan."""

from pydantic import BaseModel, Field

from app.planner.schemas.plan_step import PlanStep


class Plan(BaseModel):
    steps: list[PlanStep]
    parallel_groups: list[list[str]] = Field(default_factory=list)
