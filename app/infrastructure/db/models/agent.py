from datetime import datetime
from typing import Any

from sqlalchemy import JSON, DateTime, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.enums import AgentName
from app.infrastructure.db.base import Base


class Agent(Base):
    """Read-only catalogue of the 4 agent types, seeded by migration. No separate "type"
    column — `name` is the routing key, so a distinct type would just duplicate it."""

    __tablename__ = "agents"

    name: Mapped[AgentName] = mapped_column(String(20), primary_key=True)
    capabilities: Mapped[list[str]] = mapped_column(JSON, nullable=False)
    configuration: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False, default=dict)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
