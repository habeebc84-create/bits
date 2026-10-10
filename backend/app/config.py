"""SIGNAL HUNTER X — application settings (env-based, dev/prod separated by APP_ENV)."""
from __future__ import annotations

from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    APP_ENV: str = "development"
    DATABASE_URL: str = "sqlite:///./signalhunter.db"
    FRONTEND_ORIGIN: str = "http://localhost:3000"
    LOG_LEVEL: str = "INFO"

    LLM_PROVIDER: str = "none"  # none | openai_compatible
    LLM_BASE_URL: str = ""
    LLM_API_KEY: str = ""
    LLM_MODEL: str = ""

    SEARCH_PROVIDER: str = "builtin"  # builtin | serper | tavily
    SERPER_API_KEY: str = ""
    TAVILY_API_KEY: str = ""

    REDIS_URL: str = ""

    FETCH_TIMEOUT_S: int = 25
    FETCH_MAX_BYTES: int = 6_000_000
    FETCH_MAX_PAGES_PER_INVESTIGATION: int = 24

    @property
    def is_prod(self) -> bool:
        return self.APP_ENV.lower() == "production"


@lru_cache
def get_settings() -> Settings:
    return Settings()
