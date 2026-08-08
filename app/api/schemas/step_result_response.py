"""Purpose: one step's detail in GET /tasks/{id}/result."""

from pydantic import BaseModel, ConfigDict

from app.enums import AgentName, StepStatus


class StepResultResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    step_key: str
    agent: AgentName
    action: str
    status: StepStatus
    tokens_used: int | None
    execution_time_ms: int | None
