"""Purpose: domain exceptions, mapped to HTTP errors in one place (see main.py)."""

from app.enums import TaskStatus


class TaskNotFoundError(Exception):
    def __init__(self, task_id: str) -> None:
        self.task_id = task_id
        super().__init__(f"Task '{task_id}' not found")


class InvalidPlanError(Exception):
    """Raised when the planner can't produce a valid plan after all retry attempts."""


class InvalidTaskStateError(Exception):
    """Raised when an action is attempted on a task in the wrong state (e.g. cancelling
    a completed task)."""

    def __init__(self, task_id: str, status: TaskStatus) -> None:
        self.task_id = task_id
        self.status = status
        super().__init__(f"Task '{task_id}' is '{status}' and cannot be cancelled")


class LLMServiceError(Exception):
    """Raised when the LLM provider call itself fails (bad/missing API key, network
    error, rate limit, timeout) — distinct from InvalidPlanError, which means the LLM
    responded but its plan was malformed."""

    def __init__(self, detail: str) -> None:
        self.detail = detail
        super().__init__(f"LLM service call failed: {detail}")
