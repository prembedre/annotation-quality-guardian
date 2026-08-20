"""
Shared pytest fixtures for backend tests using PostgreSQL.
"""

import os
os.environ["ENV"] = "testing"

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.db import Base, get_db
from app.main import app

from sqlalchemy.pool import StaticPool

# Import all models so Base.metadata contains every table.
from app.models import (
    Project,
    Item,
    Annotator,
    Annotation,
    TrustScore,
    BehavioralScore,
    EmbeddingResult,
)


def _init_test_engine():
    """Create test engine with PostgreSQL if reachable, otherwise SQLite in-memory."""
    test_db_url = os.getenv("TEST_DATABASE_URL")
    if test_db_url:
        try:
            eng = create_engine(test_db_url, connect_args={"connect_timeout": 1})
            with eng.connect() as conn:
                return eng
        except Exception:
            pass

    # Default to SQLite in-memory with StaticPool for isolated fast test runs
    return create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )


engine = _init_test_engine()

TestingSessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
)

# Ensure tasks and dependencies using SessionLocal use the test database
from app.core import db as core_db
core_db.SessionLocal = TestingSessionLocal
core_db.engine = engine

from app.celery_app import celery_app
celery_app.conf.task_always_eager = True


@pytest.fixture(scope="function")
def db_session():
    """
    Provide a PostgreSQL database session for each test.
    """

    Base.metadata.create_all(bind=engine)

    db = TestingSessionLocal()

    try:
        yield db
    finally:
        db.rollback()
        db.close()

        Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def client(db_session):
    """
    Create a FastAPI TestClient using the PostgreSQL
    test database session.
    """

    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()
