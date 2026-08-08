"""Purpose: fixed constants that are part of the app's design, not deployment config.

Anything that should differ between environments (DB URL, API keys,
concurrency limits) belongs in `config.py` instead, where it can be
overridden by an environment variable.
"""

TASK_ID_PREFIX = "task"
PLAN_ID_PREFIX = "plan"
EXECUTION_STEP_ID_PREFIX = "estep"

# Every generated ID is <prefix>_<hex suffix>. The suffix length is short
# enough to stay readable in logs/API responses but long enough that
# collisions are not a practical concern for this system's scale.
ID_SUFFIX_LENGTH = 12

DEFAULT_OUTPUT_FORMAT = "markdown"

# API request limits — enforced via Pydantic Field constraints before a
# request body ever reaches a prompt (see CLAUDE.md's Security section).
TASK_GOAL_MAX_LENGTH = 2000
TASK_OUTPUT_FORMAT_MAX_LENGTH = 50
