"""
Database session and engine management with SQLAlchemy.
PostgreSQL is used as the project database.
"""

from typing import Generator

from sqlalchemy import create_engine, text
from sqlalchemy.orm import declarative_base, sessionmaker, Session

from app.core.config import settings


# ============================================================
# SQLAlchemy Engine
# ============================================================

db_url = settings.resolved_database_url

connect_args = {}
if db_url.startswith("sqlite"):
    connect_args = {"check_same_thread": False}

try:
    engine = create_engine(
        db_url,
        connect_args=connect_args,
        pool_pre_ping=not db_url.startswith("sqlite"),
        echo=settings.DEBUG and settings.is_development,
    )
except Exception:
    import os
    is_serverless = os.environ.get("VERCEL") == "1" or os.environ.get("VERCEL_ENV") is not None or os.name != "nt"
    fallback_path = "/tmp/aqg_dev.db" if is_serverless else "aqg_dev.db"
    fallback_url = f"sqlite:///{fallback_path}"
    engine = create_engine(fallback_url, connect_args={"check_same_thread": False}, pool_pre_ping=False)


# ============================================================
# Session Factory
# ============================================================

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
)


# ============================================================
# Declarative Base
# ============================================================

Base = declarative_base()


# ============================================================
# FastAPI Database Dependency
# ============================================================

def get_db() -> Generator[Session, None, None]:
    """
    Provide a database session for FastAPI requests.

    The session is automatically closed after the request.
    """

    db = SessionLocal()

    try:
        yield db
    finally:
        db.close()


# ============================================================
# Database Connection Check
# ============================================================

def check_db_connection() -> bool:
    """
    Verify database connectivity. If primary DB is unreachable, seamlessly fall back to SQLite.
    """
    global engine, SessionLocal

    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
        return True
    except Exception as exc:
        if not str(engine.url).startswith("sqlite"):
            import logging, os
            logging.getLogger(__name__).warning(
                "Primary database connection failed (%s): %s. Falling back to local SQLite engine.",
                engine.url,
                exc,
            )
            is_serverless = (
                os.environ.get("VERCEL") == "1"
                or os.environ.get("VERCEL_ENV") is not None
                or os.environ.get("AWS_LAMBDA_FUNCTION_NAME") is not None
                or os.name != "nt"
            )
            sqlite_path = "/tmp/aqg_dev.db" if is_serverless else "aqg_dev.db"
            fallback_url = f"sqlite:///{sqlite_path}"
            engine = create_engine(
                fallback_url,
                connect_args={"check_same_thread": False},
                pool_pre_ping=False,
            )
            SessionLocal.configure(bind=engine)
            try:
                with engine.connect() as connection:
                    connection.execute(text("SELECT 1"))
                return True
            except Exception as inner_exc:
                logging.getLogger(__name__).error("SQLite fallback failed: %s", inner_exc)
                return False
        return False
