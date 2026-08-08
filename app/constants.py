"""Purpose: fixed, non-env constants — anything env-overridable belongs in config.py instead."""

TASK_ID_PREFIX = "task"
PLAN_ID_PREFIX = "plan"
EXECUTION_STEP_ID_PREFIX = "estep"

# hex suffix length for generated ids (see utils.generate_id)
ID_SUFFIX_LENGTH = 12

# enforced via a Pydantic Field constraint before a request reaches a prompt
TASK_GOAL_MAX_LENGTH = 2000
