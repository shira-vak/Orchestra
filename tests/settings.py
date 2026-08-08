"""Purpose: test-only config — kept out of app/config.py since nothing under app/ reads it."""

import os

from app.config import get_settings

_DEFAULT_TEST_DB_NAME = "orchestra_test"  # see .env.example's POSTGRES_TEST_DB


def get_test_database_url() -> str:
    settings = get_settings()
    test_db_name = os.environ.get("POSTGRES_TEST_DB", _DEFAULT_TEST_DB_NAME)
    return (
        f"postgresql+asyncpg://{settings.postgres_user}:{settings.postgres_password}"
        f"@{settings.postgres_host}:{settings.postgres_port}/{test_db_name}"
    )


def get_test_database_name() -> str:
    return os.environ.get("POSTGRES_TEST_DB", _DEFAULT_TEST_DB_NAME)
