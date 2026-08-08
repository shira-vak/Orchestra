"""Purpose: ORM model for the `agents` table — the static catalogue of the
4 agent types, seeded once by the initial migration."""

from datetime import datetime
from typing import Any

from sqlalchemy import JSON, DateTime, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.enums import AgentName


class Agent(Base):
    """Static catalogue of the available agent types, seeded by migration.

    This backs `GET /agents` and lets the planner-validation step check that
    a plan only references real agents. It is read-only at runtime — the
    4 rows are written once, by the initial migration.

    The assignment's data model lists "name" and "type" as separate fields;
    here they collapse into one (`name`), because in this design the name
    *is* the routing key — there is exactly one agent instance per type, so
    a separate "type" column would just duplicate "name".
    """

    __tablename__ = "agents"

    name: Mapped[AgentName] = mapped_column(String(20), primary_key=True)
    capabilities: Mapped[list[str]] = mapped_column(JSON, nullable=False)
    configuration: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False, default=dict)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
