"""Purpose: shared constants used by more than one test module.

Test-file-specific constants (used by only one test file) are defined at
the top of that file instead — see CLAUDE.md's Testing section.
"""

from datetime import UTC, datetime

MOCK_CREATED_AT = datetime(2026, 7, 29, 8, 0, tzinfo=UTC)

EXPECTED_TABLES = {"tasks", "execution_plans", "execution_steps", "agents"}
EXPECTED_AGENT_NAMES = {"research", "writing", "analysis", "code"}
