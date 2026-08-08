"""Purpose: test-only configuration. Deliberately kept out of app/config.py
— the test database name only ever matters to the test suite, so the
production `Settings` model shouldn't carry a field for it. Connection
pieces that genuinely are shared infrastructure (host, port, credentials)
are still read from `app.config.Settings`, not re-typed here.
"""

import os

from app.config import get_settings

# Only ever read by this file — see .env.example's POSTGRES_TEST_DB.
_DEFAULT_TEST_DB_NAME = "orchestra_test"


def get_test_database_url() -> str:
    settings = get_settings()
    test_db_name = os.environ.get("POSTGRES_TEST_DB", _DEFAULT_TEST_DB_NAME)
    return (
        f"postgresql+asyncpg://{settings.postgres_user}:{settings.postgres_password}"
        f"@{settings.postgres_host}:{settings.postgres_port}/{test_db_name}"
    )


def get_test_database_name() -> str:
    return os.environ.get("POSTGRES_TEST_DB", _DEFAULT_TEST_DB_NAME)
