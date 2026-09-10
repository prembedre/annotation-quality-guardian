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


import os

_curr_dir = os.path.dirname(os.path.abspath(__file__))
_backend_dir = os.path.dirname(os.path.dirname(_curr_dir))
_root_dir = os.path.dirname(_backend_dir)
_env_files = [
    os.path.join(_backend_dir, ".env"),
    os.path.join(_root_dir, ".env"),
    ".env",
]

class Settings(BaseSettings):
    """
    Application Settings loaded from environment variables and .env file.
    """
    model_config = SettingsConfigDict(
        env_file=[f for f in _env_files if os.path.exists(f)] or ".env",
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
        default="postgresql://postgres:postgres@localhost:5432/aqg_db",
        description="SQLAlchemy Database connection URI",
    )

    @property
    def resolved_database_url(self) -> str:
        """Return database URL with resolved absolute path for SQLite."""
        url = self.DATABASE_URL
        if url.startswith("sqlite:///"):
            path_part = url[len("sqlite:///"):]
            if not os.path.isabs(path_part):
                # Try finding aqg_dev.db in root or backend
                cleaned_path = path_part.lstrip("./")
                root_candidate = os.path.join(_root_dir, cleaned_path)
                backend_candidate = os.path.join(_backend_dir, cleaned_path)
                if os.path.exists(root_candidate):
                    target = root_candidate.replace("\\", "/")
                    return f"sqlite:///{target}"
                elif os.path.exists(backend_candidate):
                    target = backend_candidate.replace("\\", "/")
                    return f"sqlite:///{target}"
                else:
                    target = root_candidate.replace("\\", "/")
                    return f"sqlite:///{target}"
        return url

    # ── Cache / Queue / Celery ──
    REDIS_URL: Optional[str] = "redis://localhost:6379/0"
    CELERY_BROKER_URL: Optional[str] = None
    CELERY_RESULT_BACKEND: Optional[str] = None
    CELERY_TASK_ALWAYS_EAGER: bool = False

    @property
    def celery_broker(self) -> str:
        """Return Celery broker URL, falling back to REDIS_URL."""
        return self.CELERY_BROKER_URL or self.REDIS_URL or "redis://localhost:6379/0"

    @property
    def celery_backend(self) -> str:
        """Return Celery result backend URL, falling back to REDIS_URL."""
        return self.CELERY_RESULT_BACKEND or self.REDIS_URL or "redis://localhost:6379/0"

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
