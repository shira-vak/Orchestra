"""Purpose: constants shared by more than one test module — file-specific ones live in that file."""

from datetime import UTC, datetime

MOCK_CREATED_AT = datetime(2026, 7, 29, 8, 0, tzinfo=UTC)

EXPECTED_TABLES = {"tasks", "execution_plans", "execution_steps", "agents"}
EXPECTED_AGENT_NAMES = {"research", "writing", "analysis", "code"}

MOCK_SINGLE_STEP_PLAN_JSON = (
    '{"steps": [{"id": "step_1", "agent": "writing", "action": "write", '
    '"input": "Write a haiku about databases", "dependencies": []}]}'
)
