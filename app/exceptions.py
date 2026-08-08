"""Purpose: domain exceptions, mapped to HTTP errors in one place (see
main.py's exception handlers) — never inline HTTPException raises deep in
business logic.
"""


class TaskNotFoundError(Exception):
    def __init__(self, task_id: str) -> None:
        self.task_id = task_id
        super().__init__(f"Task '{task_id}' not found")
