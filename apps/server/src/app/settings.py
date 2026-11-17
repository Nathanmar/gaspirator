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

    # Database (PostgreSQL from docker-compose.yml)
    database_url: str = "postgresql+psycopg://postgres:postgres@localhost:5432/gaspirator"

    # Authentication
    secret_key: str = "change-me-in-production"
    access_token_ttl_seconds: int = 15 * 60
    refresh_token_ttl_seconds: int = 30 * 24 * 60 * 60

    # Geocoding of the registration addresses (Géoplateforme of the IGN, no key needed)
    geocoding_url: str = "https://data.geopf.fr/geocodage"
    geocoding_timeout_seconds: float = 5


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
