"""Application settings using pydantic-settings."""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        # .env also holds values read by other libraries, such as API keys and
        # broker URLs; settings only reads the fields declared below.
        extra="ignore",
    )

    # Application settings
    app_name: str = "gaspirator"
    debug: bool = False
    host: str = "0.0.0.0"
    port: int = 8000

    # API settings
    api_prefix: str = "/api"
    api_version: str = "v1"



@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
