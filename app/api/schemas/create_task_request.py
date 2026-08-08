"""Purpose: request body for POST /tasks."""

from typing import Any

from pydantic import BaseModel, Field

from app.constants import TASK_GOAL_MAX_LENGTH
from app.enums import OutputFormat


class CreateTaskRequest(BaseModel):
    goal: str = Field(min_length=1, max_length=TASK_GOAL_MAX_LENGTH)
    constraints: dict[str, Any] = Field(default_factory=dict)
    output_format: OutputFormat = OutputFormat.MARKDOWN
