"""
Database session and engine management with SQLAlchemy.
Supports hosted PostgreSQL for production and SQLite for local development.
"""

import os
import logging
from typing import Generator

from sqlalchemy import create_engine, text
from sqlalchemy.orm import declarative_base, sessionmaker, Session

from app.core.config import settings

logger = logging.getLogger(__name__)

# ============================================================
# Declarative Base
# ============================================================

Base = declarative_base()


# ============================================================
# SQLAlchemy Engine Creation
# ============================================================

def _create_database_engine():
    db_url = settings.resolved_database_url
    is_serverless_prod = (
        (
            os.environ.get("VERCEL") == "1"
            or os.environ.get("VERCEL_ENV") is not None
            or os.environ.get("NOW_REGION") is not None
        )
        and (settings.ENV.value == "production" or os.environ.get("VERCEL_ENV") == "production")
    )
    is_prod = settings.is_production or is_serverless_prod

    connect_args = {}
    engine_kwargs = {
        "echo": settings.DEBUG and settings.is_development,
    }

    if db_url.startswith("sqlite"):
        if is_prod:
            logger.error(
                "CRITICAL: SQLite is not permitted in production serverless environments. "
                "Configure a hosted PostgreSQL DATABASE_URL in Vercel."
            )
        connect_args["check_same_thread"] = False
        engine_kwargs["pool_pre_ping"] = False
    else:
        # PostgreSQL Production Configuration
        engine_kwargs["pool_pre_ping"] = True
        engine_kwargs["pool_size"] = 5
        engine_kwargs["max_overflow"] = 10
        engine_kwargs["pool_recycle"] = 300

        # Proactively check driver availability: if psycopg3 is not installed, prefer psycopg2
        if db_url.startswith("postgresql://") and "+psycopg" not in db_url:
            try:
                import psycopg  # noqa: F401
            except ImportError:
                db_url = db_url.replace("postgresql://", "postgresql+psycopg2://", 1)

    try:
        return create_engine(db_url, connect_args=connect_args, **engine_kwargs)
    except Exception as exc:
        if db_url.startswith("postgresql://"):
            try:
                alt_url = db_url.replace("postgresql://", "postgresql+psycopg2://", 1)
                logger.info("Retrying database engine with postgresql+psycopg2 driver: %s", exc)
                return create_engine(alt_url, connect_args=connect_args, **engine_kwargs)
            except Exception as alt_exc:
                logger.warning("Alternative driver retry notice: %s", alt_exc)

        if is_prod:
            logger.error("Failed to create PostgreSQL engine for production: %s", exc)
            raise

        logger.warning("Database engine creation failed (%s). Falling back to local development SQLite.", exc)
        return create_engine("sqlite:///aqg_dev.db", connect_args={"check_same_thread": False}, pool_pre_ping=False)


engine = _create_database_engine()


# ============================================================
# Session Factory
# ============================================================

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
)


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
    Verify database connectivity.
    In production, fails clearly without silently creating an ephemeral SQLite file.
    In local development, may fall back to local dev SQLite.
    """
    global engine, SessionLocal

    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
        return True
    except Exception as exc:
        is_serverless_prod = (
            (
                os.environ.get("VERCEL") == "1"
                or os.environ.get("VERCEL_ENV") is not None
                or os.environ.get("NOW_REGION") is not None
            )
            and (settings.ENV.value == "production" or os.environ.get("VERCEL_ENV") == "production")
        )
        is_prod = settings.is_production or is_serverless_prod

        try:
            safe_url = engine.url.render_as_string(hide_password=True)
        except Exception:
            safe_url = "configured database"
        logger.error("Database connection check failed for [%s]: %s", safe_url, exc)

        if is_prod:
            # Never silently switch to SQLite in production
            return False

        # In local development only, attempt fallback to local dev SQLite
        if not str(engine.url).startswith("sqlite"):
            try:
                fallback_url = "sqlite:///aqg_dev.db"
                engine = create_engine(fallback_url, connect_args={"check_same_thread": False}, pool_pre_ping=False)
                SessionLocal.configure(bind=engine)
                with engine.connect() as connection:
                    connection.execute(text("SELECT 1"))
                logger.info("Fell back to local development SQLite: %s", fallback_url)
                return True
            except Exception as inner_exc:
                logger.error("Local SQLite fallback failed: %s", inner_exc)
                return False

        return False
