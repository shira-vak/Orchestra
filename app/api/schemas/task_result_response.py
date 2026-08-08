from pydantic import BaseModel

from app.api.schemas.step_result_response import StepResultResponse
from app.enums import TaskStatus


class TaskResultResponse(BaseModel):
    task_id: str
    status: TaskStatus
    result: str | None
    steps: list[StepResultResponse]
