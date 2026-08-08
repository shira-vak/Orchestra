"""Purpose: domain exceptions, mapped to HTTP errors in one place (see main.py)."""


class TaskNotFoundError(Exception):
    def __init__(self, task_id: str) -> None:
        self.task_id = task_id
        super().__init__(f"Task '{task_id}' not found")


class InvalidPlanError(Exception):
    """Raised when the planner can't produce a valid plan after all retry attempts."""
