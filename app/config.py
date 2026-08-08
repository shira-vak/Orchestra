"""Environment-driven settings — atomic values only; `database_url` is computed, not stored."""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # also selects Dockerfile.${APP_ENV} in docker-compose.yml
    app_env: str = "dev"
    app_port: int = 8000

    postgres_host: str = "db"
    postgres_port: int = 5432
    postgres_user: str = "orchestra"
    postgres_password: str = "orchestra"
    postgres_db: str = "orchestra"

    anthropic_api_key: str = ""
    anthropic_model: str = "claude-haiku-4-5-20251001"

    # caps concurrent LLM calls within one parallel step-group
    max_concurrent_llm_calls: int = 5

    # retries for a failed step before it's marked failed for good
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
