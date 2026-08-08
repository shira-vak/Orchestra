"""Purpose: response body for POST /tasks and GET /tasks/{id}."""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict

from app.enums import OutputFormat, TaskStatus


class TaskResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    goal: str
    constraints: dict[str, Any]
    output_format: OutputFormat
    status: TaskStatus
    result: str | None
    created_at: datetime
    updated_at: datetime
