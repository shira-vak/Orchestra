"""Purpose: environment-driven settings.

Everything here can legitimately differ between local dev, CI, and a real
deployment, which is exactly why it's read from the environment instead of
hardcoded — see `constants.py` for the fixed counterpart.

Fields hold atomic values (host, port, user, password), never a pre-built
connection string — `database_url` is computed from them. That way each
credential is typed in exactly one place (`.env`), and docker-compose.yml's
"db" service reads the same `POSTGRES_*` variables instead of a second,
independently-typed copy.

Test-only configuration (the test database name) deliberately does *not*
live here — see `tests/settings.py` for why.
"""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # "dev" or "prod" — also drives which Dockerfile docker-compose.yml
    # builds (see docker-compose.yml's `dockerfile: Dockerfile.${APP_ENV}`).
    app_env: str = "dev"
    app_port: int = 8000

    postgres_host: str = "db"
    postgres_port: int = 5432
    postgres_user: str = "orchestra"
    postgres_password: str = "orchestra"
    postgres_db: str = "orchestra"

    anthropic_api_key: str = ""
    anthropic_model: str = "claude-haiku-4-5-20251001"

    # Caps how many LLM calls the execution engine fires concurrently within
    # one parallel step-group. Bounds cost and avoids hitting provider rate
    # limits when a plan has many independent steps.
    max_concurrent_llm_calls: int = 5

    # How many times a failed step is retried (transient errors only) before
    # it's marked failed for good. See DECISIONS.md for the full policy.
    step_retry_attempts: int = 2

    @property
    def database_url(self) -> str:
        return (
            f"postgresql+asyncpg://{self.postgres_user}:{self.postgres_password}"
            f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
        )


@lru_cache
def get_settings() -> Settings:
    """Cached so Settings is only parsed from the environment once per process."""
    return Settings()
