from functools import lru_cache
import secrets
from typing import Optional

from pydantic_settings import BaseSettings, SettingsConfigDict


_RUNTIME_DEVELOPMENT_SECRET = secrets.token_urlsafe(32)
_LOCAL_ENVS = {"development", "dev", "test", "testing"}


class Settings(BaseSettings):
    """Centralized runtime configuration for auth and application settings."""

    app_env: str = "development"
    secret_key: Optional[str] = None
    access_token_expire_minutes: int = 60
    password_hash_iterations: int = 100_000
    llm_provider: str = ""
    llm_api_key: Optional[str] = None
    llm_model: Optional[str] = None
    llm_base_url: Optional[str] = None

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    @property
    def normalized_env(self) -> str:
        return self.app_env.strip().lower()

    @property
    def resolved_secret_key(self) -> str:
        if self.secret_key:
            return self.secret_key

        if self.normalized_env in _LOCAL_ENVS:
            return _RUNTIME_DEVELOPMENT_SECRET

        raise RuntimeError(
            "SECRET_KEY must be configured when APP_ENV is not development/test."
        )


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
