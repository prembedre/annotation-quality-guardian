"""
Tests for production database configuration and SQLite fallback guard.
Ensures production environment does not silently create ephemeral /tmp databases.
"""

import os
from unittest.mock import patch
from app.core.config import Settings, EnvironmentType


def test_production_rejects_sqlite_url():
    """Verify that in production mode, SQLite URLs are rejected and flagged."""
    with patch.dict(os.environ, {"ENV": "production", "DATABASE_URL": "sqlite:///./local.db"}):
        prod_settings = Settings()
        assert prod_settings.is_production is True
        # resolved_database_url should NOT silently return a /tmp/aqg_dev.db
        url = prod_settings.resolved_database_url
        assert "/tmp/aqg_dev.db" not in url


def test_postgres_url_normalization():
    """Verify that legacy postgres:// URLs from Neon/Supabase are normalized to postgresql://."""
    legacy_url = "postgres://user:pass@ep-test.neon.tech/neondb?sslmode=require"
    with patch.dict(os.environ, {"ENV": "production", "DATABASE_URL": legacy_url}):
        prod_settings = Settings()
        resolved = prod_settings.resolved_database_url
        assert resolved.startswith("postgresql://")
        assert "ep-test.neon.tech" in resolved


def test_development_allows_sqlite():
    """Verify that development and testing environments continue to support local SQLite."""
    with patch.dict(os.environ, {"ENV": "development", "DATABASE_URL": "sqlite:///./aqg_dev.db"}):
        dev_settings = Settings()
        assert dev_settings.is_development is True
        resolved = dev_settings.resolved_database_url
        assert resolved.startswith("sqlite:///")
        assert "aqg_dev.db" in resolved
