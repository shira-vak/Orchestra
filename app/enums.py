"""Purpose: closed value sets (StrEnum) shared across the app — TaskStatus, StepStatus,
AgentName, OutputFormat"""

from enum import StrEnum


class TaskStatus(StrEnum):
    PENDING = "pending"
    PLANNING = "planning"
    EXECUTING = "executing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class OutputFormat(StrEnum):
    """The shape a task's synthesized result is written in. Only `MARKDOWN` is
    produced today; adding a format is just adding a member here plus teaching
    `Synthesizer` to render it — the DB column is an unbounded `String`, so no
    migration is needed purely to add a new value."""

    MARKDOWN = "markdown"


class StepStatus(StrEnum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


class AgentName(StrEnum):
    RESEARCH = "research"
    WRITING = "writing"
    ANALYSIS = "analysis"
    CODE = "code"
