"""
Application configuration management using Pydantic BaseSettings.
Supports development, staging, and production environments.
"""

from enum import Enum
from functools import lru_cache
from typing import List, Optional
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class EnvironmentType(str, Enum):
    DEVELOPMENT = "development"
    STAGING = "staging"
    PRODUCTION = "production"
    TESTING = "testing"


class Settings(BaseSettings):
    """
    Application Settings loaded from environment variables and .env file.
    """
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    # ── App Info & Environment ──
    APP_NAME: str = "Annotation Quality Guardian"
    ENV: EnvironmentType = EnvironmentType.DEVELOPMENT
    DEBUG: bool = True
    SECRET_KEY: str = "insecure-dev-secret-key-change-in-production"

    # ── Server ──
    HOST: str = "0.0.0.0"
    PORT: int = 8000

    # ── Database ──
    DATABASE_URL: str = Field(
        default="postgresql:///./aqg_dev.db",
        description="SQLAlchemy Database connection URI (PostgreSQL or SQLite)",
    )

    # ── Cache / Queue (Optional) ──
    REDIS_URL: Optional[str] = "redis://localhost:6379/0"

    # ── CORS ──
    CORS_ORIGINS: str = "http://localhost:5173,http://localhost:3000,http://127.0.0.1:5173"

    @property
    def cors_origin_list(self) -> List[str]:
        """Convert comma-separated CORS_ORIGINS string into a list."""
        if not self.CORS_ORIGINS:
            return ["*"]
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",") if origin.strip()]

    @property
    def is_production(self) -> bool:
        return self.ENV == EnvironmentType.PRODUCTION

    @property
    def is_development(self) -> bool:
        return self.ENV == EnvironmentType.DEVELOPMENT


@lru_cache
def get_settings() -> Settings:
    """Cached settings instance to avoid reading from disk/env multiple times."""
    return Settings()


settings = get_settings()
