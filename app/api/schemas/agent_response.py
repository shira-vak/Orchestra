from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.enums import AgentName


class AgentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    name: AgentName
    capabilities: list[str]
    created_at: datetime
