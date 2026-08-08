from enum import StrEnum


class TaskStatus(StrEnum):
    PENDING = "pending"
    PLANNING = "planning"
    EXECUTING = "executing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class OutputFormat(StrEnum):
    """Only `MARKDOWN` exists today; add a member here and teach `Synthesizer`
    to render it to support another format."""

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
