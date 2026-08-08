"""Purpose: closed value sets shared across the app.

Using StrEnum (not raw strings) means every status/agent-name comparison is
checked by the type checker, and there is exactly one place that defines the
legal values — no risk of a typo like "compelted" slipping through as a
valid status somewhere in the codebase.
"""

from enum import StrEnum


class TaskStatus(StrEnum):
    PENDING = "pending"
    PLANNING = "planning"
    EXECUTING = "executing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


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
