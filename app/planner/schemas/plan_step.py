"""Purpose: one step of a Plan — the shape the LLM must return per step."""

from pydantic import BaseModel, Field

from app.enums import AgentName


class PlanStep(BaseModel):
    id: str
    agent: AgentName
    action: str
    input: str
    dependencies: list[str] = Field(default_factory=list)
