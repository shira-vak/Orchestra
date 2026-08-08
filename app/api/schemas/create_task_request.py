"""Purpose: request body for POST /tasks."""

from typing import Any

from pydantic import BaseModel, Field

from app.constants import DEFAULT_OUTPUT_FORMAT, TASK_GOAL_MAX_LENGTH, TASK_OUTPUT_FORMAT_MAX_LENGTH


class CreateTaskRequest(BaseModel):
    goal: str = Field(min_length=1, max_length=TASK_GOAL_MAX_LENGTH)
    constraints: dict[str, Any] = Field(default_factory=dict)
    output_format: str = Field(
        default=DEFAULT_OUTPUT_FORMAT, max_length=TASK_OUTPUT_FORMAT_MAX_LENGTH
    )
