"""Purpose: closed value sets (StrEnum) shared across the app — TaskStatus, StepStatus, AgentName"""

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
