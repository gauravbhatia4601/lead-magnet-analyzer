"""Application configuration powered by Pydantic settings."""

from functools import lru_cache
from typing import Literal, Optional

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Central application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    environment: Literal["development", "staging", "production"] = Field(
        default="development", description="Runtime environment label"
    )
    database_url: str = Field(
        default="sqlite+aiosqlite:///./magentix.db",
        description="SQLAlchemy database URL (async driver required)",
    )
    database_echo: bool = Field(
        default=False, description="Enable SQL echo for debugging"
    )
    database_pool_size: Optional[int] = Field(
        default=5, description="Primary database pool size"
    )
    database_max_overflow: Optional[int] = Field(
        default=5, description="Maximum overflow connections"
    )
    database_pool_timeout: Optional[int] = Field(
        default=30, description="Pool acquisition timeout in seconds"
    )
    database_pool_recycle: Optional[int] = Field(
        default=3600, description="Recycle connections after N seconds"
    )


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return a cached settings instance."""

    return Settings()


settings = get_settings()
