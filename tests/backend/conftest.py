"""
Shared pytest fixtures for backend tests using PostgreSQL.
"""

import os

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.db import Base, get_db
from app.main import app


# ============================================================
# PostgreSQL Test Database
# ============================================================

# Tests use a separate PostgreSQL database so that the actual
# project database (aqg_db) and its Phase 1 data are protected.
#
# You can override this using the TEST_DATABASE_URL environment
# variable.

TEST_DATABASE_URL = os.getenv(
    "TEST_DATABASE_URL",
    "postgresql://postgres:postgres@localhost:5432/aqg_test",
)


# ============================================================
# PostgreSQL Engine
# ============================================================

engine = create_engine(
    TEST_DATABASE_URL,
)


# ============================================================
# PostgreSQL Session
# ============================================================

TestingSessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
)


# ============================================================
# Database Fixture
# ============================================================

@pytest.fixture(scope="function")
def db_session():
    """
    Provide a PostgreSQL database session for each test.

    Each test gets its own session. Changes are rolled back
    when the test finishes.
    """

    db = TestingSessionLocal()

    try:
        yield db
    finally:
        db.rollback()
        db.close()


# ============================================================
# FastAPI Test Client Fixture
# ============================================================

@pytest.fixture(scope="function")
def client(db_session):
    """
    Create a FastAPI TestClient using the PostgreSQL
    database session.
    """

    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    # Override FastAPI's normal database dependency.
    app.dependency_overrides[get_db] = override_get_db

    with TestClient(app) as test_client:
        yield test_client

    # Remove the dependency override after the test.
    app.dependency_overrides.clear()
