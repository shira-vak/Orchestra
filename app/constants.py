"""Purpose: fixed, non-env constants — anything env-overridable belongs in config.py instead."""

TASK_ID_PREFIX = "task"
PLAN_ID_PREFIX = "plan"
EXECUTION_STEP_ID_PREFIX = "estep"

# hex suffix length for generated ids (see utils.generate_id)
ID_SUFFIX_LENGTH = 12

DEFAULT_OUTPUT_FORMAT = "markdown"

# enforced via Pydantic Field constraints before a request reaches a prompt
TASK_GOAL_MAX_LENGTH = 2000
TASK_OUTPUT_FORMAT_MAX_LENGTH = 50
