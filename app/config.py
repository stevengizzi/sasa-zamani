"""Application configuration via Pydantic Settings — loads from environment variables and .env file."""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Sasa/Zamani configuration. All required fields must be set as environment variables or in .env."""

    model_config = SettingsConfigDict(env_file=".env")

    supabase_url: str
    supabase_key: str
    openai_api_key: str
    anthropic_api_key: str
    telegram_bot_token: str
    cluster_join_threshold: float = 0.3
    significance_threshold: float = 0.3


@lru_cache
def get_settings() -> Settings:
    """Return cached Settings singleton. Raises ValidationError if required env vars are missing."""
    return Settings()
